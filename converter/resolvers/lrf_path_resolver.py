# LOCATION: converter/resolvers/lrf_path_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""Turns an LRF path keyword into a concrete access plan.

NAME FORM
---------
Every name this module returns is rendered in COBOL form (UPPERCASE with
hyphens), because the expander writes them straight back into COBOL
source. NameNormalizer.normalize() is deliberately NOT used: it produces
the DB2 column form (underscores) and would emit VMBTL03_R01.

CORRECTION - A KEYED PARENT WAS DROPPED, SILENTLY
--------------------------------------------------
``is_renderable`` requires BOTH a record and a ``within``::

    return bool(self.record_name and self.within_name)

and parent selection filters on it::

    renderable = [step for step in steps if step.is_renderable]
    if len(renderable) > 1:
        plan.parent = renderable[0]

A set or area access has a ``within``. A CALC access does not::

    OBTAIN FIRST VMBEFF WHERE CALCKEY EQ KY-EFFECT OF VMBEFF OF LR
    IF VMBEFF-VMBEVEF IS EMPTY
    OBTAIN EACH VMBEVEF WITHIN VMBEFF-VMBEVEF

So for ALL-VMBEVEF-BY-VMBEFF only the second step survived the filter,
``len(renderable) == 1``, and ``plan.parent`` stayed None. The expander's
parent branch never fired, no ``parent_emitted`` message was logged, and
VMDZ4310 shipped with NO read of DZBEFFTV at all - while twelve of its
output fields are moved out of DCLDZBEFFTV, a group nothing populates.

THE GUARD IS NOT THE DEFECT. Rendering ``FIND FIRST VMBEFF WITHIN ''``
would produce COBOL that does not compile, and that refusal was added
deliberately. The defect is that the MODEL had no vocabulary for a keyed
access: it knew SET and AREA, and a CALC step fits neither.

``is_calc`` and ``calc_parent`` add that vocabulary. ``is_renderable``
is UNCHANGED, and ``plan.parent`` is still set only from a renderable
step, so nothing that reads this module today sees any difference. The
expander must opt in by reading ``calc_parent`` - and it must render a
CALC parent as ``OBTAIN CALC <record>``, never as a WITHIN access.

P5 NOTE, recorded where the data lives
---------------------------------------
``end_of_set_literals`` and ``not_found_literals`` are collected here
from the subschema's ON-clause returns - VMBEFF-NOT-FND,
NO-VMBEVEF-FND, NO-MORE-VMBEVEF. LrfPathExpander._status_token ignores
them and classifies the literal by string fragments instead, which is
why three distinct statuses collapse to two tokens. The authority is
already in this plan; it is simply not consumed.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rules.lrf_conversion_rules import (
    STATUS_END_OF_SET,
    STATUS_NOT_FOUND,
    STATUS_SET_EMPTY,
)

RETURN_PREFIX = "RETURN "

# The subschema keyword marking a CALC-key access. Site vocabulary;
# belongs in rules/lrf_conversion_rules.py once that module owns the
# path-command vocabulary.
CALC_KEY_TOKEN = "CALCKEY"

NAVIGATION_VERBS = ("OBTAIN", "FIND", "ERASE")


def cobol_name(value: str) -> str:
    """UPPERCASE COBOL/IDMS form: hyphens, never underscores."""
    return str(value or "").strip().upper().replace("_", "-")


@dataclass
class LrfAccessStep:
    """One renderable IDMS access line."""

    verb: str = ""
    scope: str = ""
    record_name: str = ""
    within_name: str = ""
    where_clause: str = ""

    @property
    def is_renderable(self) -> bool:
        """A SET or AREA access: both a record and a container.

        UNCHANGED. A CALC step has no container and must never be
        rendered as ``<verb> <record> WITHIN ''``.
        """
        return bool(self.record_name and self.within_name)

    @property
    def is_calc(self) -> bool:
        """A keyed access: a record, no container, a CALCKEY clause."""
        if not self.record_name or self.within_name:
            return False
        return CALC_KEY_TOKEN in str(self.where_clause or "").upper()

    @property
    def is_resolvable(self) -> bool:
        """Either shape. Used for reporting, never for rendering."""
        return self.is_renderable or self.is_calc


@dataclass
class LrfAccessPlan:
    """Everything the expander needs for one path keyword."""

    keyword: str = ""
    logical_record: str = ""
    path_group_verb: str = ""
    parent: LrfAccessStep | None = None
    calc_parent: LrfAccessStep | None = None
    driving: LrfAccessStep | None = None
    end_of_set_literals: set[str] = field(default_factory=set)
    not_found_literals: set[str] = field(default_factory=set)
    element_records: list[str] = field(default_factory=list)

    @property
    def is_usable(self) -> bool:
        return bool(self.driving and self.driving.is_renderable)

    @property
    def has_parent_access(self) -> bool:
        """True when the path positions a parent before the driving step."""
        return bool(self.parent or self.calc_parent)


class LrfPathResolver:
    """Resolves a path keyword into an LrfAccessPlan."""

    def __init__(
        self,
        *,
        lrf_repository=None,
        mapping_repository=None,
    ) -> None:
        self.lrf_repository = lrf_repository
        self.mapping_repository = mapping_repository
        self.messages: list[str] = []

    # ---------------------------------------------------------- public
    def is_empty(self) -> bool:
        if self.lrf_repository is None:
            return True
        try:
            return bool(self.lrf_repository.is_empty())
        except Exception:  # noqa: BLE001
            return True

    def plan_for_keyword(self, keyword: str) -> LrfAccessPlan | None:
        if self.is_empty():
            return None

        try:
            path = self.lrf_repository.path_for_keyword(keyword)
        except Exception:  # noqa: BLE001
            return None

        if path is None:
            return None

        plan = LrfAccessPlan(
            keyword=cobol_name(path.keyword),
            logical_record=cobol_name(path.logical_record),
            path_group_verb=str(path.path_group_verb or "").upper(),
            element_records=[
                cobol_name(name)
                for name in self._element_records(path.logical_record)
            ],
        )

        steps: list[LrfAccessStep] = []

        for command in path.commands or []:
            self._collect_literals(command, plan)

            verb = str(command.verb or "").upper()
            if verb not in NAVIGATION_VERBS:
                continue

            steps.append(
                LrfAccessStep(
                    verb=verb,
                    scope=str(command.scope or "").upper(),
                    record_name=cobol_name(command.record_name),
                    within_name=cobol_name(command.within_name),
                    where_clause=str(command.where_clause or "").strip(),
                )
            )

        if not steps:
            return plan

        renderable = [step for step in steps if step.is_renderable]

        if renderable:
            plan.driving = renderable[-1]
            if len(renderable) > 1:
                plan.parent = renderable[0]
        else:
            plan.driving = steps[-1]

        self._attach_calc_parent(plan, steps)

        return plan

    def record_is_mapped(self, record_name: str) -> bool:
        """True when Sheet Mapping knows this IDMS record."""
        if self.mapping_repository is None:
            return True

        record = cobol_name(record_name)
        if not record:
            return False

        for probe in (
            "db2_table_for_record",
            "table_for_record",
            "has_record",
            "record_exists",
        ):
            method = getattr(self.mapping_repository, probe, None)
            if method is None:
                continue
            try:
                result = method(record)
            except Exception:  # noqa: BLE001
                continue
            if isinstance(result, bool):
                return result
            if isinstance(result, str):
                return bool(result.strip())

        return True

    # --------------------------------------------------------- helpers
    def _attach_calc_parent(
        self,
        plan: LrfAccessPlan,
        steps: list[LrfAccessStep],
    ) -> None:
        """Record a KEYED parent that precedes the driving step.

        Reported either way, so a path whose parent access this model
        still cannot express is visible rather than silently absent.
        """
        if plan.parent is not None or plan.driving is None:
            return

        for step in steps:
            if step is plan.driving:
                break
            if not step.is_calc:
                continue

            plan.calc_parent = step
            self._log(
                "calc_parent_resolved",
                keyword=plan.keyword,
                record=step.record_name,
                driving=plan.driving.record_name,
            )
            return

        preceding = [step for step in steps if step is not plan.driving]
        if preceding:
            self._log(
                "parent_not_expressible",
                keyword=plan.keyword,
                record=preceding[0].record_name or "(unnamed)",
                driving=plan.driving.record_name,
            )

    def _element_records(self, logical_record_name: str) -> list:
        try:
            return self.lrf_repository.element_records(logical_record_name) or []
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _collect_literals(command, plan: LrfAccessPlan) -> None:
        actions = getattr(command, "status_actions", None) or {}
        for status, action in actions.items():
            literal = LrfPathResolver._return_literal(action)
            if not literal:
                continue
            if str(status) == STATUS_END_OF_SET:
                plan.end_of_set_literals.add(literal)
            elif str(status) in (STATUS_NOT_FOUND, STATUS_SET_EMPTY):
                plan.not_found_literals.add(literal)

    @staticmethod
    def _return_literal(action: str) -> str:
        text = str(action or "").strip().upper()
        if not text.startswith(RETURN_PREFIX):
            return ""
        return cobol_name(text[len(RETURN_PREFIX):])

    def _log(self, key: str, **values) -> None:
        """Plain-text diagnostics. This resolver owns no message catalogue."""
        rendered = " ".join(
            f"{name}={value}" for name, value in sorted(values.items())
        )
        self.messages.append(f"LRF path: {key} {rendered}")


__all__ = ["LrfAccessStep", "LrfAccessPlan", "LrfPathResolver", "cobol_name"]
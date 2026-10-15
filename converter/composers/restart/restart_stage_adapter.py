# LOCATION: converter/composers/restart/restart_stage_adapter.py
# ACTION: CREATE NEW FILE
"""Pipeline-shaped front door for the restart injection.

    compose(text) -> str        .messages -> list[str]

That is the shape every other composer in the pipeline carries, so the
restart pass is called the same way as cursor_flow and needs no special
case in the layout steps.

WHY THIS IS NOT A ZERO-ARGUMENT REGISTRY STAGE

converter/pipeline/registry.py requires a factory taking NO arguments.
The restart pass needs run-scoped input: the Sheet Mapping repository,
the resolved DCLGEN role, the site retention and the totals produced by
'declare_counters'. A zero-argument factory could only reach those
through a module-level mutable context, which lets two conversions in
one process contaminate each other. Repository-dependent composers are
already built by the component factory and called directly; this one
joins them.

WHAT IT OWNS

Only the hand-off. It resolves the role (M10a), then calls the composer
(M9b). It makes no COBOL decision, authors no line, and chooses no
name.

TOTALS ARE CARRIED, NOT AUTHORED

context.totals are the DISPLAY lines the shared counter composer
produced. They are passed through untouched. A second author means two
sets of totals that disagree.

CLASSIFICATION HAS ONE OWNER

A retrieval program is passed to the composer with no role, so the
composer's own gate reports NOT_APPLICABLE_REASONS["retrieval"]. The
adapter does not pre-judge the program kind; two classifiers would
eventually disagree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from converter.composers.restart.restart_injection_composer import (
    PROGRAM_KIND_UPDATE,
    RestartInjectionComposer,
)
from converter.resolvers.restart_role_resolver import RestartRoleResolver
from converter.generators.restart.restart_totals_resolver import (
    RestartTotalsResolver,
)
from catalogs.restart_storage_catalog import GENERATED_STORAGE_FIELDS
from rules.counter_rules import (
    COUNTER_TOTAL_GUARANTEED_ROLES,
    COUNTER_TOTAL_MESSAGES,
)
MESSAGE_PREFIX = "Restart stage:"


@dataclass(frozen=True)
class RestartRunContext:
    """Everything the pass needs that the TEXT cannot supply."""

    program_kind: str = PROGRAM_KIND_UPDATE
    record_name: str = ""
    table_hint: str = ""
    retention_days: int = 0
    dclgen_role: Any = None
    totals: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_update(self) -> bool:
        return str(self.program_kind or "").strip().lower() == PROGRAM_KIND_UPDATE


class RestartStageAdapter:
    """Resolves the role, then runs the restart injection."""

    def __init__(
        self,
        line_utils,
        *,
        context: RestartRunContext | None = None,
        mapping_repository: Any = None,
        table_name_resolver: Any = None,
        shared_cleanups: Iterable[Any] = (),
        scheme: str | None = None,
    ) -> None:
        self.line_utils = line_utils
        self.context = context
        self.mapping_repository = mapping_repository
        self.table_name_resolver = table_name_resolver
        self.shared_cleanups = tuple(shared_cleanups or ())
        self.scheme = scheme
        self.messages: list[str] = []

    #
    # Pipeline surface
    #
    def compose(self, text: str) -> str:
        """Return the converted text. Diagnostics land on .messages."""
        self.messages = []
        source = str(text or "")

        context = self.context
        if context is None:
            self._say(
                "no restart context was supplied; the pass did not run. "
                "This is a WIRING gap, not a program without restart."
            )
            return source

        role = self._role(context)
        if context.is_update and role is None:
            self._say("no usable restart role; the program is unchanged.")
            return source

        return self._inject(source, context, role)

    #
    # Role
    #
    def _role(self, context: RestartRunContext) -> Any:
        """Resolve the role, or None.

        A retrieval program is never asked for one: the resolver would
        report three refusals for a program that is correct as it is.
        """
        if not context.is_update:
            return None

        resolver = RestartRoleResolver(
            mapping_repository=self.mapping_repository,
            table_name_resolver=self.table_name_resolver,
        )
        role, messages = resolver.resolve(
            dclgen_role=context.dclgen_role,
            record_name=context.record_name,
            table_hint=context.table_hint,
            retention_days=context.retention_days,
        )
        self.messages.extend(messages)
        return role

    #
    # Injection
    #
    def _inject(
        self,
        source: str,
        context: RestartRunContext,
        role: Any,
    ) -> str:
        composer = RestartInjectionComposer(
            self.line_utils,
            scheme=self.scheme,
            shared_cleanups=self.shared_cleanups,
        )
        text, messages = composer.compose(
            source,
            role=role,
            program_kind=context.program_kind,
            totals=self._totals(source, context),
        )
        self.messages.extend(messages)
        return text

    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")

    def _totals(self, source: str, context) -> tuple[str, ...]:
        """The end-of-run DISPLAY lines for this program.

        A caller that supplies totals always wins. When none are supplied
        - which was ALWAYS, because RestartRunContext is built with
        totals=() - they are resolved from the counters the PROCEDURE
        DIVISION actually increments, rather than left empty and silently
        dropped by the mainline builder.
        """
        supplied = tuple(context.totals or ())
        if supplied:
            return supplied

        resolver = RestartTotalsResolver(self.line_utils)
        totals = resolver.resolve(
            str(source or "").splitlines(),
            guaranteed=self._guaranteed_counters(),
        )
        self.messages.extend(resolver.messages)
        return totals

    def _guaranteed_counters(self) -> tuple[str, ...]:
        """Counter names the restart family will certainly increment.

        The catalogue has shipped as a mapping and as a sequence of field
        specs, so the role is LOOKED UP rather than assumed, and a shape
        this cannot read is reported instead of silently yielding none.
        """
        found: list[str] = []

        for role in COUNTER_TOTAL_GUARANTEED_ROLES:
            name = self._catalogue_name(role)
            if name:
                found.append(name)
            else:
                self._say(
                    COUNTER_TOTAL_MESSAGES["guarantee_unresolved"].format(
                        role=role
                    )
                )

        return tuple(found)

    @staticmethod
    def _catalogue_name(role: str) -> str:
        fields = GENERATED_STORAGE_FIELDS

        if isinstance(fields, dict):
            return str(fields.get(role) or "").strip().upper()

        for entry in fields or ():
            if isinstance(entry, dict) and str(entry.get("role")) == role:
                return str(entry.get("name") or "").strip().upper()
            if getattr(entry, "role", None) == role:
                return str(getattr(entry, "name", "") or "").strip().upper()

        return ""

__all__ = [
    "MESSAGE_PREFIX",
    "RestartRunContext",
    "RestartStageAdapter",
]
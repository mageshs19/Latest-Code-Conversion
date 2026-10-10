# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_where_builder.py
# ACTION: CREATE NEW FILE
"""Turns a resolved relationship into WHERE predicates, once.

CORRECTION 1 - the LRF branch appended the SAME predicates twice.

    if record_name in lrf_cursors:
        lrf_info = lrf_cursors[record_name]        <- assigned, never read
        if relationship and relationship.conditions:
            where_conditions.extend(               <- the identical list
                self._where_conditions_from_relationship(
                    relationship.conditions))

When the parent was also navigated, where_conditions already held those
predicates, so the clause came out as

    WHERE A = :G.A AND A = :G.A

CursorDeclareBuilder._conditions() de-duplicates byte-identical strings,
so the defect was INVISIBLE - masked by a guard in a different class,
and only while both renderings stay character-for-character equal.
Predicates are built ONCE and the LRF marker is reported, not re-used.

CORRECTION 2 - the parent table was INFERRED from the group name.

    table = dcl_name[3:] if dcl_name.startswith("DCL") else dcl_name

DclgenRepository.group_for_table() is the authority. Stripping three
characters off a name is the same class of inference that produced a
withdrawn SQLCODE -206 diagnosis earlier in this project. The
repository is consulted first; the prefix rule survives only as a
reported fallback.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import (
    DCLGEN_GROUP_PREFIX,
    HOST_GROUP_SEPARATOR,
    HOST_REFERENCE_PREFIX,
    RELATIONSHIP_PREDICATE_TEMPLATE,
)


class SpecWhereBuilder:
    """Builds and reads child-cursor predicates."""

    def __init__(self, dclgen_repository=None) -> None:
        self.dclgen_repository = dclgen_repository
        self.messages: list[str] = []

    def predicates(self, conditions) -> list[str]:
        """One predicate per resolved relationship condition.

        De-duplicated here so no caller has to re-check, and so a second
        contributor cannot silently double the clause.
        """
        output: list[str] = []
        seen: set[str] = set()

        for condition in conditions or []:
            child_column = NameNormalizer.normalize(
                getattr(condition, "child_column", "")
            )
            parent_host = str(
                getattr(condition, "parent_host_reference", "") or ""
            ).strip()

            if not child_column or not parent_host:
                continue

            predicate = RELATIONSHIP_PREDICATE_TEMPLATE.format(
                child_column=child_column,
                parent_host=parent_host,
            )
            if predicate in seen:
                continue

            seen.add(predicate)
            output.append(predicate)

        return output

    def parent_reference(self, condition: str) -> tuple[str, str]:
        """'CHILD_COL = :DCLDZBEFFTV.CT-RKTPROD-479BEFF' -> (table, column).

        Returns the parent TABLE and the parent COLUMN the host
        reference resolves to, or ("", "") when either side is
        unreadable.
        """
        text = str(condition or "")
        if HOST_REFERENCE_PREFIX not in text:
            return "", ""

        host = text.split(HOST_REFERENCE_PREFIX, 1)[1].strip()
        if HOST_GROUP_SEPARATOR not in host:
            return "", ""

        group, _sep, field = host.partition(HOST_GROUP_SEPARATOR)
        table = self._table_for_group(group.strip().upper())
        column = NameNormalizer.normalize(field.strip())

        return NameNormalizer.normalize(table), column

    # ---- group -> table
    def _table_for_group(self, group: str) -> str:
        """Ask the DCLGEN repository; fall back to the prefix rule."""
        if not group:
            return ""

        resolver = getattr(
            self.dclgen_repository, "table_for_group", None
        )
        if callable(resolver):
            try:
                table = resolver(group)
            except Exception:  # noqa: BLE001 - fall through and report
                table = ""
            if table:
                return str(table)

        if group.startswith(DCLGEN_GROUP_PREFIX):
            return group[len(DCLGEN_GROUP_PREFIX):]

        return group


__all__ = ["SpecWhereBuilder"]
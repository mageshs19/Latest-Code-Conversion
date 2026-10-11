# LOCATION: converter/resolvers/restart_role_resolver.py
# ACTION: CREATE NEW FILE
"""Builds the M2 RestartDclgenRole from the three site authorities.

    Sheet Mapping   -> the DB2 table name
    DCLGEN          -> every column and host-variable spelling
    Site metadata   -> the retention value carried on NB_DAY_RS

WHY THIS REPLACES production_restart_role()

That helper is a CATALOGUED CONSTANT. It hands the generator a table
name no site input confirmed, so a program pointed at a different
checkpoint table would silently write its rows into the catalogued one.
A name the run cannot prove is a name the run must refuse.

WHY SHEET MAPPING OUTRANKS DCLGEN ON THE TABLE NAME

rules/field_mapping_rules.py already decides this for columns - "Sheet
Mapping is the authority for DB2 column names" - and the table name is
the same kind of fact. The DCLGEN member carries the COBOL structure
name, conventionally a TV form, which is NOT guaranteed to equal the
DB2 object the SQL must name. When the two disagree the sheet wins and
the disagreement is REPORTED, never silently reconciled.

ALL OR NOTHING

Every field the role declares without a default must be filled. One
unfilled field refuses the whole role and returns None. A half role
produces half a restart family, which is the failure mode M2 through
M9b exist to prevent.

FIELD DISCOVERY, NOT A FIELD LIST

The role's own dataclass fields are read with dataclasses.fields(). A
hand-copied list here would be a second declaration of the role, and
the two would drift the first time M2 gains a column. Only ONE name
needs translating - the resolved DCLGEN metadata spells host_record as
host_record_name - and that single alias is declared below.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from catalogs.restart_paragraph_catalog import RestartDclgenRole
from rules.restart_standard_rules import NOT_APPLICABLE_REASONS

MESSAGE_PREFIX = "Restart role:"

# Filled from Sheet Mapping, never from the DCLGEN member.
SHEET_AUTHORITY_FIELD = "table_name"

# Filled from site metadata, never chosen by the generator.
SITE_AUTHORITY_FIELD = "retention_days"

# The resolved DCLGEN metadata spells one field differently. Schema
# names only - no site vocabulary.
DCLGEN_ALIASES = {
    "host_record": ("host_record", "host_record_name"),
}


class RestartRoleResolver:
    """Assembles one RestartDclgenRole, or refuses and says why."""

    def __init__(
        self,
        mapping_repository: Any = None,
        table_name_resolver: Any = None,
    ) -> None:
        self.mapping_repository = mapping_repository
        self.table_name_resolver = table_name_resolver
        self.messages: list[str] = []

    #
    # Public surface
    #
    def resolve(
        self,
        *,
        dclgen_role: Any = None,
        record_name: str = "",
        table_hint: str = "",
        retention_days: int = 0,
    ) -> tuple[RestartDclgenRole | None, list[str]]:
        """Return (role, messages). The role is None when refused."""
        self.messages = []

        if dclgen_role is None:
            self._say(NOT_APPLICABLE_REASONS["dclgen_unresolved"])
            return None, list(self.messages)

        table = self._table_name(record_name, table_hint, dclgen_role)
        retention = self._retention(retention_days)

        values, missing = self._collect(dclgen_role, table, retention)
        if missing:
            for name in missing:
                self._say(f"{name} unresolved; no restart role built.")
            return None, list(self.messages)

        self._say(
            f"built from Sheet Mapping table {table}, "
            f"{len(values) - 2} DCLGEN entry(ies) and a site retention "
            f"of {retention} day(s)."
        )
        return RestartDclgenRole(**values), list(self.messages)

    #
    # Sheet Mapping - the table name
    #
    def _table_name(
        self,
        record_name: str,
        table_hint: str,
        dclgen_role: Any,
    ) -> str:
        repository = self.mapping_repository
        if repository is None:
            self._say(
                "no Sheet Mapping repository supplied; the DB2 table name "
                "cannot be confirmed."
            )
            return ""

        mapped = ""
        record = str(record_name or "").strip()
        if record:
            mapped = str(repository.db2_table_for_record(record) or "").strip()

        hint = str(table_hint or "").strip()
        if not mapped and hint and self._has_table(hint):
            mapped = hint
            self._say(f"Sheet Mapping confirmed the supplied hint {hint}.")

        if not mapped:
            self._say(
                "Sheet Mapping names no DB2 table for "
                f"{record or hint or 'the restart record'}."
            )
            return ""

        resolved = self._resolve_table(mapped)
        self._report_disagreement(resolved, dclgen_role)
        return resolved

    def _has_table(self, name: str) -> bool:
        checker = getattr(self.mapping_repository, "has_table", None)
        return bool(checker(name)) if callable(checker) else False

    def _resolve_table(self, mapped: str) -> str:
        resolver = self.table_name_resolver
        if resolver is None:
            return mapped.upper()
        return str(resolver.resolve_table(mapped) or mapped).upper()

    def _report_disagreement(self, resolved: str, dclgen_role: Any) -> None:
        declared = str(
            getattr(dclgen_role, SHEET_AUTHORITY_FIELD, "") or ""
        ).strip().upper()
        if declared and resolved and declared != resolved:
            self._say(
                f"the DCLGEN member names {declared}; Sheet Mapping is the "
                f"authority and {resolved} was used."
            )

    #
    # Site metadata - the retention value
    #
    def _retention(self, retention_days: int) -> int:
        try:
            value = int(retention_days or 0)
        except (TypeError, ValueError):
            value = 0
        if value <= 0:
            self._say(
                "the site supplied no retention value; the generator does "
                "not choose one."
            )
            return 0
        return value

    #
    # Assembly
    #
    def _collect(
        self,
        dclgen_role: Any,
        table: str,
        retention: int,
    ) -> tuple[dict[str, Any], list[str]]:
        values: dict[str, Any] = {}
        missing: list[str] = []

        for field in dataclasses.fields(RestartDclgenRole):
            name = field.name
            if name == SHEET_AUTHORITY_FIELD:
                value: Any = table
            elif name == SITE_AUTHORITY_FIELD:
                value = retention
            else:
                value = self._from_dclgen(dclgen_role, name)

            values[name] = value
            if not self._is_filled(value):
                missing.append(name)

        return values, missing

    @staticmethod
    def _from_dclgen(dclgen_role: Any, name: str) -> str:
        for attribute in DCLGEN_ALIASES.get(name, (name,)):
            value = str(getattr(dclgen_role, attribute, "") or "").strip()
            if value:
                return value.upper()
        return ""

    @staticmethod
    def _is_filled(value: Any) -> bool:
        if isinstance(value, int):
            return value > 0
        return bool(str(value or "").strip())

    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")


__all__ = [
    "DCLGEN_ALIASES",
    "MESSAGE_PREFIX",
    "RestartRoleResolver",
    "SHEET_AUTHORITY_FIELD",
    "SITE_AUTHORITY_FIELD",
]
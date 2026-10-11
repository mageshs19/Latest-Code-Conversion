"""
Repository wrapper for Sheet Mapping rows.

Authority:
- Sheet Mapping provides DB2 record/table names and column names.
- Source-field resolution is deterministic (COBOL identifier ->
  new_db2_field_name on the same row). No fuzzy / similarity matching.

This class is a thin facade that delegates to focused helpers:
- MappingRowQuery       (row filtering / listing)
- MappingKeyResolver    (primary / foreign / non-key columns)
- MappingColumnResolver (source->column, audit, update candidates)
"""

from __future__ import annotations

from catalogs.db2_naming_catalog import DB2_TABLE_SUFFIX_EQUIVALENTS
from converter.domain.models import SheetMappingRow
from converter.repositories.mapping_column_resolver import (
    MappingColumnResolver,
)
from converter.repositories.mapping_key_resolver import (
    MappingKeyResolver,
)
from converter.repositories.mapping_row_query import MappingRowQuery
from converter.services.name_normalizer import NameNormalizer


# A Sheet Mapping COBOL cell carries the copybook level number:
#   "  04  CT-RK-TPROD  "
# The level is layout, not identity, so it is stripped.
LEVEL_NUMBER_MAX_WIDTH = 2


def _cobol_name_of(value: str) -> str:
    """The bare COBOL data name from a Sheet Mapping COBOL Zone cell."""
    text = " ".join(str(value or "").split())
    if not text:
        return ""

    parts = text.split()
    if (
        len(parts) > 1
        and parts[0].isdigit()
        and len(parts[0]) <= LEVEL_NUMBER_MAX_WIDTH
    ):
        parts = parts[1:]

    return parts[0].upper() if parts else ""


class MappingRepository:
    def __init__(
        self,
        rows: list[SheetMappingRow] | None = None,
    ) -> None:
        self.rows = rows or []
        self._query = MappingRowQuery(self.rows)
        self._keys = MappingKeyResolver(self._query)
        self._columns = MappingColumnResolver(self._query, self._keys)

    # --- row query ---
    def all(self) -> list[SheetMappingRow]:
        return self._query.all()

    def count(self) -> int:
        return self._query.count()

    def records(self) -> list[str]:
        return self._query.records()

    def tables(self) -> list[str]:
        return self._query.tables()

    def rows_for_record(
        self,
        record_name: str,
    ) -> list[SheetMappingRow]:
        return self._query.rows_for_record(record_name)

    def rows_for_table(
        self,
        table_name: str,
    ) -> list[SheetMappingRow]:
        return self._query.rows_for_table(table_name)

    def db2_columns_for_table(
        self,
        table_name: str,
    ) -> list[str]:
        return self._query.db2_columns_for_table(table_name)

    def db2_table_for_record(
        self,
        record_name: str,
    ) -> str:
        return self._query.db2_table_for_record(record_name)

    def has_record(self, record_name: str) -> bool:
        return bool(self._query.rows_for_record(record_name))

    def has_table(self, table_name: str) -> bool:
        return bool(self._query.rows_for_table(table_name))

    # --- key resolution ---
    def key_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self._keys.primary_key_columns_for_record(record_name)

    def primary_key_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self._keys.primary_key_columns_for_record(record_name)

    def foreign_key_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self._keys.foreign_key_columns_for_record(record_name)

    def non_key_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self._keys.non_key_columns_for_record(record_name)

    # --- column resolution ---
    def column_for_source_field(
        self,
        record_name: str,
        source_field_name: str,
    ) -> str:
        return self._columns.column_for_source_field(
            record_name=record_name,
            source_field_name=source_field_name,
        )

    def update_audit_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self._columns.update_audit_columns_for_record(record_name)

    def update_candidate_columns_for_record(
        self,
        record_name: str,
        changed_source_fields: list[str] | None = None,
    ) -> list[str]:
        return self._columns.update_candidate_columns_for_record(
            record_name=record_name,
            changed_source_fields=changed_source_fields,
        )

    # --- reverse lookup: DB2 column -> IDMS COBOL field name ---
    #
    # CORRECTION - this method delegated through `self.query`, an
    # attribute this class does not own. MappingColumnResolver and
    # MappingKeyResolver hold a MappingRowQuery under that name; the
    # repository holds it as `_query`. Every call raised
    #
    #   AttributeError: 'MappingRepository' object has no attribute 'query'
    #
    # JoinKeyLabelResolver caught it, reported it, and fell back to the
    # DCLGEN host name - so a converter defect was indistinguishable
    # from a missing workbook cell in the generated COBOL.
    #
    # The lookup is now performed HERE, over this class's own public row
    # accessors, and delegates to nothing. A renamed internal helper can
    # no longer break it.
    def cobol_field_for_column(
        self,
        table_name: str = "",
        column_name: str = "",
    ) -> str:
        """The COBOL Zone this DB2 column was mapped FROM.

        Sheet Mapping pairs a COBOL-side identifier (cobol_zone, with
        reference_field_name_copybook as the alternate spelling) with
        new_db2_field_name. Every other query walks that pair LEFT to
        RIGHT. The cursor error-branch label needs it the other way:

            CT_RKTPROD_479BEFF  ->  CT-RKT-PROD

        It is a LOOKUP, not a derivation. The pairing is not reversible
        by any string rule - NS-DBSTK-479BEFF maps to NR-DB-STOCK, and
        the prefix changes.

        Two passes. The first honours the caller's table, so a column
        name reused across tables cannot cross-match. The second drops
        the table filter, because JoinKeyLabelResolver probes several
        spellings of the same table (DZBEFFTV / DZBEFFTB / DZBEFF) and
        the workbook carries only one of them.

        Keyword arguments, because JoinKeyLabelResolver probes
        keyword-first.

        Returns "" when the column is unknown. The caller reports the
        gap and falls back to the DCLGEN host name.
        """
        target = NameNormalizer.normalize(column_name)
        if not target:
            return ""

        wanted_table = NameNormalizer.normalize(table_name)

        for restrict_to_table in (True, False):
            if restrict_to_table and not wanted_table:
                continue

            for record in self.records():
                if restrict_to_table:
                    record_table = NameNormalizer.normalize(
                        self.db2_table_for_record(record)
                    )
                    if record_table and record_table != wanted_table:
                        continue

                for row in self.rows_for_record(record) or []:
                    column = NameNormalizer.normalize(
                        getattr(row, "new_db2_field_name", "")
                        or getattr(row, "cross_application_db2_field_name", "")
                    )
                    if column != target:
                        continue

                    for candidate in (
                        getattr(row, "cobol_zone", ""),
                        getattr(row, "reference_field_name_copybook", ""),
                    ):
                        name = _cobol_name_of(candidate)
                        if name:
                            return name

        return ""

    # --- restart AND-gate support (TB/TV aware) ---
    def _restart_table_candidates(self, table_name: str) -> list[str]:
        """All equivalent DB2 table spellings (TB/TV) for confirmation.

        Mirrors TableNameResolver.table_candidates so a DCLGEN 'TV' name is
        confirmed against a Sheet Mapping 'TB' name (and vice versa).
        """
        normalized = NameNormalizer.normalize(table_name)
        if not normalized:
            return []

        candidates = [normalized]
        for source_suffix, target_suffix in DB2_TABLE_SUFFIX_EQUIVALENTS:
            if normalized.endswith(source_suffix):
                candidates.append(
                    normalized[: -len(source_suffix)] + target_suffix
                )

        # de-duplicate, preserve order
        seen: set[str] = set()
        output: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                seen.add(candidate)
                output.append(candidate)
        return output

    def confirms_restart_table(self, table_name: str) -> bool:
        """True when the Sheet Mapping contains this DB2 table under ANY
        equivalent TB/TV spelling.

        Sheet Mapping is the authority for DB2 table names (authority_rules),
        but it stores the intended (often 'TB') spelling while DCLGEN carries
        the final ('TV') spelling. We therefore confirm across equivalents to
        avoid falsely blocking valid restart generation (Case 1).
        """
        for candidate in self._restart_table_candidates(table_name):
            if self.has_table(candidate):
                return True
        return False


__all__ = [
    "MappingRepository",
]
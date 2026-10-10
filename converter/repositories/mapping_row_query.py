# LOCATION: converter/repositories/mapping_row_query.py
# ACTION: CREATE NEW FILE

"""
Sheet Mapping row query helpers.

Pure row filtering / listing. No column or key resolution logic.
"""

from __future__ import annotations

from converter.domain.models import SheetMappingRow
from converter.services.name_normalizer import NameNormalizer


class MappingRowQuery:
    def __init__(
        self,
        rows: list[SheetMappingRow],
    ) -> None:
        self.rows = rows

    def all(self) -> list[SheetMappingRow]:
        return list(self.rows)

    def count(self) -> int:
        return len(self.rows)

    def records(self) -> list[str]:
        values = {
            NameNormalizer.normalize(row.cobol_record_idms)
            for row in self.rows
            if NameNormalizer.normalize(row.cobol_record_idms)
        }
        return sorted(values)

    def tables(self) -> list[str]:
        values = {
            NameNormalizer.normalize(
                row.new_db2_record or row.cross_application_db2_table
            )
            for row in self.rows
            if NameNormalizer.normalize(
                row.new_db2_record or row.cross_application_db2_table
            )
        }
        return sorted(values)

    def rows_for_record(
        self,
        record_name: str,
    ) -> list[SheetMappingRow]:
        target = NameNormalizer.normalize(record_name)

        if not target:
            return []

        return [
            row
            for row in self.rows
            if NameNormalizer.normalize(row.cobol_record_idms) == target
        ]

    def rows_for_table(
        self,
        table_name: str,
    ) -> list[SheetMappingRow]:
        target = NameNormalizer.normalize(table_name)

        if not target:
            return []

        return [
            row
            for row in self.rows
            if NameNormalizer.normalize(row.new_db2_record) == target
            or NameNormalizer.normalize(row.cross_application_db2_table)
            == target
        ]

    def db2_columns_for_table(
        self,
        table_name: str,
    ) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for row in self.rows_for_table(table_name):
            column = NameNormalizer.normalize(
                row.new_db2_field_name or row.cross_application_db2_field_name
            )
            if not column or column in seen:
                continue
            seen.add(column)
            output.append(column)

        return output

    def db2_table_for_record(
        self,
        record_name: str,
    ) -> str:
        rows = self.rows_for_record(record_name)

        for row in rows:
            table = NameNormalizer.normalize(row.new_db2_record)
            if table:
                return table

        for row in rows:
            table = NameNormalizer.normalize(row.cross_application_db2_table)
            if table:
                return table

        return ""

# LOCATION: converter/repositories/mapping_row_query.py
# ACTION: APPEND these two methods to class MappingRowQuery

    # ------------------------------------------------------------------
    # Reverse lookup: DB2 column -> IDMS COBOL field name
    # ------------------------------------------------------------------
    def cobol_field_for_column(
        self,
        table_name: str,
        column_name: str,
    ) -> str:
        """The COBOL Zone this DB2 column was mapped FROM.

        Sheet Mapping pairs a COBOL-side identifier (cobol_zone, with
        reference_field_name_copybook as the alternate spelling) with
        new_db2_field_name. Every other query in this class walks that
        pair LEFT to RIGHT. The cursor error-branch label needs it the
        other way round:

            CT_RKTPROD_479BEFF  ->  CT-RKT-PROD

        It is a LOOKUP, not a derivation. The pairing is not reversible
        by any string rule - NS-DBSTK-479BEFF maps to NR-DB-STOCK, and
        the prefix changes.

        Returns "" when the column is unknown. The caller reports the
        gap and falls back to the DCLGEN host name.
        """
        target = NameNormalizer.normalize(column_name)
        if not target:
            return ""

        rows = self.rows_for_table(table_name)
        if not rows:
            # A table the Sheet Mapping does not name cannot be
            # narrowed, so scan every row rather than return nothing.
            rows = self.rows

        for row in rows:
            column = NameNormalizer.normalize(
                row.new_db2_field_name
                or row.cross_application_db2_field_name
            )
            if column != target:
                continue

            for candidate in (
                row.cobol_zone,
                row.reference_field_name_copybook,
            ):
                field = self._cobol_zone_field(candidate)
                if field:
                    return field

        return ""

    @staticmethod
    def _cobol_zone_field(value) -> str:
        """The data-name inside a COBOL Zone cell.

        The cell may carry the level number as written in the copybook:

            "02 CT-RKT-PROD"  ->  CT-RKT-PROD
            "CT-RKT-PROD"     ->  CT-RKT-PROD

        A level number reaching the job log as part of the label is a
        defect, so the leading numeric token is dropped.
        """
        text = str(value or "").strip()
        if not text:
            return ""

        parts = text.split()
        if len(parts) > 1 and parts[0].isdigit():
            text = " ".join(parts[1:])

        return NameNormalizer.to_cobol(text.strip())
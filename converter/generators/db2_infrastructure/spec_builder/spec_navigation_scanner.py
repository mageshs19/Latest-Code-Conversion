# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_navigation_scanner.py
# ACTION: CREATE NEW FILE
"""Which records does this program position, and which are copied whole?

Two read-only scans that decide whether a cursor may carry a WHERE and
whether it must project the full record.
"""

from __future__ import annotations

from converter.domain.models import IdmsOperation
from converter.generators.db2_infrastructure.spec_builder.spec_fixed_format import (
    bodies_of,
)
from converter.services.name_normalizer import NameNormalizer
from patterns.record_materialisation_patterns import WHOLE_RECORD_MOVE_PATTERN

NAVIGATION_VERB_PREFIXES = ("OBTAIN", "FIND")


class SpecNavigationScanner:
    """Read-only program scans."""

    @staticmethod
    def navigated_records(operations: list[IdmsOperation] | None) -> set[str]:
        """Records positioned by an OBTAIN/FIND anywhere in the program.

        A parent WHERE join is only valid when the parent is obtained
        HERE; otherwise its host variables are never populated and the
        predicate is evaluated against blanks.
        """
        records: set[str] = set()

        for operation in operations or []:
            verb = str(getattr(operation, "operation", "") or "").upper()
            if not verb.startswith(NAVIGATION_VERB_PREFIXES):
                continue

            record = NameNormalizer.normalize(
                getattr(operation, "record_name", "")
            )
            if record:
                records.add(record)

        return records

    @staticmethod
    def materialised_records(cobol_text: str) -> set[str]:
        """Records copied whole via 'MOVE <record> TO <target>'.

        The record materialisation composer keys off this exact
        statement and later emits one MOVE per mapped column. The cursor
        for such a record must project the FULL record, or those MOVEs
        read a zero-filled host group.
        """
        records: set[str] = set()

        for body in bodies_of(cobol_text):
            if not body:
                continue

            match = WHOLE_RECORD_MOVE_PATTERN.match(body)
            if not match:
                continue

            record = NameNormalizer.normalize(match.group("record"))
            if record:
                records.add(record)

        return records


__all__ = ["SpecNavigationScanner"]
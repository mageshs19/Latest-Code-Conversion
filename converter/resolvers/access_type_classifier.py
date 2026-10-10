# LOCATION: converter/resolvers/access_type_classifier.py
# ACTION: CREATE NEW FILE
"""Classifies IDMS record access types (CALC DN, CALC DL, VIA).

CALC DN (Duplicate Not Allowed) - only one record instance per key
CALC DL (Duplicate Lost) - multiple instances per key, newest kept
VIA - accessed through set relationship
"""

from __future__ import annotations

from typing import Any

from converter.repositories.mapping_repository import MappingRepository
from converter.services.name_normalizer import NameNormalizer
from rules.key_naming_rules import IDENTITY_KEY_PREFIXES


class AccessTypeClassifier:
    """Determines if record is CALC DN, CALC DL, or VIA accessed."""

    def __init__(self, mapping_repository: MappingRepository) -> None:
        self.mapping_repository = mapping_repository

    def is_calc_dn(self, record_name: str) -> bool:
        """CALC DN - no duplicate key values allowed."""
        record = NameNormalizer.normalize(record_name)
        rows = self.mapping_repository.rows_for_record(record) or []

        # Has CALC key and NO seq.no field → DN
        has_calc = False
        has_seq_no = False

        for row in rows:
            idms_key = NameNormalizer.normalize(getattr(row, "idms_key", ""))
            if "CALC" in idms_key:
                has_calc = True

            column_name = NameNormalizer.normalize(
                getattr(row, "new_db2_field_name", "")
            )
            if self._is_seq_no_field(column_name):
                has_seq_no = True

        return has_calc and not has_seq_no

    def is_calc_dl(self, record_name: str) -> bool:
        """CALC DL - duplicate key values allowed (newest kept)."""
        record = NameNormalizer.normalize(record_name)
        rows = self.mapping_repository.rows_for_record(record) or []

        # Has CALC key and HAS seq.no field → DL
        has_calc = False
        has_seq_no = False

        for row in rows:
            idms_key = NameNormalizer.normalize(getattr(row, "idms_key", ""))
            if "CALC" in idms_key:
                has_calc = True

            column_name = NameNormalizer.normalize(
                getattr(row, "new_db2_field_name", "")
            )
            if self._is_seq_no_field(column_name):
                has_seq_no = True

        return has_calc and has_seq_no

    def is_via_accessed(self, record_name: str) -> bool:
        """VIA - accessed through set relationship (child record)."""
        record = NameNormalizer.normalize(record_name)
        rows = self.mapping_repository.rows_for_record(record) or []

        # Has FOREIGN key (child) and NOT CALC → VIA
        for row in rows:
            db2_key = NameNormalizer.normalize(getattr(row, "db2_key", ""))
            idms_key = NameNormalizer.normalize(getattr(row, "idms_key", ""))

            if "FOREIGN" in db2_key or "FK" in db2_key:
                # This is a child record (has foreign key)
                # If it's not CALC, it's VIA accessed
                if "CALC" not in idms_key:
                    return True

        return False

    def has_seq_no_field(self, record_name: str) -> bool:
        """True if record has a seq.no field (NR_ID_ with underscore)."""
        record = NameNormalizer.normalize(record_name)
        rows = self.mapping_repository.rows_for_record(record) or []

        for row in rows:
            column_name = NameNormalizer.normalize(
                getattr(row, "new_db2_field_name", "")
            )
            if self._is_seq_no_field(column_name):
                return True

        return False

    def seq_no_field_count(self, record_name: str) -> int:
        """Count of seq.no fields (NR_ID_ fields) in the record."""
        record = NameNormalizer.normalize(record_name)
        rows = self.mapping_repository.rows_for_record(record) or []
        count = 0

        for row in rows:
            column_name = NameNormalizer.normalize(
                getattr(row, "new_db2_field_name", "")
            )
            if self._is_seq_no_field(column_name):
                count += 1

        return count

    @staticmethod
    def _is_seq_no_field(column_name: str) -> bool:
        """True if column name starts with NR_ID_ (with underscore).

        NR_ID_ = sequence number field (surrogate identity key)
        NR_ID  = regular field (not seq.no)
        """
        normalized = str(column_name or "").strip().upper()
        return normalized.startswith("NR_ID_")


__all__ = ["AccessTypeClassifier"]

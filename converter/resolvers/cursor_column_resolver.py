from __future__ import annotations

from converter.analyzers.field_usage_analyzer import FieldUsageAnalysis
from converter.repositories.mapping_repository import MappingRepository
from converter.resolvers.column_name_resolver import ColumnNameResolver
from converter.resolvers.cursor_column_filter import CursorColumnFilter
from converter.resolvers.cursor_field_usage_column_selector import (
    CursorFieldUsageColumnSelector,
)
from converter.resolvers.cursor_order_by_resolver import CursorOrderByResolver
from converter.resolvers.relationship_resolver import RelationshipResolver
from converter.resolvers.table_name_resolver import TableNameResolver
from converter.services.name_normalizer import NameNormalizer
from rules.cursor_column_rules import (
    CURSOR_COLUMN_MESSAGES,
    ENFORCE_FULL_RECORD_SELECT,
)
from rules.timestamp_audit_rules import AUDIT_COLUMN_PREFIXES


class CursorColumnResolver:
    """
    Resolves minimal cursor SELECT and ORDER BY columns generically.

    SELECT priority:
    1. DCLGEN host fields used in procedure logic.
    2. Fields used in procedure conditions.
    3. Fields used as MOVE sources for output writes.
    4. Parent key columns required by child cursor relationships.
    5. Child order key columns.
    6. Fallback to mapped non-audit columns only if usage is unavailable.

    ORDER BY rule:
    - Parent/root cursors do not get ORDER BY unless explicit order metadata
      exists in Sheet Mapping.
    - Child cursors may order by non-FK primary/sequence key.
    - DESC is added for child sequence/order key where metadata indicates
      sequence/event/latest-first semantics.
    """

    def __init__(
        self,
        mapping_repository: MappingRepository,
        table_name_resolver: TableNameResolver,
        column_name_resolver: ColumnNameResolver,
        relationship_resolver: RelationshipResolver,
    ) -> None:
        self.mapping_repository = mapping_repository
        self.table_name_resolver = table_name_resolver
        self.column_name_resolver = column_name_resolver
        self.relationship_resolver = relationship_resolver

        self.column_filter = CursorColumnFilter(
            table_name_resolver=table_name_resolver,
            column_name_resolver=column_name_resolver,
        )
        self.usage_column_selector = CursorFieldUsageColumnSelector(
            mapping_repository=mapping_repository,
        )
        self.order_by_resolver = CursorOrderByResolver(
            mapping_repository=mapping_repository,
            relationship_resolver=relationship_resolver,
            column_filter=self.column_filter,
        )
        self.diagnostics: list[str] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def select_columns_for_record(
        self,
        record_name: str,
        field_usage_analysis=None,
        force_full_record: bool = False,
    ) -> list[str]:
        """Cursor SELECT columns for one IDMS record.

        Two contributions. Contribution 2 applies ONLY when the record is
        materialised; see force_full_record below.

        1. USAGE-DRIVEN  - columns FieldUsageAnalyzer proved the original
           IDMS COBOL reads. For a non-materialised record this is the
           WHOLE answer: selecting more would over-fetch, and the site
           standard requires an explicit, minimal column list
           (cobol_standards.ENFORCE_CURSOR_EXPLICIT_COLUMNS).

        2. FULL RECORD   - every mapped DCLGEN column, merged with the
           usage columns, when force_full_record is True.

        CORRECTION - this docstring described a union that the code no
        longer performs. It previously claimed contribution 2 was always
        a superset, which made a usage-only result look like a defect.
        A non-materialised record with no proven usage legitimately
        resolves to NO columns here; cursor_spec_builder's augmentation
        pass then adds the parent key columns a child WHERE clause needs.
        Verified 10-10-2026: across all six sample programs this path
        never fires and no empty SELECT is emitted.
        """
        
        record = NameNormalizer.normalize(record_name)
        if not record:
            return []

        usage_columns = self._usage_columns(record, field_usage_analysis)

        # COBOL Standard Logic (Generic Fix):
        # If record is materialized (force_full_record=True), SELECT must include
        # ALL mapped columns to support the whole-record MOVE. Merge usage
        # (proven references) with full mapped columns for completeness.
        if force_full_record:
            full_columns = self._materialised_record_columns(record)
            if full_columns:
                # Merge proven usage with full materialized record
                merged = self._unique(
                    list(usage_columns) + list(full_columns)
                )
                resolved = self._without_audit_columns(merged)
                resolved = self._without_unnecessary_columns(resolved)
                self._log(
                    "materialized_record",
                    record=record,
                    usage=len(usage_columns),
                    full=len(full_columns),
                    total=len(resolved),
                )
                return resolved

        # Non-materialized: use only proven usage columns (COBOL standard)
        resolved = self._without_audit_columns(usage_columns)
        resolved = self._without_unnecessary_columns(resolved)
        if resolved:
            self._log("usage_driven", record=record, count=len(resolved))
            return resolved

        # Non-materialized with no usage: return empty.
        # The cursor_spec_builder.py augmentation pass will add parent key
        # columns needed for child WHERE clauses, avoiding over-selection.
        # For records that genuinely need columns, force_full_record=True
        # handles that case above (materialized records).
        self._log("no_usage_no_full_record", record=record, count=0)
        return []

    # ------------------------------------------------------------------
    # Contributions
    # ------------------------------------------------------------------
    def _usage_columns(
        self,
        record_name: str,
        field_usage_analysis=None,
    ) -> list[str]:
        """Columns proven used by the original COBOL. Never fabricated.

        Guarded because this contribution is an ORDERING preference, not
        a source of columns. A wrong attribute name here previously
        raised

            AttributeError: 'CursorColumnResolver' object has no
            attribute 'field_usage_selector'

        at conversion time while every unit test passed.
        """
        if field_usage_analysis is None:
            return []

        selector = getattr(self, "usage_column_selector", None)
        if selector is None:
            self._log("usage_selector_missing", record=record_name)
            return []

        try:
            selected = selector.columns_from_field_usage(
                record_name=record_name,
                field_usage_analysis=field_usage_analysis,
            )
        except (AttributeError, TypeError) as error:
            self._log(
                "usage_selector_failed",
                record=record_name,
                reason=str(error),
            )
            return []

        return self._unique(selected or [])

    def _materialised_record_columns(self, record_name: str) -> list[str]:
        """Every mapped DCLGEN column of the record.

        ColumnNameResolver.columns_for_record already applies both
        authorities in the correct order:

            Sheet Mapping decides WHICH columns belong to the record.
            DCLGEN decides which of those actually exist.

        A column Sheet Mapping names but DCLGEN does not declare is
        dropped there, so nothing is fabricated here.
        """
        columns = self.column_name_resolver.columns_for_record(record_name)
        return self._unique(columns or [])

    # ------------------------------------------------------------------
    # Audit exclusion
    # ------------------------------------------------------------------
    @staticmethod
    def _without_audit_columns(columns: list[str]) -> list[str]:
        """Drop audit columns from a cursor SELECT list.

        Applied against the same AUDIT_COLUMN_PREFIXES that
        CursorColumnFilter uses, inline rather than through the filter,
        so this method depends on one verified constant instead of an
        unverified collaborator signature.
        """
        prefixes = tuple(
            str(prefix or "").strip().upper()
            for prefix in AUDIT_COLUMN_PREFIXES
            if str(prefix or "").strip()
        )
        if not prefixes:
            return list(columns or [])

        return [
            column
            for column in (columns or [])
            if not str(column).upper().startswith(prefixes)
        ]

    @staticmethod
    def _without_unnecessary_columns(columns: list[str]) -> list[str]:
        """Remove columns that are not typically needed in application logic.
        
        Filters out system metadata, redundant fields, and filler columns
        that shouldn't be in SELECT unless explicitly required.
        """
        unnecessary_patterns = {
            "FILLER",  # Placeholder fields
            "_FILLER_",
            "_RES_",  # Reserved fields
            "_RSV_",
            "_RESERVED_",
            "_SPARE_",  # Spare/unused fields
            "_UNUSED_",
            "_VERSION_",  # Schema versioning
            "_CHECKSUM_",  # Data validation (usually internal)
            "_HASH_",
        }
        
        filtered = []
        for column in (columns or []):
            col_upper = str(column).upper()
            # Skip if column matches unnecessary pattern
            if any(pattern in col_upper for pattern in unnecessary_patterns):
                continue
            filtered.append(column)
        
        return filtered

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        """Normalised, order-preserving de-duplication.

        Order is the contract: CursorDeclareBuilder renders SELECT from
        this list and the FETCH INTO hosts are resolved from the SAME
        list. A reorder here silently corrupts every fetched row.
        """
        output: list[str] = []
        seen: set[str] = set()
        for value in values or []:
            normalized = NameNormalizer.normalize(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            output.append(normalized)
        return output

    def _log(self, key: str, **values) -> None:
        template = CURSOR_COLUMN_MESSAGES.get(key, "")
        if not template:
            return
        if not hasattr(self, "diagnostics"):
            self.diagnostics = []
        self.diagnostics.append(template.format(**values))
        
    def _usage_selector(self):
        """The CursorFieldUsageColumnSelector held by this resolver.

        Found by capability, not by a guessed attribute name: the only
        thing that matters is that it answers select_columns_for_record.
        """
        for value in vars(self).values():
            if hasattr(value, "select_columns_for_record"):
                return value
        return None
    
    def _materialised_record_columns(
        self,
        record_name: str,
    ) -> list[str]:
        """Every mapped DCLGEN column of the record.

        ColumnNameResolver.columns_for_record already applies both
        authorities in the correct order:

            Sheet Mapping decides WHICH columns belong to the record.
            DCLGEN decides which of those actually exist.

        A column Sheet Mapping names but DCLGEN does not declare is
        dropped there, so nothing is fabricated here.
        """
        columns = self.column_name_resolver.columns_for_record(record_name)
        return self._unique(columns or [])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _unique(values: list[str]) -> list[str]:
        """Normalised, order-preserving de-duplication.

        Order is the contract: CursorDeclareBuilder renders SELECT from
        this list and CursorParagraphBodyBuilder renders INTO from the
        host references built off the SAME list. A reorder here silently
        corrupts every fetched row.
        """
        output: list[str] = []
        seen: set[str] = set()
        for value in values or []:
            normalized = NameNormalizer.normalize(value)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            output.append(normalized)
        return output

    def _log(self, key: str, **values) -> None:
        template = CURSOR_COLUMN_MESSAGES.get(key, "")
        if template:
            self.diagnostics.append(template.format(**values))

    def order_by_columns_for_record(
        self,
        record_name: str,
    ) -> list[str]:
        return self.order_by_resolver.order_by_columns_for_record(record_name)
# LOCATION: converter/generators/db2_infrastructure/spec_builder/cursor_spec_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Builds cursor specifications from IDMS operations.

REFACTOR - one 380-line class became six collaborators:

    spec_fixed_format.py          columns 8-72 of a record
    spec_navigation_scanner.py    navigated / materialised records
    spec_lrf_scanner.py           LRF expansion markers
    spec_where_builder.py         relationship -> predicates
    spec_select_augmenter.py      the columns a cursor must expose
    spec_reporter.py              include names, spec diagnostics

Regex moved to patterns/cursor_spec/, constants to rules/cursor_spec/.

CORRECTION 1 - is_parent_cursor read a PARAGRAPH NUMBER.

    return fetch_paragraph.split("-")[0][0] == "7"

CURSOR_OPEN_NUMBERS is (710, 810, 910), so the THIRD cursor opens at
910 and the test returned False for it. That cursor was mis-classified
as a child and cursor_paragraph_body_builder emitted driving-key
DISPLAY lines for a cursor that has no driving key.

A cursor is a CHILD when it carries WHERE predicates and the DRIVER
when it does not - the shape the manual reference shows, and immune to
the numbering.

CORRECTION 2 - the LRF branch appended the SAME predicates twice.

    lrf_info = lrf_cursors[record_name]   <- assigned, never read
    where_conditions.extend(...)          <- the identical list

Predicates are built ONCE, by SpecWhereBuilder, which de-duplicates.
The LRF marker is REPORTED, not used as a second reason to append what
is already there.

CORRECTION 3 - a skipped WHERE was silent. A sweep cursor and a
deliberately unqualified cursor looked identical in the report.

CORRECTION 4 - the reporter was constructed EAGERLY.

    self.reporter = SpecReporter(owner.line_utils)

SpecReporter needs owner.line_utils, but ONLY include_names() ever uses
it. Reading it in __init__ silently widened the owner contract: a
caller that only augments specs - which is what
tests/test_cursor_select_column_parity.py supplies - broke at
construction with AttributeError before a single spec was touched.
Built on first use, so the constructor asks for nothing it does not
need.
"""

from __future__ import annotations

from converter.analyzers.field_usage_analyzer import FieldUsageAnalyzer
from converter.domain.models import IdmsOperation
from converter.generators.db2_infrastructure.spec_builder.spec_lrf_scanner import (
    SpecLrfScanner,
)
from converter.generators.db2_infrastructure.spec_builder.spec_navigation_scanner import (
    SpecNavigationScanner,
)
from converter.generators.db2_infrastructure.spec_builder.spec_reporter import (
    SpecReporter,
)
from converter.generators.db2_infrastructure.spec_builder.spec_select_augmenter import (
    SpecSelectAugmenter,
)
from converter.generators.db2_infrastructure.spec_builder.spec_where_builder import (
    SpecWhereBuilder,
)
from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import (
    CLASSIFY_PARENT_BY_ABSENT_WHERE,
    CURSOR_OPERATIONS,
    PARAGRAPH_NUMBER_SEPARATOR,
    PARENT_CURSOR_OPEN_NUMBER,
    SPEC_CLOSE_PARAGRAPH,
    SPEC_CURSOR_NAME,
    SPEC_CURSOR_ORDER,
    SPEC_FETCH_PARAGRAPH,
    SPEC_HOST_VARIABLES,
    SPEC_IS_PARENT_CURSOR,
    SPEC_MESSAGES,
    SPEC_OPEN_PARAGRAPH,
    SPEC_ORDER_BY_COLUMNS,
    SPEC_RECORD_NAME,
    SPEC_SELECT_COLUMNS,
    SPEC_SET_NAME,
    SPEC_TABLE_NAME,
    SPEC_WHERE_CONDITIONS,
)

PARENT_SERIES_DIGIT = str(PARENT_CURSOR_OPEN_NUMBER)[0]


class CursorSpecBuilder:
    """Assembles one spec dict per cursor the program needs."""

    def __init__(self, owner) -> None:
        # owner exposes mapping_repository, table_name_resolver,
        # cursor_column_resolver, relationship_resolver,
        # cursor_name_resolver, host_variable_resolver and
        # _cursor_paragraph_spec. line_utils is read LAZILY by the
        # reporter - see CORRECTION 4.
        self.owner = owner

        self.navigation = SpecNavigationScanner()
        self.lrf = SpecLrfScanner()
        self.where = SpecWhereBuilder(
            dclgen_repository=getattr(owner, "dclgen_repository", None),
        )
        self.augmenter = SpecSelectAugmenter(
            host_variable_resolver=owner.host_variable_resolver,
            where_builder=self.where,
        )

        self._reporter: SpecReporter | None = None
        self.messages: list[str] = []

    @property
    def reporter(self) -> SpecReporter:
        """Built on first use. See CORRECTION 4."""
        if self._reporter is None:
            self._reporter = SpecReporter(self.owner.line_utils)
        return self._reporter

    # =================================================================
    # Public entry point
    # =================================================================
    def build(
        self,
        operations: list[IdmsOperation],
        cobol_text: str = "",
        field_usage_analysis=None,
    ) -> list[dict[str, object]]:
        self.messages = []

        if field_usage_analysis is None:
            field_usage_analysis = FieldUsageAnalyzer(
                mapping_repository=self.owner.mapping_repository,
                table_name_resolver=self.owner.table_name_resolver,
            ).analyze(cobol_text)

        navigated = self.navigation.navigated_records(operations)
        materialised = self.navigation.materialised_records(cobol_text)
        lrf_cursors = self.lrf.cursors(cobol_text)

        specs: list[dict[str, object]] = []
        seen: set[tuple[str, str, str]] = set()
        cursor_order = 1

        for operation in operations or []:
            spec = self._spec_for(
                operation=operation,
                cursor_order=cursor_order,
                seen=seen,
                navigated=navigated,
                materialised=materialised,
                lrf_cursors=lrf_cursors,
                field_usage_analysis=field_usage_analysis,
            )
            if spec is None:
                continue

            specs.append(spec)
            cursor_order += 1

        self.augmenter.augment(specs)
        self.messages.extend(self.where.messages)

        return specs

    # =================================================================
    # One cursor
    # =================================================================
    def _spec_for(
        self,
        operation: IdmsOperation,
        cursor_order: int,
        seen: set[tuple[str, str, str]],
        navigated: set[str],
        materialised: set[str],
        lrf_cursors: dict,
        field_usage_analysis,
    ) -> dict[str, object] | None:
        name = str(getattr(operation, "operation", "") or "").upper()
        if name not in CURSOR_OPERATIONS:
            return None

        record = NameNormalizer.normalize(
            getattr(operation, "record_name", "")
        )
        if not record:
            return None

        set_name = NameNormalizer.normalize(
            getattr(operation, "set_name", "")
        )

        table = self.owner.table_name_resolver.table_for_record(record)
        if not table:
            return None

        key = (set_name, record, table)
        if key in seen:
            return None
        seen.add(key)

        paragraphs = self.owner._cursor_paragraph_spec(
            cursor_order=cursor_order,
            table_name=table,
        )
        select_columns = (
            self.owner.cursor_column_resolver.select_columns_for_record(
                record_name=record,
                field_usage_analysis=field_usage_analysis,
                force_full_record=record in materialised,
            )
        )
        where_conditions = self._where_for(record, navigated, lrf_cursors)

        return {
            SPEC_SET_NAME: set_name,
            SPEC_RECORD_NAME: record,
            SPEC_TABLE_NAME: table,
            SPEC_CURSOR_NAME: (
                self.owner.cursor_name_resolver.cursor_name_from_table(table)
            ),
            SPEC_SELECT_COLUMNS: select_columns,
            SPEC_HOST_VARIABLES: (
                self.owner.host_variable_resolver.host_references_for_columns(
                    table_name=table,
                    columns=select_columns,
                )
            ),
            SPEC_WHERE_CONDITIONS: where_conditions,
            SPEC_ORDER_BY_COLUMNS: (
                self.owner.cursor_column_resolver.order_by_columns_for_record(
                    record
                )
            ),
            SPEC_OPEN_PARAGRAPH: paragraphs["open_paragraph"],
            SPEC_FETCH_PARAGRAPH: paragraphs["fetch_paragraph"],
            SPEC_CLOSE_PARAGRAPH: paragraphs["close_paragraph"],
            SPEC_CURSOR_ORDER: cursor_order,
            SPEC_IS_PARENT_CURSOR: self._is_parent_cursor(
                where_conditions=where_conditions,
                fetch_paragraph=paragraphs["fetch_paragraph"],
            ),
        }

    # =================================================================
    # WHERE - built ONCE
    # =================================================================
    def _where_for(
        self,
        record: str,
        navigated: set[str],
        lrf_cursors: dict,
    ) -> list[str]:
        """Predicates for one child record, or [] with a reported reason.

        A parent WHERE join is only valid when the parent is obtained in
        THIS program; otherwise its host variables are never populated
        and the predicate is evaluated against blanks.
        """
        relationship = (
            self.owner.relationship_resolver.resolve_for_child_record(record)
        )
        conditions = list(getattr(relationship, "conditions", []) or [])
        if not conditions:
            return []

        parent = NameNormalizer.normalize(
            getattr(relationship, "parent_record", "")
        )
        if parent and parent not in navigated:
            self._log("parent_not_navigated", record=record, parent=parent)
            return []

        predicates = self.where.predicates(conditions)

        # The LRF marker is EVIDENCE, not a second source of predicates.
        if record in lrf_cursors and predicates:
            self._log(
                "lrf_where_already_present",
                record=record,
                count=len(predicates),
            )

        return predicates

    # =================================================================
    # Parent / child
    # =================================================================
    @staticmethod
    def _is_parent_cursor(
        where_conditions: list[str],
        fetch_paragraph: str,
    ) -> bool:
        """A cursor with no WHERE is the driver.

        The paragraph-series fallback is retained only so the previous
        behaviour can be reproduced for a diff; it mis-reads the third
        cursor of a program, which opens at 910.
        """
        if CLASSIFY_PARENT_BY_ABSENT_WHERE:
            return not where_conditions

        name = str(fetch_paragraph or "")
        number = name.split(PARAGRAPH_NUMBER_SEPARATOR, 1)[0]
        return bool(number) and number[:1] == PARENT_SERIES_DIGIT

    # =================================================================
    # Delegated reporting - signatures unchanged for existing callers
    # =================================================================
    def include_names(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        return self.reporter.include_names(cursor_specs)

    def spec_messages(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        return self.reporter.messages(cursor_specs)

    # ---- diagnostics
    def _log(self, key: str, **fields) -> None:
        template = SPEC_MESSAGES.get(key, "")
        if not template:
            return
        try:
            self.messages.append(template.format(**fields))
        except (KeyError, IndexError):
            return


__all__ = ["CursorSpecBuilder"]
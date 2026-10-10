# LOCATION: converter/generators/cursor_paragraph/cursor_paragraph_body_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Builds the COBOL body of a cursor OPEN / FETCH / CLOSE paragraph.

This class owns no COBOL layout literals: every token, indent and
template lives in rules/cursor_paragraph_rules.py. Only dynamic values
(cursor name, paragraph name, host variables) are substituted here.

REFACTOR - one 600-line class became six collaborators.

    cursor_line_geometry.py      does a body line fit the window
    cursor_host_reference.py     one host parser, three spellings
    cursor_key_diagnostics.py    the row-identity DISPLAY lines
    cursor_sql_location.py       MOVE ... TO SQL-LOCATION
    cursor_error_branch.py       WHEN OTHER through the period
    cursor_statement_blocks.py   header, EXEC SQL wrapper, INTO

The public surface is UNCHANGED - open_paragraph, fetch_paragraph,
close_paragraph, sqlcode_error_tail, sql_location_move,
sql_location_body and fetch_into_lines all keep their signatures, so no
caller or test moves.

CORRECTION 1 - the FETCH error branch emitted an UNQUALIFIED host.

See cursor_key_diagnostics.py. Briefly: a foreign-key column keeps the
PARENT's column name, so the data-name exists in two DCLGEN groups and
the bare form is a not-unique reference the compiler rejects. There is
now ONE DISPLAY renderer for both diagnostic paths.

CORRECTION 2 - the refactor DROPPED the fetched-column fallback.

fetch_paragraph() forwarded `where_conditions` and nothing else. A
cursor with no resolved WHERE therefore reached ErrorBranchBuilder with
both key lists empty and produced

    WHEN OTHER
         MOVE 720    TO SQL-LOCATION
         DISPLAY 'ERROR WHILE FETCHING CURSOR DZBFASC1'
         PERFORM SQLERROR

an error branch that identifies NO ROW AT ALL. The operator gets a
cursor name and nothing to look the failure up by.

Three cases, decided here and nowhere else:

    PARENT cursor      cursor name only. It is the driver; there is no
                       driving key to report. This is what the manual
                       reference shows at 720-FETCH.
    CHILD, WHERE known report the driving key - the manual reference
                       shape at 820-FETCH.
    CHILD, no WHERE    report the leading FETCHED columns, so the row
                       is still identifiable.
"""

from __future__ import annotations

from converter.generators.counter_generator import CounterGenerator
from converter.generators.cursor_paragraph import cursor_host_reference as hosts
from converter.generators.cursor_paragraph.cursor_error_branch import (
    ErrorBranchBuilder,
)
from converter.generators.cursor_paragraph.cursor_key_diagnostics import (
    KeyDiagnosticsBuilder,
)
from converter.generators.cursor_paragraph.cursor_sql_location import (
    SqlLocationBuilder,
)
from converter.generators.cursor_paragraph.cursor_statement_blocks import (
    StatementBlockBuilder,
)
from rules.cursor_paragraph_rules import (
    CLOSE_STATEMENT_TEMPLATE,
    CURSOR_EOC_SUFFIX,
    CURSOR_NOT_EOC_SUFFIX,
    ENFORCE_FETCH_PROLOGUE,
    ERROR_CLOSE_TEMPLATE,
    ERROR_FETCH_TEMPLATE,
    ERROR_OPEN_TEMPLATE,
    FETCH_STATEMENT_TEMPLATE,
    IND_SQL_BODY,
    IND_STATEMENT,
    IND_WHEN,
    IND_WHEN_BODY,
    INITIALIZE_HOST_GROUP_TEMPLATE,
    OPEN_STATEMENT_TEMPLATE,
    SET_EOC_TEMPLATE,
    SET_NOT_EOC_TEMPLATE,
    TOKEN_CONTINUE,
    TOKEN_END_EXEC,
    TOKEN_EVALUATE_SQLCODE,
    TOKEN_EXEC_SQL,
    TOKEN_WHEN_100,
    TOKEN_WHEN_ZERO,
)


class CursorParagraphBodyBuilder:
    """Assembles one cursor paragraph from its collaborators."""

    def __init__(self) -> None:
        self.sql_location = SqlLocationBuilder()
        self.blocks = StatementBlockBuilder(self.sql_location)
        self.diagnostics = KeyDiagnosticsBuilder()
        self.error_branch = ErrorBranchBuilder(
            sql_location=self.sql_location,
            diagnostics=self.diagnostics,
        )

    # ------------------------------------------------------------------
    # OPEN
    # ------------------------------------------------------------------
    def open_paragraph(
        self,
        cursor_name: str,
        paragraph_name: str,
        sql_error_paragraph: str,
    ) -> list[str]:
        lines = self.blocks.prologue(
            paragraph_name=paragraph_name,
            statement=OPEN_STATEMENT_TEMPLATE.format(cursor=cursor_name),
        )
        lines.extend(
            [
                f"{IND_STATEMENT}{TOKEN_EVALUATE_SQLCODE}",
                f"{IND_WHEN}{TOKEN_WHEN_ZERO}",
                IND_WHEN_BODY
                + SET_NOT_EOC_TEMPLATE.format(
                    cursor=cursor_name,
                    suffix=CURSOR_NOT_EOC_SUFFIX,
                ),
            ]
        )
        # OPEN has not fetched a row: nothing row-specific to report.
        lines.extend(
            self.error_branch.build(
                error_text=ERROR_OPEN_TEMPLATE.format(cursor=cursor_name),
                sql_error_paragraph=sql_error_paragraph,
                paragraph_name=paragraph_name,
            )
        )
        return lines

    # ------------------------------------------------------------------
    # FETCH
    # ------------------------------------------------------------------
    def fetch_paragraph(
        self,
        cursor_name: str,
        paragraph_name: str,
        host_variables: list[str],
        sql_error_paragraph: str,
        where_conditions: list[str] | None = None,
        table_name: str = "",
        is_parent_cursor: bool = False,
    ) -> list[str]:
        """FETCH paragraph body.

        DB2 leaves the host variables UNCHANGED on SQLCODE 100 or a
        negative code, so without the INITIALIZE the DCLGEN group still
        holds the PREVIOUS row and every downstream MOVE copies stale
        values into the output record. The group is derived from the
        FETCH INTO list itself, so it is always the group this very
        statement writes into.
        """
        lines = self.blocks.header(paragraph_name)

        if ENFORCE_FETCH_PROLOGUE:
            group = hosts.group_of(host_variables)
            if group:
                lines.append(
                    IND_STATEMENT
                    + INITIALIZE_HOST_GROUP_TEMPLATE.format(group=group)
                )

        lines.append(
            IND_STATEMENT
            + SET_NOT_EOC_TEMPLATE.format(
                cursor=cursor_name,
                suffix=CURSOR_NOT_EOC_SUFFIX,
            )
        )
        lines.append(self.sql_location.statement(paragraph_name))
        lines.append("")

        lines.append(f"{IND_STATEMENT}{TOKEN_EXEC_SQL}")
        lines.append(
            f"{IND_SQL_BODY}"
            f"{FETCH_STATEMENT_TEMPLATE.format(cursor=cursor_name)}"
        )
        lines.extend(self.blocks.into_lines(host_variables))
        lines.append(f"{IND_SQL_BODY}{TOKEN_END_EXEC}")
        lines.append("")

        lines.append(f"{IND_STATEMENT}{TOKEN_EVALUATE_SQLCODE}")
        lines.append(f"{IND_WHEN}{TOKEN_WHEN_ZERO}")

        if table_name:
            counter = CounterGenerator()
            name = counter.counter_name_for_table(table_name)
            lines.append(f"{IND_WHEN_BODY}{counter.increment(name)}")

        lines.append(f"{IND_WHEN_BODY}{TOKEN_CONTINUE}")
        lines.append(f"{IND_WHEN}{TOKEN_WHEN_100}")
        lines.append(
            IND_WHEN_BODY
            + SET_EOC_TEMPLATE.format(
                cursor=cursor_name,
                suffix=CURSOR_EOC_SUFFIX,
            )
        )

        # ---- row identity. See CORRECTION 2.
        #
        # A PARENT cursor is the driver and reports the cursor name
        # only. A CHILD reports its driving key, or - with no WHERE
        # resolved - the fetched columns, so the branch never comes out
        # unable to identify the failing row.
        driving_key = None if is_parent_cursor else (where_conditions or None)
        fetched_hosts = (
            None
            if is_parent_cursor or driving_key
            else (host_variables or None)
        )

        lines.extend(
            self.error_branch.build(
                error_text=ERROR_FETCH_TEMPLATE.format(cursor=cursor_name),
                sql_error_paragraph=sql_error_paragraph,
                paragraph_name=paragraph_name,
                where_conditions=driving_key,
                fetched_hosts=fetched_hosts,
            )
        )
        return lines

    # ------------------------------------------------------------------
    # CLOSE
    # ------------------------------------------------------------------
    def close_paragraph(
        self,
        cursor_name: str,
        paragraph_name: str,
        sql_error_paragraph: str,
    ) -> list[str]:
        lines = self.blocks.prologue(
            paragraph_name=paragraph_name,
            statement=CLOSE_STATEMENT_TEMPLATE.format(cursor=cursor_name),
        )
        lines.extend(
            [
                f"{IND_STATEMENT}{TOKEN_EVALUATE_SQLCODE}",
                f"{IND_WHEN}{TOKEN_WHEN_ZERO}",
                f"{IND_WHEN_BODY}{TOKEN_CONTINUE}",
            ]
        )
        # The row is already gone by CLOSE time.
        lines.extend(
            self.error_branch.build(
                error_text=ERROR_CLOSE_TEMPLATE.format(cursor=cursor_name),
                sql_error_paragraph=sql_error_paragraph,
                paragraph_name=paragraph_name,
            )
        )
        return lines

    # ------------------------------------------------------------------
    # Backward-compatible delegates
    # ------------------------------------------------------------------
    def sql_location_move(self, paragraph_name: str) -> str:
        return self.sql_location.statement(paragraph_name)

    def sql_location_body(self, paragraph_name: str) -> str:
        return self.sql_location.body(paragraph_name)

    def fetch_into_lines(self, host_variables: list[str]) -> list[str]:
        return self.blocks.into_lines(host_variables)

    def sqlcode_error_tail(
        self,
        error_text: str,
        sql_error_paragraph: str,
        paragraph_name: str = "",
        diagnostic_hosts: list[str] | None = None,
        display_where_clause: bool = False,
    ) -> list[str]:
        """Retained signature for existing callers and tests."""
        return self.error_branch.build(
            error_text=error_text,
            sql_error_paragraph=sql_error_paragraph,
            paragraph_name=paragraph_name,
            where_conditions=diagnostic_hosts if display_where_clause else None,
            fetched_hosts=None if display_where_clause else diagnostic_hosts,
        )


__all__ = ["CursorParagraphBodyBuilder"]
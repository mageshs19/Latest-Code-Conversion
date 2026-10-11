# LOCATION: converter/generators/cursor_paragraph/cursor_paragraph_body_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Builds the COBOL body of a cursor OPEN / FETCH / CLOSE paragraph.

This class owns no COBOL layout literals: every token, indent and
template lives in rules/cursor_paragraph_rules.py. Only dynamic values
(cursor name, paragraph name, host variables) are substituted here.

REFACTOR - one 600-line class became seven collaborators.

    cursor_line_geometry.py      does a body line fit the window
    cursor_host_reference.py     one host parser, three spellings
    cursor_key_diagnostics.py    the row-identity DISPLAY lines
    cursor_sql_location.py       MOVE ... TO SQL-LOCATION
    cursor_error_branch.py       WHEN OTHER through the period
    cursor_statement_blocks.py   header, EXEC SQL wrapper, INTO
    cursor_fetch_paragraph.py    the FETCH body and its three decisions

WHY FETCH MOVED OUT

OPEN and CLOSE are one fixed shape each - header, EXEC SQL, one WHEN
ZERO line, the error branch. FETCH makes THREE decisions: whether to
count the row, what to report on failure, whether to prime the host
group. Those decisions and their corrections now live in one file each
side of the seam, so a change to counting cannot disturb OPEN.

The public surface is UNCHANGED - open_paragraph, fetch_paragraph,
close_paragraph, sqlcode_error_tail, sql_location_move,
sql_location_body and fetch_into_lines all keep their signatures, so no
caller or test moves.

CORRECTION 1 - the FETCH error branch emitted an UNQUALIFIED host.

See cursor_key_diagnostics.py. Briefly: a foreign-key column keeps the
PARENT's column name, so the data-name exists in two DCLGEN groups and
the bare form is a not-unique reference the compiler rejects. There is
now ONE DISPLAY renderer for both diagnostic paths.

CORRECTION 2 - the diagnostic LABEL was the DCLGEN host name.

    DISPLAY 'CT-RKTPROD-479BEFF : ' CT-RKTPROD-479BEFF

The operator reads the job log against the IDMS record layout, so the
label must be the IDMS COBOL field name Sheet Mapping pairs with the
DB2 column. That is a LOOKUP, not a derivation - NS-DBSTK-479BEFF maps
to NR-DB-STOCK, and no string rule turns NS into NR.

This class was constructed bare - KeyDiagnosticsBuilder() - so the
renderer had nothing but the host name to print. The mapping repository
is now accepted and forwarded. It is OPTIONAL: with no repository the
renderer falls back to the host name and REPORTS every fallback, so an
unwired build is visible in the conversion log instead of silently
producing the old output.

OWNERSHIP

ONE SqlLocationBuilder and ONE ErrorBranchBuilder are constructed here
and INJECTED into the fetch builder. Two copies would be two places for
an indent to drift.

MESSAGES

`messages` exposes the label-resolution diagnostics. The generator must
drain it; an unreported fallback is the exact failure CORRECTION 2
exists to end.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph.cursor_error_branch import (
    ErrorBranchBuilder,
)
from converter.generators.cursor_paragraph.cursor_fetch_paragraph import (
    FetchParagraphBuilder,
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
from converter.generators.cursor_paragraph.join_key_label_resolver import (
    JoinKeyLabelResolver,
)
from rules.cursor_paragraph_rules import (
    CLOSE_STATEMENT_TEMPLATE,
    CURSOR_NOT_EOC_SUFFIX,
    ERROR_CLOSE_TEMPLATE,
    ERROR_OPEN_TEMPLATE,
    IND_STATEMENT,
    IND_WHEN,
    IND_WHEN_BODY,
    OPEN_STATEMENT_TEMPLATE,
    SET_NOT_EOC_TEMPLATE,
    TOKEN_CONTINUE,
    TOKEN_EVALUATE_SQLCODE,
    TOKEN_WHEN_ZERO,
)


class CursorParagraphBodyBuilder:
    """Assembles one cursor paragraph from its collaborators."""

    def __init__(self, mapping_repository=None) -> None:
        self.sql_location = SqlLocationBuilder()
        self.blocks = StatementBlockBuilder(self.sql_location)

        # CORRECTION 2 - constructed bare, so the diagnostic label had
        # nothing but the DCLGEN host name to print. Sheet Mapping is
        # the authority for the COBOL field name; DCLGEN is the
        # authority for the host variable. They are different facts.
        self.label_resolver = JoinKeyLabelResolver(mapping_repository)
        self.diagnostics = KeyDiagnosticsBuilder(
            label_resolver=self.label_resolver,
        )
        self.error_branch = ErrorBranchBuilder(
            sql_location=self.sql_location,
            diagnostics=self.diagnostics,
        )

        # INJECTED, not constructed inside. One sql_location, one
        # error_branch, shared by all three paragraph shapes.
        self.fetch_builder = FetchParagraphBuilder(
            blocks=self.blocks,
            sql_location=self.sql_location,
            error_branch=self.error_branch,
        )

    @property
    def messages(self) -> list[str]:
        """Label-resolution diagnostics. The generator must drain this."""
        return self.label_resolver.messages

    def reset(self) -> None:
        """Clear per-program diagnostics."""
        self.label_resolver.reset()

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
    # FETCH - delegated. See cursor_fetch_paragraph.py.
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
        """FETCH paragraph body. Signature retained for every caller."""
        return self.fetch_builder.build(
            cursor_name=cursor_name,
            paragraph_name=paragraph_name,
            host_variables=host_variables,
            sql_error_paragraph=sql_error_paragraph,
            where_conditions=where_conditions,
            table_name=table_name,
            is_parent_cursor=is_parent_cursor,
        )

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
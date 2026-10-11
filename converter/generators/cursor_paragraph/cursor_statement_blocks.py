# LOCATION: converter/generators/cursor_paragraph/cursor_statement_blocks.py
# ACTION: REPLACE ENTIRE FILE
"""Paragraph header, debug trace, EXEC SQL wrapper and the INTO clause.

The mechanical scaffolding of a cursor paragraph. Makes no decision
about diagnostics or flow.

    710-OPEN-DZBEFFC1.
    D    DISPLAY '710-OPEN-DZBEFFC1.'
         MOVE 710    TO SQL-LOCATION

         EXEC SQL
           OPEN DZBEFFC1
         END-EXEC

Column contract, from the manual reference:

    paragraph header   8    Area A
    D indicator        7    column 7, body from 12
    MOVE / EXEC SQL    12
    OPEN / FETCH       14
    INTO               15
    , :GROUP.HOST      18
    END-EXEC           12   back at the EXEC SQL column

CORRECTION 1 - DEBUG_BODY_INDENT was a module literal.

Four spaces sat in this file while every other indent came from
rules/. One edit to the debug column would have had to be made in two
places, and the project rule is that generated COBOL layout text lives
in rules/. It is now derived from the statement column.

CORRECTION 2 - into_lines() rendered a bare INTO on an empty list.

A FETCH whose host list could not be resolved produced

    EXEC SQL
      FETCH DZBEFFC1
    END-EXEC

which binds nothing and fails at run time with no host variables. An
empty list now yields NO INTO line at all, so the defect is visible in
the SQL rather than hidden behind a well-formed keyword.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph.cursor_sql_location import (
    SqlLocationBuilder,
)
from rules.cursor_paragraph_rules import (
    DEBUG_BODY_INDENT,
    DEBUG_INDICATOR,
    DEBUG_TRACE_TEMPLATE,
    EMIT_DEBUG_TRACE_LINES,
    IND_SQL_BODY,
    IND_SQL_INTO,
    IND_SQL_INTO_NEXT,
    IND_STATEMENT,
    PARAGRAPH_HEADER_TEMPLATE,
    TOKEN_END_EXEC,
    TOKEN_EXEC_SQL,
    TOKEN_HOST_SEPARATOR,
    TOKEN_INTO,
)


class StatementBlockBuilder:
    """Renders the non-decisional parts of a cursor paragraph."""

    def __init__(self, sql_location: SqlLocationBuilder | None = None) -> None:
        self.sql_location = sql_location or SqlLocationBuilder()

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    def header(self, paragraph_name: str) -> list[str]:
        """Paragraph header plus the optional D-indicator trace line.

        The 'D' sits in column 7 and the body starts at the statement
        column, matching the reference:

            D    DISPLAY '710-OPEN-DZBEFFC1.'
        """
        lines = [PARAGRAPH_HEADER_TEMPLATE.format(paragraph=paragraph_name)]

        if EMIT_DEBUG_TRACE_LINES:
            trace = DEBUG_TRACE_TEMPLATE.format(paragraph=paragraph_name)
            lines.append(f"{DEBUG_INDICATOR}{DEBUG_BODY_INDENT}{trace}")

        return lines

    # ------------------------------------------------------------------
    # EXEC SQL wrapper
    # ------------------------------------------------------------------
    def prologue(
        self,
        paragraph_name: str,
        statement: str,
        close_exec: bool = True,
    ) -> list[str]:
        """Header, trace, SQL-LOCATION move and the EXEC SQL opening.

        END-EXEC returns to the EXEC SQL column, never the body column.
        """
        lines = self.header(paragraph_name)
        lines.extend(
            [
                self.sql_location.statement(paragraph_name),
                "",
                f"{IND_STATEMENT}{TOKEN_EXEC_SQL}",
                f"{IND_SQL_BODY}{statement}",
            ]
        )

        if close_exec:
            lines.append(f"{IND_STATEMENT}{TOKEN_END_EXEC}")
            lines.append("")

        return lines

    # ------------------------------------------------------------------
    # INTO clause
    # ------------------------------------------------------------------
    @staticmethod
    def into_lines(host_variables: list[str]) -> list[str]:
        """INTO clause in manual form: first host on INTO, leading commas.

            INTO :DCLDZBEFFTV.CO-IDPRKSK-479BEFF
               , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF

        Blank entries are dropped before the first host is chosen, so a
        padded list cannot put the comma form on line one.
        """
        hosts = [
            str(host).strip()
            for host in (host_variables or [])
            if str(host or "").strip()
        ]

        # CORRECTION 2. No hosts, no INTO keyword.
        if not hosts:
            return []

        output = [f"{IND_SQL_INTO}{TOKEN_INTO} {hosts[0]}"]
        output.extend(
            f"{IND_SQL_INTO_NEXT}{TOKEN_HOST_SEPARATOR}{host}"
            for host in hosts[1:]
        )
        return output


__all__ = ["StatementBlockBuilder"]
# LOCATION: converter/generators/cursor_paragraph/cursor_statement_blocks.py
# ACTION: CREATE NEW FILE
"""Paragraph header, debug trace, EXEC SQL wrapper and the INTO clause.

The mechanical scaffolding of a cursor paragraph. Makes no decision
about diagnostics or flow.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph.cursor_sql_location import (
    SqlLocationBuilder,
)
from rules.cursor_paragraph_rules import (
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

DEBUG_BODY_INDENT = "    "


class StatementBlockBuilder:
    """Renders the non-decisional parts of a cursor paragraph."""

    def __init__(self, sql_location: SqlLocationBuilder | None = None) -> None:
        self.sql_location = sql_location or SqlLocationBuilder()

    def header(self, paragraph_name: str) -> list[str]:
        """Paragraph header plus the optional D-indicator trace line."""
        lines = [PARAGRAPH_HEADER_TEMPLATE.format(paragraph=paragraph_name)]

        if EMIT_DEBUG_TRACE_LINES:
            trace = DEBUG_TRACE_TEMPLATE.format(paragraph=paragraph_name)
            lines.append(f"{DEBUG_INDICATOR}{DEBUG_BODY_INDENT}{trace}")

        return lines

    def prologue(
        self,
        paragraph_name: str,
        statement: str,
        close_exec: bool = True,
    ) -> list[str]:
        """Header, trace, SQL-LOCATION move and the EXEC SQL opening."""
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

    @staticmethod
    def into_lines(host_variables: list[str]) -> list[str]:
        """INTO clause in manual form: first host on INTO, leading commas.

            INTO :DCLDZBEFFTV.CO-IDPRKSK-479BEFF
               , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF
        """
        output: list[str] = []

        for index, host in enumerate(host_variables or []):
            if index == 0:
                output.append(f"{IND_SQL_INTO}{TOKEN_INTO} {host}")
                continue
            output.append(f"{IND_SQL_INTO_NEXT}{TOKEN_HOST_SEPARATOR}{host}")

        return output


__all__ = ["StatementBlockBuilder"]
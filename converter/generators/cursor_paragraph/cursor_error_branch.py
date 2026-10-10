# LOCATION: converter/generators/cursor_paragraph/cursor_error_branch.py
# ACTION: CREATE NEW FILE
"""The WHEN OTHER branch of an EVALUATE SQLCODE block.

Order is fixed and asserted by review:

    WHEN OTHER
         MOVE <nnn> TO SQL-LOCATION      <- CHK-09.05 / CHK-10.05 / CHK-20.07
         DISPLAY '<error text>'
         <row identity DISPLAY lines>    <- FETCH only
         PERFORM SQLERROR
    END-EVALUATE
    .

SQL-LOCATION stays FIRST: those three checks read the first statement
of this branch, and the cursor contract tests assert it explicitly.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph.cursor_key_diagnostics import (
    KeyDiagnosticsBuilder,
)
from converter.generators.cursor_paragraph.cursor_sql_location import (
    SqlLocationBuilder,
)
from rules.cursor_paragraph_rules import (
    DISPLAY_ERROR_TEMPLATE,
    ENFORCE_SQL_LOCATION_IN_ERROR_BRANCH,
    IND_STATEMENT,
    IND_WHEN,
    IND_WHEN_BODY,
    LONE_PERIOD,
    PERFORM_TEMPLATE,
    TOKEN_END_EVALUATE,
    TOKEN_WHEN_OTHER,
)


class ErrorBranchBuilder:
    """Renders WHEN OTHER through the closing period."""

    def __init__(
        self,
        sql_location: SqlLocationBuilder | None = None,
        diagnostics: KeyDiagnosticsBuilder | None = None,
    ) -> None:
        self.sql_location = sql_location or SqlLocationBuilder()
        self.diagnostics = diagnostics or KeyDiagnosticsBuilder()

    def build(
        self,
        error_text: str,
        sql_error_paragraph: str,
        paragraph_name: str = "",
        where_conditions: list[str] | None = None,
        fetched_hosts: list[str] | None = None,
    ) -> list[str]:
        """One WHEN OTHER branch.

        A PARENT cursor passes neither key list and gets the
        cursor-name-only branch the manual reference shows.
        """
        lines: list[str] = [f"{IND_WHEN}{TOKEN_WHEN_OTHER}"]

        if ENFORCE_SQL_LOCATION_IN_ERROR_BRANCH and paragraph_name:
            lines.append(IND_WHEN_BODY + self.sql_location.body(paragraph_name))

        lines.append(
            IND_WHEN_BODY + DISPLAY_ERROR_TEMPLATE.format(text=error_text)
        )

        if where_conditions:
            lines.extend(self.diagnostics.lines_for_where(where_conditions))
        elif fetched_hosts:
            lines.extend(self.diagnostics.lines_for_hosts(fetched_hosts))

        lines.append(
            IND_WHEN_BODY
            + PERFORM_TEMPLATE.format(paragraph=sql_error_paragraph)
        )
        lines.append(f"{IND_STATEMENT}{TOKEN_END_EVALUATE}")
        lines.append(f"{IND_STATEMENT}{LONE_PERIOD}")

        return lines


__all__ = ["ErrorBranchBuilder"]
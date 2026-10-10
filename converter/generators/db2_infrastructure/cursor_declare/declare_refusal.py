# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_refusal.py
# ACTION: CREATE NEW FILE
"""Builds the DB2 WARNING block emitted in place of a refused cursor.

CORRECTION - the warning did not fit a COBOL line.

The single-line templates rendered to ~77 characters with real names.
The body window is columns 8-72, so the fixed-format composer wrapped
or truncated the one comment that explains why a cursor is missing.
The rules-owned *_LINES tuples are sized for the window.

CORRECTION - two refusals were SILENT.

A spec with no cursor name, or no table, emitted a warning into the
COBOL and logged nothing, so the cursor vanished and the conversion
report did not say why. Every refusal reports now.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_declare.declare_diagnostics import (
    DeclareDiagnostics,
)
from rules.cursor_declaration_rules import (
    MISSING_COLUMNS_LINES,
    UNRESOLVED_JOIN_KEY_LINES,
)
from rules.db2_infrastructure_rules import (
    MISSING_CURSOR_NAME,
    MISSING_TABLE_TEMPLATE,
)


class DeclareRefusal:
    """One refusal: a logged reason and the COBOL comment block."""

    def __init__(self, diagnostics: DeclareDiagnostics) -> None:
        self.diagnostics = diagnostics

    def no_cursor_name(self) -> list[str]:
        self.diagnostics.log("missing_cursor_name")
        return [MISSING_CURSOR_NAME]

    def no_table(self, cursor: str) -> list[str]:
        self.diagnostics.log("missing_table", cursor=cursor)
        return [MISSING_TABLE_TEMPLATE.format(cursor=cursor)]

    def no_columns(self, cursor: str, table: str) -> list[str]:
        """Refusing beats SELECT *: CHK-12.04 forbids selecting every
        column, and an implicit list breaks FETCH parity."""
        self.diagnostics.log("select_all_refused", cursor=cursor)
        return self.lines(MISSING_COLUMNS_LINES, cursor=cursor, table=table)

    def unowned_join_key(self, cursor: str, column: str, table: str) -> list[str]:
        self.diagnostics.log(
            "join_key_unresolved",
            column=column,
            table=table,
            cursor=cursor,
        )
        return self.lines(
            UNRESOLVED_JOIN_KEY_LINES,
            cursor=cursor,
            column=column,
            table=table,
        )

    @staticmethod
    def lines(templates, **fields) -> list[str]:
        """Render a rules-owned multi-line warning block.

        str.format ignores surplus keyword arguments, so every line
        receives the full field set and takes what it needs.
        """
        return [
            str(template or "").format(**fields)
            for template in (templates or ())
            if str(template or "").strip()
        ]


__all__ = ["DeclareRefusal"]
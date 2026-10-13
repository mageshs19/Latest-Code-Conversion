# LOCATION: converter/generators/cursor_paragraph/cursor_sql_location.py
# ACTION: REPLACE ENTIRE FILE

"""MOVE <paragraph identity> TO SQL-LOCATION, cursor-path entry point.

SQLERROR displays SQL-LOCATION. Setting it only at paragraph entry lets
any statement in between leave a stale value, sending the operator to
the wrong paragraph - so the error branch sets it again.

The converter must NOT declare SQL-LOCATION: the SQLERRWS copybook owns
it. This module only writes into it.

CORRECTION - this module was the only correct emitter, and was unreachable
-------------------------------------------------------------------------
The rendering logic and its templates both sat under "cursor_paragraph".
The update path could not import them without pretending to be a cursor,
so it inlined its own f-strings and emitted the RECORD name instead of a
paragraph number. Rendering now lives in
converter/generators/db2_infrastructure/sql_location_move_builder.py and
the templates in rules/sql_location_rules.py, where every path can reach
them.

The class name, both method names and their output are unchanged, so
every existing cursor import and assertion holds.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.sql_location_move_builder import (
    SqlLocationMoveBuilder,
)
from rules.cursor_paragraph_rules import IND_STATEMENT

PARAGRAPH_NUMBER_SEPARATOR = "-"


class SqlLocationBuilder:
    """Renders the SQL-LOCATION move in its two indent forms."""

    def __init__(self, mover: SqlLocationMoveBuilder | None = None) -> None:
        self.mover = mover or SqlLocationMoveBuilder()

    def statement(self, paragraph_name: str) -> str:
        """Paragraph-level form, carrying its own indent. No period."""
        return IND_STATEMENT + self.body(paragraph_name)

    def body(self, paragraph_name: str) -> str:
        """Un-indented body, for use inside a WHEN branch.

        The manual reference moves the bare paragraph NUMBER. Falls back
        to the quoted full name when the paragraph is not
        number-prefixed.
        """
        return self.mover.body(paragraph_name)


__all__ = ["SqlLocationBuilder"]
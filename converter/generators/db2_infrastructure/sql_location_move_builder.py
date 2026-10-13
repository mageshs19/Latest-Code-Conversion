# LOCATION: converter/generators/db2_infrastructure/sql_location_move_builder.py
# ACTION: CREATE NEW FILE

"""The one renderer of MOVE ... TO SQL-LOCATION.

Indent-agnostic on purpose: the cursor path, the update rewriter and the
STORE/MODIFY builder each own a different leading indent, and that is the
only thing they legitimately differ on. Callers prepend their own.

NAMED SqlLocationMoveBuilder, NOT SqlLocationBuilder
    SqlLocationBuilder already exists twice in this tree:

        db2_infrastructure/sql_location_builder.py   builds the 01 DECLARATION
        cursor_paragraph/cursor_sql_location.py      builds the MOVE

    Two classes, one name, different jobs, same generators package - an
    import typo away from emitting a declaration where a MOVE belongs.
    This module takes the unambiguous name and the cursor module keeps
    its public name as a delegating shim so no existing import breaks.

REFUSAL
    When the paragraph carries no numeric prefix there is no proven safe
    literal to emit. body() then returns "" and the caller must drop the
    line entirely - never emit a half-built MOVE. Gated by
    EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER so this patch changes no
    output today.
"""

from __future__ import annotations

from rules.sql_location_rules import (
    EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER,
    PARAGRAPH_NUMBER_SEPARATOR,
    SQL_LOCATION_FIELD,
    SQL_LOCATION_NAME_TEMPLATE,
    SQL_LOCATION_NUMBER_PAD,
    SQL_LOCATION_NUMBER_TEMPLATE,
    SQL_LOCATION_USES_PARAGRAPH_NUMBER,
)


class SqlLocationMoveBuilder:
    """Renders the SQL-LOCATION move from a paragraph identity."""

    @staticmethod
    def paragraph_number(paragraph_name: str) -> str:
        """The numeric prefix of a paragraph label, or "".

        1100-UPDATE-VMBFAR -> "1100"
        VERWERKING         -> ""
        """
        name = str(paragraph_name or "").strip()
        if not name:
            return ""

        head = name.split(PARAGRAPH_NUMBER_SEPARATOR, 1)[0]
        return head if head.isdigit() else ""

    def body(self, paragraph_name: str) -> str:
        """Un-indented, no period. "" means: emit nothing at all."""
        name = str(paragraph_name or "").strip()
        if not name:
            return ""

        number = self.paragraph_number(name)

        if SQL_LOCATION_USES_PARAGRAPH_NUMBER and number:
            return SQL_LOCATION_NUMBER_TEMPLATE.format(
                number=number,
                pad=SQL_LOCATION_NUMBER_PAD,
                field=SQL_LOCATION_FIELD,
            )

        if not EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER:
            return ""

        return SQL_LOCATION_NAME_TEMPLATE.format(
            name=name,
            field=SQL_LOCATION_FIELD,
        )

    def sentence(self, paragraph_name: str, leading: str = "") -> str:
        """Full COBOL sentence with its indent and period, or "".

        The form the update emitters need:

            MOVE 1100    TO SQL-LOCATION.
        """
        rendered = self.body(paragraph_name)
        if not rendered:
            return ""
        return f"{leading}{rendered}."


__all__ = ["SqlLocationMoveBuilder"]
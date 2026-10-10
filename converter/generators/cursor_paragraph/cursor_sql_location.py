# LOCATION: converter/generators/cursor_paragraph/cursor_sql_location.py
# ACTION: CREATE NEW FILE
"""MOVE <paragraph identity> TO SQL-LOCATION.

SQLERROR displays SQL-LOCATION. Setting it only at paragraph entry lets
any statement in between leave a stale value, sending the operator to
the wrong paragraph - so the error branch sets it again.

The converter must NOT declare SQL-LOCATION: the SQLERRWS copybook owns
it. This module only writes into it.
"""

from __future__ import annotations

from rules.cursor_paragraph_rules import (
    IND_STATEMENT,
    SQL_LOCATION_FIELD,
    SQL_LOCATION_NAME_TEMPLATE,
    SQL_LOCATION_NUMBER_PAD,
    SQL_LOCATION_NUMBER_TEMPLATE,
    SQL_LOCATION_USES_PARAGRAPH_NUMBER,
)

PARAGRAPH_NUMBER_SEPARATOR = "-"


class SqlLocationBuilder:
    """Renders the SQL-LOCATION move in its two indent forms."""

    def statement(self, paragraph_name: str) -> str:
        """Paragraph-level form, carrying its own indent. No period."""
        return IND_STATEMENT + self.body(paragraph_name)

    def body(self, paragraph_name: str) -> str:
        """Un-indented body, for use inside a WHEN branch.

        The manual reference moves the bare paragraph NUMBER. Falls back
        to the quoted full name when the paragraph is not
        number-prefixed.
        """
        name = str(paragraph_name or "").strip()
        number = name.split(PARAGRAPH_NUMBER_SEPARATOR, 1)[0]

        if SQL_LOCATION_USES_PARAGRAPH_NUMBER and number.isdigit():
            return SQL_LOCATION_NUMBER_TEMPLATE.format(
                number=number,
                pad=SQL_LOCATION_NUMBER_PAD,
                field=SQL_LOCATION_FIELD,
            )

        return SQL_LOCATION_NAME_TEMPLATE.format(
            name=name,
            field=SQL_LOCATION_FIELD,
        )


__all__ = ["SqlLocationBuilder"]
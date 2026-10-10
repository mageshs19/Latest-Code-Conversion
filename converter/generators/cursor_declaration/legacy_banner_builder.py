# LOCATION: converter/generators/cursor_declaration/legacy_banner_builder.py
# ACTION: CREATE NEW FILE
"""The three-line comment banner above a legacy declaration.

    * DECLARE CURSOR FOR BEFF TABLE
    * ------------------------------
    *

This is the ONE thing the legacy generator does that
CursorDeclareBuilder does not. Isolating it is what makes the rest of
the legacy path safe to replace with the shared collaborators.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_declaration_legacy import (
    BANNER_NAME_TRIM,
    TABLE_PREFIX_LENGTH,
    TABLE_VIEW_SUFFIXES,
)
from rules.manual_reference_rules import (
    CURSOR_BANNER_BLANK,
    CURSOR_BANNER_TITLE_TEMPLATE,
    CURSOR_BANNER_UNDERLINE,
)


class LegacyBannerBuilder:
    """Renders the banner. Decides nothing else."""

    def banner(self, table: str) -> list[str]:
        return [
            CURSOR_BANNER_TITLE_TEMPLATE.format(
                short_name=self.short_table_name(table)
            ),
            CURSOR_BANNER_UNDERLINE,
            CURSOR_BANNER_BLANK,
        ]

    @staticmethod
    def short_table_name(table: str) -> str:
        """DZBEFFTV -> BEFF. Prefix and TV/TB suffix removed.

        Falls back to the full normalised name when the convention does
        not apply, rather than returning a mangled fragment. A banner is
        a comment: a wrong one misleads, an absent one does not.
        """
        full = NameNormalizer.normalize(str(table or ""))
        if not full:
            return ""

        token = full
        for suffix in TABLE_VIEW_SUFFIXES:
            if token.endswith(suffix):
                token = token[: -len(suffix)]
                break

        if len(token) > TABLE_PREFIX_LENGTH:
            token = token[TABLE_PREFIX_LENGTH:]

        return token.strip(BANNER_NAME_TRIM) or full


__all__ = ["LegacyBannerBuilder"]
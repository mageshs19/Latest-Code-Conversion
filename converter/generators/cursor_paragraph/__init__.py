# LOCATION: converter/generators/cursor_paragraph/__init__.py
# ACTION: REPLACE ENTIRE FILE
"""Cursor paragraph body generation.

Only the facade is exported. Importing a collaborator directly is fine
inside this package and discouraged outside it.
"""

from converter.generators.cursor_paragraph.cursor_paragraph_body_builder import (
    CursorParagraphBodyBuilder,
)

__all__ = ["CursorParagraphBodyBuilder"]
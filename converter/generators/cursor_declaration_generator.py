# LOCATION: converter/generators/cursor_declaration_generator.py
# ACTION: REPLACE ENTIRE FILE
"""Deprecated. Use CursorDeclareBuilder.

This generator was a second implementation of the DECLARE statement and
had DIVERGED: QUERYNO 253 against 254, an ownership guard that split on
'=' only, and a discarded diagnostics list. One implementation now.
"""

from converter.generators.db2_infrastructure.cursor_declare_builder import (  # noqa: F401
    CursorDeclareBuilder as CursorDeclarationGenerator,
)

__all__ = ["CursorDeclarationGenerator"]
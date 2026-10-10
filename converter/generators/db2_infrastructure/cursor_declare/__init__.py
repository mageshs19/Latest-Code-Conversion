# LOCATION: converter/generators/db2_infrastructure/cursor_declare/__init__.py
# ACTION: CREATE NEW FILE
"""DECLARE CURSOR rendering.

Only the facade is exported. Importing a collaborator directly is fine
inside this package and discouraged outside it.
"""

from converter.generators.db2_infrastructure.cursor_declare.cursor_declare_builder import (
    CursorDeclareBuilder,
)

__all__ = ["CursorDeclareBuilder"]
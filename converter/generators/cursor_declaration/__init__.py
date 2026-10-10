# LOCATION: converter/generators/cursor_declaration/__init__.py
# ACTION: CREATE NEW FILE
"""Legacy cursor declaration generation.

Only the facade is exported. Delete this whole package when the legacy
shape is retired - and delete the legacy indents in
rules/db2_infrastructure_rules.py with it, as that module instructs.
"""

from converter.generators.cursor_declaration.cursor_declaration_generator import (
    CursorDeclarationGenerator,
)

__all__ = ["CursorDeclarationGenerator"]
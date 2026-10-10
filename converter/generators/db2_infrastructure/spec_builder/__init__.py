# LOCATION: converter/generators/db2_infrastructure/spec_builder/__init__.py
# ACTION: CREATE NEW FILE
"""Cursor specification building.

Only the facade is exported. Importing a collaborator directly is fine
inside this package and discouraged outside it.

The package is named spec_builder, NOT cursor_spec: a sibling module
converter/generators/db2_infrastructure/cursor_spec.py already exists
and a package of that name would shadow it.
"""

from converter.generators.db2_infrastructure.spec_builder.cursor_spec_builder import (
    CursorSpecBuilder,
)

__all__ = ["CursorSpecBuilder"]
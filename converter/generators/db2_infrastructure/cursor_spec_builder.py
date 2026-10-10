# LOCATION: converter/generators/db2_infrastructure/cursor_spec_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Backward-compatible import point.

Db2InfrastructureGenerator.__init__ does

    self._spec_builder = CursorSpecBuilder(self)

after importing CursorSpecBuilder from HERE. The implementation moved
into converter/generators/db2_infrastructure/spec_builder/; this module
keeps the old path valid so the split needs no call-site edits.

Delete this file only once every importer has been repointed.
"""

from converter.generators.db2_infrastructure.spec_builder import (  # noqa: F401
    CursorSpecBuilder,
)

__all__ = ["CursorSpecBuilder"]
# LOCATION: converter/generators/db2_infrastructure/cursor_declare_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Backward-compatible import point.

tests/test_cursor_generation_contract.py and
tests/test_cursor_order_by_retention.py both import CursorDeclareBuilder
from HERE, as does InfrastructureBlockBuilder. The implementation moved
into converter/generators/db2_infrastructure/cursor_declare/; this
module keeps the old path valid so the split needs no call-site edits.

Delete this file only once every importer has been repointed.
"""

from converter.generators.db2_infrastructure.cursor_declare import (  # noqa: F401
    CursorDeclareBuilder,
)

__all__ = ["CursorDeclareBuilder"]
# LOCATION: tests/cursor_where/conftest.py
# ACTION: CREATE NEW FILE
"""Fixtures for the cursor WHERE suite.

A FRESH builder per test. CursorDeclareBuilder accumulates diagnostics
across the cursors of one program and caches column ownership per
table; sharing one instance between tests would let one test's
messages satisfy another's assertion.
"""

from __future__ import annotations

import pytest

from converter.generators.db2_infrastructure.cursor_declare_builder import (
    CursorDeclareBuilder,
)
from tests.cursor_where._fixtures import ColumnNameResolver, LineUtils


@pytest.fixture
def declares() -> CursorDeclareBuilder:
    """Builder WITHOUT the ownership guard wired (guard stands down)."""
    return CursorDeclareBuilder(LineUtils())


@pytest.fixture
def guarded_declares() -> CursorDeclareBuilder:
    """Builder WITH the ownership guard wired."""
    return CursorDeclareBuilder(
        LineUtils(),
        column_name_resolver=ColumnNameResolver(),
    )
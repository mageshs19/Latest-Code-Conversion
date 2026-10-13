# LOCATION: tests/update_sql_cleanup/conftest.py
# ACTION: REPLACE ENTIRE FILE
"""Minimal DCLGEN stub for the qualified-date-move pass.

The pass resolves group + host -> column with no table or record
context, so the stub only has to answer three questions.

PATTERN SOURCE

The three patterns the rewriter reads from its owner are re-exported as
CLASS ATTRIBUTES on UpdateSqlCleanupBase, not by composer_patterns.
Reading them from the base class is also the honest stand-in: it is
exactly where the real owner gets them.
"""

from __future__ import annotations

import pytest

from converter.composers.update_sql_cleanup.date_move_builder import (
    DateMoveBuilder,
)
from converter.composers.update_sql_cleanup.qualified_date_move_rewriter import (
    QualifiedDateMoveRewriter,
)
from converter.composers.update_sql_cleanup_base import UpdateSqlCleanupBase
from converter.domain.models import DclgenColumn

TABLE = "DZBFARTV"
GROUP = "DCLDZBFARTV"


class _StubDclgenRepository:
    """Answers tables(), group_for_table() and columns_for_table()."""

    COLUMNS = [
        DclgenColumn(
            table_name=TABLE,
            column_name="DA_CRFMAS_479BFAR",
            cobol_host_name="DA-CRFMAS-479BFAR",
        ),
        DclgenColumn(
            table_name=TABLE,
            column_name="DA_INFSDGD_479BFAR",
            cobol_host_name="DA-INFSDGD-479BFAR",
        ),
        DclgenColumn(
            table_name=TABLE,
            column_name="NR_CIOFMAS_479BFAR",
            cobol_host_name="NR-CIOFMAS-479BFAR",
        ),
    ]

    def tables(self) -> list[str]:
        return [TABLE]

    def group_for_table(self, table_name: str) -> str:
        return GROUP if str(table_name).upper() == TABLE else ""

    def columns_for_table(self, table_name: str) -> list[DclgenColumn]:
        if str(table_name).upper() != TABLE:
            return []
        return list(self.COLUMNS)


class _StubOwner:
    """Supplies only what QualifiedDateMoveRewriter reads from its owner."""

    EXEC_SQL_START_PATTERN = UpdateSqlCleanupBase.EXEC_SQL_START_PATTERN
    EXEC_SQL_END_PATTERN = UpdateSqlCleanupBase.EXEC_SQL_END_PATTERN
    MOVE_TO_DCL_HOST_PATTERN = UpdateSqlCleanupBase.MOVE_TO_DCL_HOST_PATTERN

    def __init__(self) -> None:
        self.dclgen_repository = _StubDclgenRepository()

    @staticmethod
    def _logical(line: str) -> str:
        text = str(line or "")
        body = text[7:72] if len(text) > 7 and text[:6].isdigit() else text
        return " ".join(body.split())

    @staticmethod
    def _leading_spaces(line: str) -> str:
        text = str(line or "")
        return text[: len(text) - len(text.lstrip())]


@pytest.fixture
def composer() -> QualifiedDateMoveRewriter:
    return QualifiedDateMoveRewriter(
        owner=_StubOwner(),
        date_builder=DateMoveBuilder(),
    )
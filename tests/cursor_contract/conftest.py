from __future__ import annotations

import pytest

from converter.generators.cursor_paragraph.cursor_paragraph_body_builder import (
    CursorParagraphBodyBuilder,
)
from converter.generators.db2_infrastructure.cursor_declare_builder import (
    CursorDeclareBuilder,
)
from converter.generators.db2_infrastructure.cursor_spec import CursorSpec
from rules.cursor_declaration_rules import QUERYNO_BASE, QUERYNO_STEP

CURSOR = "DZBFASC1"
GROUP = "DCLDZBFASTV"
TABLE = "DZBFASTV"
RECORD = "VMBFAS"
SQL_ERROR = "SQLERROR"
SQL_LOCATION_SUFFIX = "TO SQL-LOCATION"
COLUMNS = ["DA_CPTAFS_479BFAS", "DA_CRFMAS_479BFAS"]
HOSTS = [
    f":{GROUP}.DA-CPTAFS-479BFAS",
    f":{GROUP}.DA-CRFMAS-479BFAS",
]


class LineUtilsStub:

    @staticmethod
    def and_lines(items: list[str], indent: str) -> list[str]:
        return [
            f"{indent}{'AND ' if index else ''}{item}"
            for index, item in enumerate(items)
        ]

    @staticmethod
    def comma_lines(items: list[str], indent: str) -> list[str]:
        return [
            f"{indent}{', ' if index else ''}{item}"
            for index, item in enumerate(items)
        ]


@pytest.fixture
def names() -> dict:
    return {
        "cursor": CURSOR,
        "group": GROUP,
        "table": TABLE,
        "record": RECORD,
        "sql_error": SQL_ERROR,
        "suffix": SQL_LOCATION_SUFFIX,
        "hosts": list(HOSTS),
        "columns": list(COLUMNS),
        "open_paragraph": f"710-OPEN-{CURSOR}",
        "fetch_paragraph": f"720-FETCH-{CURSOR}",
        "close_paragraph": f"730-CLOSE-{CURSOR}",
        "queryno_base": QUERYNO_BASE,
        "queryno_step": QUERYNO_STEP,
    }


@pytest.fixture
def paragraphs() -> CursorParagraphBodyBuilder:
    return CursorParagraphBodyBuilder()


@pytest.fixture
def declares() -> CursorDeclareBuilder:
    return CursorDeclareBuilder(LineUtilsStub())


@pytest.fixture
def bodies():
    def _bodies(lines: list[str]) -> list[str]:
        return [line.strip() for line in lines if line.strip()]

    return _bodies


@pytest.fixture
def clause_index():
    def _index(items: list[str], token: str) -> int:
        for position, body in enumerate(items):
            if body.upper().startswith(token.upper()):
                return position
        return -1

    return _index


@pytest.fixture
def has_clause(clause_index):
    def _has(items: list[str], token: str) -> bool:
        return clause_index(items, token) >= 0

    return _has


@pytest.fixture
def when_other(clause_index):
    def _branch(items: list[str]) -> list[str]:
        start = clause_index(items, "WHEN OTHER")
        if start < 0:
            return []
        end = len(items)
        for position in range(start + 1, len(items)):
            if items[position].upper().startswith("END-EVALUATE"):
                end = position
                break
        return items[start + 1:end]

    return _branch


@pytest.fixture
def sql_moves():
    def _moves(items: list[str]) -> list[str]:
        return [
            body for body in items
            if body.endswith(SQL_LOCATION_SUFFIX)
        ]

    return _moves


@pytest.fixture
def fetch(paragraphs, bodies):
    def _fetch(**overrides) -> list[str]:
        arguments = {
            "cursor_name": CURSOR,
            "paragraph_name": f"720-FETCH-{CURSOR}",
            "host_variables": list(HOSTS),
            "sql_error_paragraph": SQL_ERROR,
        }
        arguments.update(overrides)
        return bodies(paragraphs.fetch_paragraph(**arguments))

    return _fetch


@pytest.fixture
def cursor_paragraph(paragraphs, bodies):
    def _build(shape: str, paragraph_name: str) -> list[str]:
        return bodies(
            getattr(paragraphs, shape)(
                cursor_name=CURSOR,
                paragraph_name=paragraph_name,
                sql_error_paragraph=SQL_ERROR,
            )
        )

    return _build


@pytest.fixture
def spec():
    def _spec(order: int = 0, **overrides) -> CursorSpec:
        source = {
            "cursor_name": CURSOR,
            "table_name": TABLE,
            "record_name": RECORD,
            "select_columns": list(COLUMNS),
            "cursor_order": order,
        }
        source.update(overrides)
        return CursorSpec.read(source)

    return _spec
from __future__ import annotations

import pytest

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.scope_initializer import (
    CursorScopedInitializer,
)

AREA_A = " " * 7
AREA_B = " " * 11


def _render(body: str) -> str:
    text = str(body or "").rstrip()
    if not text:
        return ""
    if text.endswith(".") and " " not in text:
        return f"{AREA_A}{text}"
    return f"{AREA_B}{text}"


def _fetch_block(cursor: str, group: str, field: str) -> list[str]:
    return [
        f"{cursor_paragraph_number(cursor)}-FETCH-{cursor}.",
        "EXEC SQL",
        f"FETCH {cursor}",
        f"INTO :{group}.{field}",
        "END-EXEC",
        ".",
    ]


def cursor_paragraph_number(cursor: str) -> str:
    return {"AAAC1": "720", "BBBC1": "820", "CCCC1": "920"}.get(
        cursor, "720"
    )


def _drive(cursor: str, open_number: str) -> list[str]:
    close_number = str(int(open_number) + 20)
    fetch_number = str(int(open_number) + 10)
    return [
        f"PERFORM {open_number}-OPEN-{cursor}",
        f"PERFORM {fetch_number}-FETCH-{cursor} UNTIL {cursor}-EOC",
        f"PERFORM {close_number}-CLOSE-{cursor}",
    ]


@pytest.fixture
def program():
    def _program(lines: list[str]) -> str:
        return "\n".join(_render(line) for line in lines)

    return _program


@pytest.fixture
def run():
    def _run(text: str):
        initializer = CursorScopedInitializer(text)
        return initializer.process(), list(initializer.messages)

    return _run


@pytest.fixture
def bodies():
    def _bodies(text: str) -> list[str]:
        return [
            LineGeometry.body(line)
            for line in LineGeometry.split(text)
            if LineGeometry.body(line)
        ]

    return _bodies


@pytest.fixture
def index_of():
    def _index(items: list[str], prefix: str) -> int:
        for position, body in enumerate(items):
            if body.upper().startswith(prefix.upper()):
                return position
        return -1

    return _index


@pytest.fixture
def count_of():
    def _count(items: list[str], prefix: str) -> int:
        return len(
            [b for b in items if b.upper().startswith(prefix.upper())]
        )

    return _count


@pytest.fixture
def single_cursor_lines() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        "OPEN OUTPUT OUTFILE",
        *_drive("AAAC1", "710"),
        "CLOSE OUTFILE",
        "STOP RUN.",
        *_fetch_block("AAAC1", "DCLAAATV", "FIELD-ONE"),
    ]


@pytest.fixture
def parent_child_lines() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        *_drive("AAAC1", "710"),
        "STOP RUN.",
        "ROW-WORK.",
        "MOVE SPACE TO WS-STATUS",
        *_drive("BBBC1", "810"),
        *_fetch_block("AAAC1", "DCLAAATV", "FIELD-ONE"),
        *_fetch_block("BBBC1", "DCLBBBTV", "FIELD-TWO"),
    ]


@pytest.fixture
def three_level_lines() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        *_drive("AAAC1", "710"),
        "STOP RUN.",
        "ROW-WORK.",
        *_drive("BBBC1", "810"),
        "DEEP-WORK.",
        *_drive("CCCC1", "910"),
        *_fetch_block("AAAC1", "DCLAAATV", "FIELD-ONE"),
        *_fetch_block("BBBC1", "DCLBBBTV", "FIELD-TWO"),
        *_fetch_block("CCCC1", "DCLCCCTV", "FIELD-THREE"),
    ]


@pytest.fixture
def legacy_startup_lines() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        "MOVE CS-PROGRAM   TO PROGRAM-NAME",
        "PERFORM 100-INITIALIZE.",
        *_drive("AAAC1", "710"),
        "STOP RUN.",
        "100-INITIALIZE.",
        "INITIALIZE DCLAAATV.",
        "INITIALIZE DCLBBBTV.",
        "MOVE CS-PROGRAM   TO PROGRAM-NAME.",
        "PERFORM 600-GET-TIMESTAMP.",
        "ROW-WORK.",
        *_drive("BBBC1", "810"),
        *_fetch_block("AAAC1", "DCLAAATV", "FIELD-ONE"),
        *_fetch_block("BBBC1", "DCLBBBTV", "FIELD-TWO"),
        "600-GET-TIMESTAMP.",
        "MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.",
    ]
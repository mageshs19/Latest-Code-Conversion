from __future__ import annotations

import pytest

from converter.composers.output_write_paragraph_composer import (
    OutputWriteParagraphComposer,
)

AREA_A = " " * 7
AREA_B = " " * 11


def _render(body: str) -> str:
    text = str(body or "").rstrip()
    if not text:
        return ""
    stripped = text.lstrip()
    if stripped.endswith("DIVISION.") or stripped.endswith("SECTION."):
        return f"{AREA_A}{stripped}"
    if stripped.endswith(".") and " " not in stripped:
        return f"{AREA_A}{stripped}"
    return f"{AREA_B}{stripped}"

@pytest.fixture
def program():
    def _program(lines: list[str]) -> str:
        return "\n".join(_render(line) for line in lines)

    return _program


@pytest.fixture
def compose():
    def _compose(text: str):
        composer = OutputWriteParagraphComposer()
        return composer.compose(text), list(composer.messages)

    return _compose


@pytest.fixture
def bodies():
    def _bodies(text: str) -> list[str]:
        return [
            line.strip()
            for line in str(text or "").splitlines()
            if line.strip()
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
def single_line_guard() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        "HOOFDVERWERKING.",
        "IF WS-STATUS = 'C'",
        "INITIALIZE UITRECORD",
        "MOVE WS-A TO UIT-A",
        "WRITE UITRECORD",
        "END-IF.",
        "EXIT.",
    ]


@pytest.fixture
def four_line_guard() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        "BEHANDELING.",
        "IF (HELP-DA-A < DA-ARCH-YMD AND",
        "HELP-DA-A NOT = '00000000') OR",
        "(HELP-DA-B < DA-ARCH-YMD AND",
        "HELP-DA-A = '00000000')",
        "INITIALIZE REC-FORM",
        "MOVE WS-A TO F-A",
        "WRITE REC-FORM",
        "END-IF.",
        "EXIT.",
    ]


@pytest.fixture
def two_writes() -> list[str]:
    return [
        "PROCEDURE DIVISION.",
        "BEHANDELING.",
        "IF WS-STATUS = 'C'",
        "INITIALIZE UITRECORD",
        "WRITE UITRECORD",
        "WRITE UITRECORD",
        "END-IF.",
        "EXIT.",
    ]
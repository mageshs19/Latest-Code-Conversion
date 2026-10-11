from __future__ import annotations

import pytest

from converter.generators.timestamp.cs_program_declarator import (
    CsProgramDeclarator,
)
from converter.services.generated_field_anchor import (
    GeneratedFieldAnchorResolver,
)

AREA_A = " " * 7
AREA_B = " " * 11


def _render(body: str) -> str:
    text = str(body or "").rstrip()
    if not text:
        return ""
    stripped = text.lstrip()
    if stripped.startswith(("01 ", "FD ")) or stripped.endswith("SECTION."):
        return f"{AREA_A}{stripped}"
    if stripped.endswith("DIVISION."):
        return f"{AREA_A}{stripped}"
    return f"{AREA_B}{stripped}"


@pytest.fixture
def program():
    def _program(lines: list[str]) -> list[str]:
        return [_render(line) for line in lines]

    return _program


@pytest.fixture
def resolve():
    def _resolve(lines: list[str]):
        resolver = GeneratedFieldAnchorResolver()
        updated, anchor = resolver.resolve(lines)
        return updated, anchor, list(resolver.messages)

    return _resolve


@pytest.fixture
def declare():
    def _declare(lines: list[str], program_id: str = "VMDZTEST"):
        declarator = CsProgramDeclarator()
        updated = declarator.declare(lines, program_id)
        return updated, list(declarator.messages)

    return _declare


@pytest.fixture
def bodies():
    def _bodies(lines: list[str]) -> list[str]:
        return [line.strip() for line in lines if line.strip()]

    return _bodies


@pytest.fixture
def with_work_group() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  WS-TE-WORK.",
        "10  WS-STATUS                PIC X    VALUE SPACE.",
        "PROCEDURE DIVISION.",
        "STOP RUN.",
    ]


@pytest.fixture
def with_generated_group() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  WS-DATUMVELDEN.",
        "03  DA-CCYYMMDD              PIC 9(8).",
        "01  WS-DB2-COUNTERS.",
        "10  WS-NB-BFAS-COUNT         PIC 9(7)    COMP-3 VALUE ZEROES.",
        "PROCEDURE DIVISION.",
        "STOP RUN.",
    ]


@pytest.fixture
def without_any_known_group() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  WS-DATUMVELDEN.",
        "03  DA-CCYYMMDD              PIC 9(8).",
        "PROCEDURE DIVISION.",
        "STOP RUN.",
    ]


@pytest.fixture
def with_record_layout() -> list[str]:
    return [
        "DATA DIVISION.",
        "FILE SECTION.",
        "FD  OUTFILE",
        "RECORD CONTAINS 50 CHARACTERS.",
        "01  OUTRECORD.",
        "03  OUT-ID                   PIC X(04).",
        "WORKING-STORAGE SECTION.",
        "01  REC-FORM.",
        "05  F-FORM                   PIC X(478).",
        "PROCEDURE DIVISION.",
        "WRITE REC-FORM",
        "STOP RUN.",
    ]


@pytest.fixture
def with_childless_group() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  W-NR-IS-FORM-AS          PIC X(9).",
        "PROCEDURE DIVISION.",
        "STOP RUN.",
    ]


@pytest.fixture
def without_working_storage() -> list[str]:
    return [
        "DATA DIVISION.",
        "PROCEDURE DIVISION.",
        "STOP RUN.",
    ]
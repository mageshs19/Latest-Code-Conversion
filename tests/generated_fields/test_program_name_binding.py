from __future__ import annotations

import pytest

from converter.generators.timestamp.program_name_binder import (
    ProgramNameBinder,
)


@pytest.fixture
def bind():
    def _bind(lines: list[str]):
        binder = ProgramNameBinder()
        return binder.bind(lines), list(binder.messages)

    return _bind


@pytest.fixture
def declared() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  WS-TE-WORK.",
        "10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.",
        "PROCEDURE DIVISION.",
        "MOVE 'VMDZ4420' TO PROGRAM-NAME.",
        "STOP RUN.",
    ]


@pytest.fixture
def undeclared() -> list[str]:
    return [
        "DATA DIVISION.",
        "WORKING-STORAGE SECTION.",
        "01  WS-TE-WORK.",
        "10  WS-STATUS                PIC X    VALUE SPACE.",
        "PROCEDURE DIVISION.",
        "MOVE 'VMDZ4420' TO PROGRAM-NAME.",
        "STOP RUN.",
    ]


def test_the_literal_is_replaced_by_the_constant(
    program, bind, bodies, declared
):
    out, _messages = bind(program(declared))
    text = bodies(out)

    assert any(b.startswith("MOVE CS-PROGRAM") for b in text)
    assert not any("'VMDZ4420' TO PROGRAM-NAME" in b for b in text)


def test_the_terminator_is_preserved(program, bind, bodies, declared):
    out, _messages = bind(program(declared))
    moves = [b for b in bodies(out) if b.startswith("MOVE CS-PROGRAM")]

    assert moves[0].endswith(".")


def test_the_rewrite_is_reported(program, bind, declared):
    _out, messages = bind(program(declared))
    assert any("CS-PROGRAM" in m for m in messages)


def test_an_undeclared_constant_refuses_the_rewrite(
    program, bind, bodies, undeclared
):
    out, messages = bind(program(undeclared))
    text = bodies(out)

    assert any("'VMDZ4420' TO PROGRAM-NAME" in b for b in text)
    assert any("not declared" in m for m in messages)


def test_binding_is_idempotent(program, bind, declared):
    once, _messages = bind(program(declared))
    twice, messages = bind(once)

    assert once == twice
    assert any("already set" in m for m in messages)


def test_a_business_literal_move_is_untouched(program, bind, bodies):
    lines = program(
        [
            "DATA DIVISION.",
            "WORKING-STORAGE SECTION.",
            "01  WS-TE-WORK.",
            "10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.",
            "PROCEDURE DIVISION.",
            "MOVE 'ABC' TO WS-STATUS",
            "STOP RUN.",
        ]
    )
    out, _messages = bind(lines)

    assert any("MOVE 'ABC' TO WS-STATUS" in b for b in bodies(out))
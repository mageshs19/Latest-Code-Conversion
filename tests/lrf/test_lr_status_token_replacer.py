# LOCATION: tests/lrf/test_lr_status_token_replacer.py
# ACTION: REPLACE ENTIRE FILE
"""The DB-REC-FOUND -> SQLCODE substitution, and its refusals.

SCOPE CHANGE - this suite previously asserted that the replacer owned
all three status tokens. It owns ONE. DB-END-OF-SET and
DB-REC-NOT-FOUND belong to the IDMS statement transformer; this pass
runs before it and must leave them alone.
"""

from __future__ import annotations

import pytest

from converter.transformers.lr_status_token_replacer import (
    LrStatusTokenReplacer,
)
from rules.lrf_conversion_rules import (
    END_OF_SET_TOKEN,
    LR_STATUS_TOKEN_SQLCODE,
    RECORD_FOUND_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
    TOKENS_OWNED_DOWNSTREAM,
)


def _fixed(body: str, seq: str = "001000", right: str = "01000000") -> str:
    assert len(body) <= 65, body
    return seq + " " + body.ljust(65) + right


def _program(*bodies: str) -> str:
    lines = [_fixed("    PROCEDURE DIVISION.")]
    lines.extend(_fixed(b) for b in bodies)
    return "\n".join(lines)


def _bodies(text: str) -> list[str]:
    return [line[7:72].strip() for line in text.splitlines()]


# ------------------------------------------------------------ positive
def test_record_found_becomes_sqlcode_0() -> None:
    out = LrStatusTokenReplacer().apply(
        _program(f"    IF {RECORD_FOUND_TOKEN}")
    )
    bodies = _bodies(out)
    assert "IF SQLCODE = 0" in bodies
    assert "IF SQLCODE = 100" not in bodies


def test_negation_is_carried_through_unchanged() -> None:
    out = LrStatusTokenReplacer().apply(
        _program(f"    IF NOT {RECORD_FOUND_TOKEN}")
    )
    assert "IF NOT SQLCODE = 0" in _bodies(out)


# -------------------------------------------------------------- scope
@pytest.mark.parametrize("token", [END_OF_SET_TOKEN, RECORD_NOT_FOUND_TOKEN])
def test_tokens_owned_elsewhere_are_left_intact(token) -> None:
    """VM4BD420 carried four native DB-END-OF-SET conditions and this
    pass claimed all of them. The statement transformer owns them."""
    source = _program(f"    IF {token}")
    assert LrStatusTokenReplacer().apply(source) == source


def test_on_clause_is_never_disarmed() -> None:
    """ON DB-REC-NOT-FOUND must survive to ON_DB_REC_NOT_FOUND_PATTERN.
    Rewriting it to 'ON SQLCODE = 100' leaves a residual IDMS clause."""
    source = _program(f"    ON {RECORD_NOT_FOUND_TOKEN} MOVE +1 TO SW-X")
    assert LrStatusTokenReplacer().apply(source) == source


def test_mixed_program_converts_only_the_owned_token() -> None:
    out = LrStatusTokenReplacer().apply(
        _program(
            f"    IF {RECORD_FOUND_TOKEN}",
            f"    UNTIL {END_OF_SET_TOKEN}",
        )
    )
    bodies = _bodies(out)
    assert "IF SQLCODE = 0" in bodies
    assert f"UNTIL {END_OF_SET_TOKEN}" in bodies


# ------------------------------------------------------------ geometry
def test_fixed_format_columns_are_preserved() -> None:
    out = LrStatusTokenReplacer().apply(
        _program(f"    IF {RECORD_FOUND_TOKEN}")
    )
    changed = [l for l in out.splitlines() if "SQLCODE" in l]
    assert changed
    for line in changed:
        assert len(line) == 80
        assert line[0:6].isdigit()
        assert line[72:80].isdigit()


# ------------------------------------------------------------ contract
def test_program_without_tokens_is_returned_byte_for_byte() -> None:
    source = _program("    MOVE 0 TO WS-COUNT")
    assert LrStatusTokenReplacer().apply(source) == source


def test_tokens_before_procedure_division_are_untouched() -> None:
    source = "\n".join(
        [
            _fixed(f"    88 {RECORD_FOUND_TOKEN}     VALUE 1."),
            _fixed("    PROCEDURE DIVISION."),
        ]
    )
    assert LrStatusTokenReplacer().apply(source) == source


def test_comment_lines_are_untouched() -> None:
    source = "\n".join(
        [
            _fixed("    PROCEDURE DIVISION."),
            "001100*" + f"DB2: {RECORD_FOUND_TOKEN} audit".ljust(65)
            + "01100000",
        ]
    )
    assert RECORD_FOUND_TOKEN in LrStatusTokenReplacer().apply(source)


def test_replacement_is_reported() -> None:
    replacer = LrStatusTokenReplacer()
    replacer.apply(_program(f"    IF {RECORD_FOUND_TOKEN}"))
    assert any("replaced 1" in m for m in replacer.messages)
    assert any(RECORD_FOUND_TOKEN in m for m in replacer.messages)
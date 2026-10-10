"""Regression test for the bare ON DB-REC-NOT-FOUND conversion.

When the ON clause sits on its own line (the guarded imperative statement is on
the following line), the converter must open a valid COBOL guard
``IF SQLCODE = 100`` rather than letting the line reach the blind token
replacement, which produced the uncompilable ``ON SQLCODE = 100`` (ON is not a
COBOL statement).
"""

from __future__ import annotations

from idms_db2_phase2.transformers.idms_statement.data_statement_converter import (
    DataStatementConverterMixin,
)
from rules.idms_transformer_rules import (
    SQLCODE_100_IF_CLOSE,
    SQLCODE_100_IF_OPEN,
)


def _converter() -> DataStatementConverterMixin:
    return DataStatementConverterMixin.__new__(DataStatementConverterMixin)


def test_bare_on_opens_a_valid_if_guard() -> None:
    result = _converter()._convert_on_db_rec_not_found("ON DB-REC-NOT-FOUND")
    assert result == [SQLCODE_100_IF_OPEN]


def test_bare_on_with_trailing_period_opens_a_valid_if_guard() -> None:
    result = _converter()._convert_on_db_rec_not_found("ON DB-REC-NOT-FOUND.")
    assert result == [SQLCODE_100_IF_OPEN]


def test_bare_on_never_emits_the_invalid_on_sqlcode_statement() -> None:
    result = _converter()._convert_on_db_rec_not_found("ON DB-REC-NOT-FOUND")
    assert result is not None
    for line in result:
        assert not line.upper().lstrip().startswith("ON SQLCODE")


def test_same_line_on_still_builds_the_full_guard_block() -> None:
    result = _converter()._convert_on_db_rec_not_found(
        "ON DB-REC-NOT-FOUND MOVE +1 TO SW-FFRECAB"
    )
    assert result[0] == SQLCODE_100_IF_OPEN
    assert result[-1] == SQLCODE_100_IF_CLOSE
    assert any("MOVE +1 TO SW-FFRECAB" in line for line in result)


def test_unrelated_line_is_not_claimed() -> None:
    assert _converter()._convert_on_db_rec_not_found("MOVE 0 TO X") is None

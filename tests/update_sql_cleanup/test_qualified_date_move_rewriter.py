# LOCATION: tests/update_sql_cleanup/test_qualified_date_move_rewriter.py
# ACTION: CREATE NEW FILE
"""The defect: a DATE column that arrived QUALIFIED lost its conversion.

BareMoveRewriter anchors on end-of-line after the target, so
'MOVE src TO HOST OF DCLGROUP' never reached DateMoveBuilder. The host
is DB2 external (DD.MM.CCYY), the source is CCYYMMDD, and the WHERE
predicate built on that host matched zero rows.
"""

from __future__ import annotations

import pytest

from converter.composers.update_sql_cleanup.qualified_date_move_rewriter import (
    QualifiedDateMoveRewriter,
)


def _logical(lines):
    return [" ".join(str(l).upper().split()) for l in lines if str(l).strip()]


def test_a_qualified_date_move_gains_the_conversion_block(composer):
    source = "       MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR OF DCLDZBFARTV\n"
    body = _logical(composer.rewrite(source).splitlines())

    assert "MOVE ZEROES TO DA-CCYYMMDD" in body
    assert "MOVE DA-CREA-FORM-AS-R TO DA-CCYYMMDD" in body
    assert "IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES" in body
    assert "MOVE 00010101 TO DA-CCYYMMDD" in body
    assert "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY" in body
    assert "MOVE DA-DD-MM-CCYY TO DA-CRFMAS-479BFAR OF DCLDZBFARTV" in body


def test_the_continuation_form_is_matched(composer):
    """The column-72 wrapper pushes the qualifier onto the next line."""
    source = (
        "       MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR\n"
        "                                 OF DCLDZBFARTV\n"
    )
    body = _logical(composer.rewrite(source).splitlines())
    assert "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY" in body


def test_a_non_date_column_is_left_alone(composer):
    source = "       MOVE NR-CIO-FORM-AS-R TO NR-CIOFMAS-479BFAR OF DCLDZBFARTV\n"
    body = _logical(composer.rewrite(source).splitlines())
    assert "DA-CCYYMMDD" not in " ".join(body)


def test_the_pass_is_idempotent(composer):
    source = "       MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR OF DCLDZBFARTV\n"
    once = composer.rewrite(source)
    twice = composer.rewrite(once)
    assert _logical(once.splitlines()).count(
        "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY"
    ) == _logical(twice.splitlines()).count(
        "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY"
    )


def test_a_move_inside_exec_sql_is_never_touched(composer):
    source = (
        "       EXEC SQL\n"
        "         MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR OF DCLDZBFARTV\n"
        "       END-EXEC\n"
    )
    assert "DA-CCYYMMDD" not in composer.rewrite(source)


def test_the_conversion_is_reported(composer):
    composer.rewrite(
        "       MOVE DA-CREA-FORM-AS-R TO DA-CRFMAS-479BFAR OF DCLDZBFARTV\n"
    )
    assert any("Qualified date move" in m for m in composer.messages)
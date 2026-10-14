# LOCATION: tests/cursor_close_guarantee/test_fetch_business_binder_span_conflict.py
# ACTION: CREATE NEW FILE
"""FetchBusinessBinder - SPAN-loop double-drive regression.

GOVERNING DEFECT (observed in VMDZ7200's generated and baseline output,
never in the hand-authored Manual Output reference for the same program)
-----------------------------------------------------------------------
cursor_flow's SPAN strategy is documented as deliberately conservative:
it leaves a program shaped as

    PERFORM BEHANDELING THRU BEHANDELING-EXIT UNTIL DZBFASC1-EOC.
    ...
    BEHANDELING.
        ...
        PERFORM 720-FETCH-DZBFASC1.

exactly as-is - BEHANDELING already drives its own iteration and
re-fetches itself at its own tail. FetchBusinessBinder runs later,
path-independently of cursor_flow, and - before the fix - had no way to
see that decision. Finding a bare CONTINUE under 720-FETCH-DZBFASC1's
WHEN ZERO, it bound PERFORM BEHANDELING there too, creating mutual
recursion (FETCH -> BEHANDELING -> FETCH -> ...) that silently drains
the whole cursor the first time the FETCH paragraph is called, leaving
the external "UNTIL DZBFASC1-EOC" loop structurally present but
functionally dead.

THREE THINGS THIS SUITE PROVES
-------------------------------
1. The new guard refuses to bind when a genuine external SPAN loop
   already owns the business paragraph for this cursor's EOC flag.
2. The guard does NOT regress the file's original purpose: a classic
   INLINE cursor (external loop drives the FETCH paragraph itself, no
   SPAN loop anywhere) still gets its WHEN ZERO bound correctly.
3. Binding remains idempotent: running bind() twice never double-binds
   and never raises.
"""

from __future__ import annotations

import pytest

from converter.composers.cursor_close_guarantee.fetch_business_binder import (
    FetchBusinessBinder,
)

from converter.composers.cursor_close_guarantee.fetch_business_binder import (
    FetchBusinessBinder,
)
# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

_DRIVEN_AND_FETCHES = [
    "PROCEDURE DIVISION.",
    "    PERFORM 710-OPEN-DZBFASC1.",
    "    PERFORM BEHANDELING THRU BEHANDELING-EXIT",
    "        UNTIL DZBFASC1-EOC.",
    "    PERFORM 730-CLOSE-DZBFASC1.",
    "    GOBACK.",
    "BEHANDELING.",
    "    MOVE ZEROES TO DA-CCYYMMDD",
    "    PERFORM 720-FETCH-DZBFASC1.",
    "BEHANDELING-EXIT.",
    "    EXIT.",
]

_DRIVEN_BUT_NEVER_FETCHES = [
    "PROCEDURE DIVISION.",
    "    PERFORM 710-OPEN-DZBFASC1.",
    "    PERFORM BEHANDELING THRU BEHANDELING-EXIT",
    "        UNTIL DZBFASC1-EOC.",
    "    PERFORM 730-CLOSE-DZBFASC1.",
    "    GOBACK.",
    "BEHANDELING.",
    "    MOVE ZEROES TO DA-CCYYMMDD",
    "BEHANDELING-EXIT.",
    "    EXIT.",
]

@pytest.fixture
def binder() -> FetchBusinessBinder:
    return FetchBusinessBinder()


@pytest.fixture
def span_conflict_lines() -> list[str]:
    """VMDZ7200-shaped SPAN idiom: BEHANDELING already drives itself.

    Mirrors the real BEGIN-PROGRAMMA / BEHANDELING / 720-FETCH-DZBFASC1
    structure traced from VMDZ7200's BASELINE and GENERATED output, with
    one deliberate simplification: BEGIN-PROGRAMMA is PERFORMed without
    a THRU clause, so it needs no separate -EXIT paragraph of its own -
    this keeps the fixture focused on the SPAN-conflict path being
    tested, rather than on BEGIN-PROGRAMMA's own paragraph boundaries.
    """
    return [
        "PERFORM 600-GET-TIMESTAMP.",
        "PERFORM BEGIN-PROGRAMMA.",
        "PERFORM BEHANDELING THRU BEHANDELING-EXIT",
        "UNTIL DZBFASC1-EOC.",
        "PERFORM 730-CLOSE-DZBFASC1.",
        "GOBACK.",
        "BEGIN-PROGRAMMA.",
        "OPEN INPUT DAARCH OUTPUT FORM.",
        "PERFORM 710-OPEN-DZBFASC1.",
        "PERFORM 720-FETCH-DZBFASC1.",
        "BEHANDELING.",
        "MOVE DA-CPTAFS-479BFAS OF DCLDZBFASTV TO DA-DD-MM-CCYY",
        "IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD)",
        "PERFORM WRITE-FORM-REC",
        "END-IF.",
        "PERFORM 720-FETCH-DZBFASC1.",
        "BEHANDELING-EXIT.",
        "EXIT.",
        "WRITE-FORM-REC.",
        "WRITE FORM-REC FROM REC-FORM.",
        "710-OPEN-DZBFASC1.",
        "EXEC SQL",
        "OPEN DZBFASC1",
        "END-EXEC",
        "EVALUATE SQLCODE",
        "WHEN ZERO",
        "SET DZBFASC1-NOT-EOC TO TRUE",
        "WHEN OTHER",
        "PERFORM SQLERROR",
        "END-EVALUATE.",
        "720-FETCH-DZBFASC1.",
        "SET DZBFASC1-NOT-EOC TO TRUE",
        "EXEC SQL",
        "FETCH DZBFASC1",
        "INTO :DCLDZBFASTV.DA-CPTAFS-479BFAS",
        "END-EXEC",
        "EVALUATE SQLCODE",
        "WHEN ZERO",
        "CONTINUE",
        "WHEN 100",
        "SET DZBFASC1-EOC TO TRUE",
        "WHEN OTHER",
        "PERFORM SQLERROR",
        "END-EVALUATE.",
        "730-CLOSE-DZBFASC1.",
        "EXEC SQL",
        "CLOSE DZBFASC1",
        "END-EXEC.",
    ]


@pytest.fixture
def inline_control_lines() -> list[str]:
    """Classic INLINE idiom: the external loop drives the FETCH paragraph
    itself, with no SPAN loop anywhere. This is the exact shape
    FetchBusinessBinder was built to fix, and must keep working.
    """
    return [
        "PERFORM 600-GET-TIMESTAMP.",
        "PERFORM BEGIN-PROGRAMMA.",
        "PERFORM 720-FETCH-DZBEFFC1",
        "UNTIL DZBEFFC1-EOC.",
        "PERFORM 730-CLOSE-DZBEFFC1.",
        "GOBACK.",
        "BEGIN-PROGRAMMA.",
        "PERFORM 710-OPEN-DZBEFFC1.",
        "HOOFDVERWERKING.",
        "MOVE FIELD-ONE OF DCLDZBEFFTV TO WS-FIELD",
        "710-OPEN-DZBEFFC1.",
        "EXEC SQL",
        "OPEN DZBEFFC1",
        "END-EXEC",
        "EVALUATE SQLCODE",
        "WHEN ZERO",
        "SET DZBEFFC1-NOT-EOC TO TRUE",
        "WHEN OTHER",
        "PERFORM SQLERROR",
        "END-EVALUATE.",
        "720-FETCH-DZBEFFC1.",
        "SET DZBEFFC1-NOT-EOC TO TRUE",
        "EXEC SQL",
        "FETCH DZBEFFC1",
        "INTO :DCLDZBEFFTV.FIELD-ONE",
        "END-EXEC",
        "EVALUATE SQLCODE",
        "WHEN ZERO",
        "CONTINUE",
        "WHEN 100",
        "SET DZBEFFC1-EOC TO TRUE",
        "WHEN OTHER",
        "PERFORM SQLERROR",
        "END-EVALUATE.",
        "730-CLOSE-DZBEFFC1.",
        "EXEC SQL",
        "CLOSE DZBEFFC1",
        "END-EXEC.",
    ]


# ---------------------------------------------------------------------
# 1. Unit tests - already_externally_driven() in isolation
# ---------------------------------------------------------------------

def test_detects_span_loop_on_one_physical_line(binder):
    lines = [
        "PERFORM BEHANDELING THRU BEHANDELING-EXIT UNTIL DZBFASC1-EOC.",
        "BEHANDELING.",
        "EXIT.",
    ]
    assert binder.already_externally_driven(lines, "DZBFASC1", "BEHANDELING")


def test_detects_span_loop_split_across_continuation_line(
    binder, span_conflict_lines
):
    assert binder.already_externally_driven(
        span_conflict_lines, "DZBFASC1", "BEHANDELING"
    )


def test_does_not_match_a_different_business_paragraph(binder):
    lines = [
        "PERFORM OTHER-PARAGRAPH THRU OTHER-PARAGRAPH-EXIT",
        "UNTIL DZBFASC1-EOC.",
    ]
    assert not binder.already_externally_driven(lines, "DZBFASC1", "BEHANDELING")


def test_does_not_match_a_different_cursors_eoc_condition(binder):
    lines = [
        "PERFORM BEHANDELING THRU BEHANDELING-EXIT",
        "UNTIL DZOTHERC1-EOC.",
    ]
    assert not binder.already_externally_driven(lines, "DZBFASC1", "BEHANDELING")


def test_recognises_a_legacy_eoc_condition(binder):
    lines = [
        "PERFORM BEHANDELING THRU BEHANDELING-EXIT",
        "UNTIL SQLCODE = 100.",
    ]
    assert binder.already_externally_driven(lines, "DZBFASC1", "BEHANDELING")


def test_no_span_perform_anywhere_returns_false(binder, inline_control_lines):
    assert not binder.already_externally_driven(
        inline_control_lines, "DZBEFFC1", "HOOFDVERWERKING"
    )


# ---------------------------------------------------------------------
# 2. End-to-end - bind() refuses on a genuine SPAN conflict
# ---------------------------------------------------------------------

def test_bind_refuses_when_business_paragraph_is_already_driven(
    binder, span_conflict_lines
):
    output, business = binder.bind(
        lines=span_conflict_lines,
        cursor="DZBFASC1",
        fetch_paragraph="720-FETCH-DZBFASC1",
        open_paragraph="710-OPEN-DZBFASC1",
    )

    assert business == "BEHANDELING"
    assert output == span_conflict_lines

    # Robust check: the FETCH paragraph's WHEN ZERO branch must still
    # contain a bare CONTINUE, found by scanning its span rather than by
    # a hardcoded line index (which is fragile against fixture edits).
    fetch_start, fetch_end = binder.span_of(output, "720-FETCH-DZBFASC1")
    fetch_body = [binder._body(line) for line in output[fetch_start:fetch_end + 1]]
    assert "CONTINUE" in fetch_body
    
def test_bind_logs_the_refusal_reason(binder, span_conflict_lines):
    binder.bind(
        lines=span_conflict_lines,
        cursor="DZBFASC1",
        fetch_paragraph="720-FETCH-DZBFASC1",
        open_paragraph="710-OPEN-DZBFASC1",
    )

    assert any(
        "already driven by an external SPAN loop" in message
        for message in binder.messages
    )
    assert any("BEHANDELING" in message for message in binder.messages)


def test_bind_never_injects_a_second_fetch_call_path(
    binder, span_conflict_lines
):
    output, _business = binder.bind(
        lines=span_conflict_lines,
        cursor="DZBFASC1",
        fetch_paragraph="720-FETCH-DZBFASC1",
        open_paragraph="710-OPEN-DZBFASC1",
    )

    fetch_start, fetch_end = binder.span_of(output, "720-FETCH-DZBFASC1")
    fetch_body = " ".join(
        binder._body(line) for line in output[fetch_start:fetch_end + 1]
    ).upper()

    assert "PERFORM BEHANDELING" not in fetch_body


# ---------------------------------------------------------------------
# 3. End-to-end - bind() still works for the INLINE idiom (no regression)
# ---------------------------------------------------------------------

def test_bind_still_binds_when_no_span_loop_exists(
    binder, inline_control_lines
):
    output, business = binder.bind(
        lines=inline_control_lines,
        cursor="DZBEFFC1",
        fetch_paragraph="720-FETCH-DZBEFFC1",
        open_paragraph="710-OPEN-DZBEFFC1",
    )

    assert business == "HOOFDVERWERKING"
    assert output != inline_control_lines

    fetch_start, fetch_end = binder.span_of(output, "720-FETCH-DZBEFFC1")
    fetch_body = " ".join(
        binder._body(line) for line in output[fetch_start:fetch_end + 1]
    ).upper()

    assert "PERFORM HOOFDVERWERKING" in fetch_body
    assert any("now performs business paragraph" in m for m in binder.messages)


def test_bind_is_idempotent_on_the_inline_case(binder, inline_control_lines):
    first_pass, business_1 = binder.bind(
        lines=inline_control_lines,
        cursor="DZBEFFC1",
        fetch_paragraph="720-FETCH-DZBEFFC1",
        open_paragraph="710-OPEN-DZBEFFC1",
    )

    binder.messages = []
    second_pass, business_2 = binder.bind(
        lines=first_pass,
        cursor="DZBEFFC1",
        fetch_paragraph="720-FETCH-DZBEFFC1",
        open_paragraph="710-OPEN-DZBEFFC1",
    )

    assert business_1 == business_2 == "HOOFDVERWERKING"
    assert second_pass == first_pass
    assert not any("now performs business paragraph" in m for m in binder.messages)


def test_bind_is_idempotent_on_the_span_conflict_case(
    binder, span_conflict_lines
):
    first_pass, business_1 = binder.bind(
        lines=span_conflict_lines,
        cursor="DZBFASC1",
        fetch_paragraph="720-FETCH-DZBFASC1",
        open_paragraph="710-OPEN-DZBFASC1",
    )

    binder.messages = []
    second_pass, business_2 = binder.bind(
        lines=first_pass,
        cursor="DZBFASC1",
        fetch_paragraph="720-FETCH-DZBFASC1",
        open_paragraph="710-OPEN-DZBFASC1",
    )

    assert business_1 == business_2 == "BEHANDELING"
    assert second_pass == first_pass
    assert any(
        "already driven by an external SPAN loop" in m for m in binder.messages
    )
def test_refuses_when_business_is_driven_and_refetches():
    """The VMDZ7200 shape. Binding here creates a mutual PERFORM."""
    assert FetchBusinessBinder().already_externally_driven(
        _DRIVEN_AND_FETCHES,
        "DZBFASC1",
        "BEHANDELING",
        "720-FETCH-DZBFASC1",
    )


def test_does_not_refuse_when_nothing_refetches():
    """An external driver with no tail fetch still needs the bind.

    Refusing here would trade a recursion for a stall: the flag would
    never flip because no FETCH would ever run.
    """
    assert not FetchBusinessBinder().already_externally_driven(
        _DRIVEN_BUT_NEVER_FETCHES,
        "DZBFASC1",
        "BEHANDELING",
        "720-FETCH-DZBFASC1",
    )
    
if __name__ == "__main__":
    pytest.main([__file__, "-v"])


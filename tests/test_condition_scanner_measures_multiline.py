# LOCATION: tests/test_condition_scanner_measures_multiline.py
# ACTION: REPLACE ENTIRE FILE
"""Condition measurement, and the scope at which it is allowed to decide.

REGRESSION 1 - a dangling boolean operator closed a condition
--------------------------------------------------------------
condition_end_index() inspected only the NEXT line's first word, so

    IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND
    HELP-DA-CPTAFS-479BFAS NOT = '00000000') OR
    (HELP-DA-CRFMAS-479BFAS < DA-ARCH-YMD AND
    HELP-DA-CPTAFS-479BFAS = '00000000')

measured as ONE line. OutputWriteGuard then allowed an extraction that
cut the IF away from its own condition tail:

    IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND
       PERFORM WRITE-FORM-REC
    END-IF.
    ...
    WRITE-FORM-REC.
       HELP-DA-CPTAFS-479BFAS NOT = '00000000') OR

REGRESSION 2 - the guard decided PROGRAM-WIDE
----------------------------------------------
The fix for regression 1 over-corrected. blocks_extraction() refused
every extraction in a program when ANY PROCEDURE DIVISION IF carried a
multi-line condition. VMDZ4420 carried three two-line business status
tests in the same paragraph as its write block; the write block's own
guard, IF WS-STATUS = 'C', is one line and safe to cut. Three of six
programs lost WRITE-<record> and WS-NB-OUTPUT-COUNT.

The decision is now blocks_candidate(), scoped to one candidate.
blocks_extraction() survives as MEASUREMENT only - the tests below name
it that way so the distinction cannot be lost again.
"""

import pytest

from converter.composers.output_write.output_write_guard import (
    OutputWriteGuard,
)
from converter.composers.output_write_paragraph_composer import (
    OutputWriteParagraphComposer,
)
from converter.services.cobol_condition_scanner import (
    CobolConditionScanner,
)

QUOTE = chr(39)
ZERO8 = QUOTE + "00000000" + QUOTE
C_FLAG = QUOTE + "C" + QUOTE
D_FLAG = QUOTE + "D" + QUOTE
Y_FLAG = QUOTE + "Y" + QUOTE


def fixed(seq: str, body: str, right: str) -> str:
    """One 80-column fixed-format record."""
    assert len(body) <= 65
    return seq + " " + body.ljust(65) + right


HEADER = [
    fixed("001750", " PROCEDURE DIVISION.", "01750000"),
    fixed("002290", " BEHANDELING.", "02290000"),
]

FOUR_LINE = [
    fixed("002600", "    IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND", "02600000"),
    fixed("002610", "    HELP-DA-CPTAFS-479BFAS NOT = " + ZERO8 + ") OR", "02610000"),
    fixed("002620", "    (HELP-DA-CRFMAS-479BFAS < DA-ARCH-YMD AND", "02620000"),
    fixed("002630", "    HELP-DA-CPTAFS-479BFAS = " + ZERO8 + ")", "02630000"),
    fixed("002660", "       ADD 1 TO WS-TELLER", "02660000"),
    fixed("002770", "    END-IF.", "02770000"),
]


@pytest.fixture
def scanner():
    return CobolConditionScanner()


# =====================================================================
# REGRESSION 1 - measurement
# =====================================================================
def test_a_four_line_condition_measures_four(scanner):
    lines = HEADER + FOUR_LINE
    if_index = len(HEADER)

    assert scanner.condition_line_count(lines, if_index) == 4


def test_a_line_ending_on_and_never_closes_the_condition(scanner):
    """The defect in one assertion."""
    lines = HEADER + FOUR_LINE
    if_index = len(HEADER)

    assert scanner.condition_end_index(lines, if_index) > if_index


def test_a_single_line_condition_still_measures_one(scanner):
    """The fix must not make every condition look multi-line."""
    lines = HEADER + [
        fixed("002600", "    IF WS-FLAG = " + Y_FLAG, "02600000"),
        fixed("002610", "       ADD 1 TO WS-TELLER", "02610000"),
        fixed("002620", "    END-IF.", "02620000"),
    ]

    assert scanner.condition_line_count(lines, len(HEADER)) == 1


# =====================================================================
# The program-wide methods MEASURE. They never decide.
# =====================================================================
def test_the_guard_measures_a_multi_line_condition():
    """blocks_extraction() reports; it does not refuse.

    Renamed from test_the_guard_refuses_extraction_for_this_program.
    The old name asserted a contract that no longer holds: a multi-line
    condition anywhere in the program no longer blocks extraction. See
    test_an_unrelated_multi_line_condition_does_not_block_a_candidate.
    """
    text = "\n".join(HEADER + FOUR_LINE) + "\n"

    assert OutputWriteGuard().blocks_extraction(text) is True
    assert OutputWriteGuard().widest_condition(text) == 4


def test_the_guard_measures_a_single_line_condition():
    text = "\n".join(
        HEADER
        + [
            fixed("002600", "    IF WS-FLAG = " + Y_FLAG, "02600000"),
            fixed("002610", "       WRITE FORM-REC FROM REC-FORM", "02610000"),
            fixed("002620", "    END-IF.", "02620000"),
        ]
    ) + "\n"

    assert OutputWriteGuard().blocks_extraction(text) is False
    assert OutputWriteGuard().widest_condition(text) == 1


# =====================================================================
# REGRESSION 2 - the decision is PER CANDIDATE
# =====================================================================
UNRELATED_MULTILINE_THEN_SAFE_WRITE = [
    fixed("001750", " PROCEDURE DIVISION.", "01750000"),
    fixed("002290", " VERWERK-VMBEVEF.", "02290000"),
    # Two-line business status test. No WRITE anywhere in it.
    fixed("002300", "    IF CT-RKTEVPR-479EVEF = " + QUOTE + "0060" + QUOTE + " AND", "02300000"),
    fixed("002310", "    WS-STATUS NOT = " + D_FLAG, "02310000"),
    fixed("002320", "       MOVE " + C_FLAG + " TO WS-STATUS", "02320000"),
    fixed("002330", "    END-IF.", "02330000"),
    # The real write block. Its own guard is ONE line and safe to cut.
    fixed("002340", "    IF WS-STATUS = " + C_FLAG, "02340000"),
    fixed("002350", "       INITIALIZE UITRECORD", "02350000"),
    fixed("002360", "       MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE", "02360000"),
    fixed("002370", "       WRITE UITRECORD", "02370000"),
    fixed("002380", "    END-IF.", "02380000"),
    fixed("002390", "710-OPEN-DZBEFFC1.", "02390000"),
    fixed("002400", "    CONTINUE.", "02400000"),
]


def test_an_unrelated_multi_line_condition_does_not_block_a_candidate():
    """The defect that cost three programs their WRITE paragraph.

    A two-line status test sits in the same paragraph as the write
    block. The write block's own guard is one line. The old
    program-wide gate refused the whole program.
    """
    text = "\n".join(UNRELATED_MULTILINE_THEN_SAFE_WRITE) + "\n"

    out = OutputWriteParagraphComposer().compose(text)

    assert "WRITE-UITRECORD." in out
    assert "PERFORM WRITE-UITRECORD" in out
    assert out.count("WRITE UITRECORD") == 1


def test_the_unrelated_condition_is_left_exactly_as_written():
    """Extraction moves lines. It never edits a condition."""
    text = "\n".join(UNRELATED_MULTILINE_THEN_SAFE_WRITE) + "\n"

    out = OutputWriteParagraphComposer().compose(text)
    bodies = [line[7:72].strip() for line in out.splitlines() if len(line) > 7]

    assert "IF CT-RKTEVPR-479EVEF = " + QUOTE + "0060" + QUOTE + " AND" in bodies
    assert "WS-STATUS NOT = " + D_FLAG in bodies


# =====================================================================
# Rule A1 still holds where it actually applies
# =====================================================================
OWN_GUARD_SPANS_LINES = [
    fixed("001750", " PROCEDURE DIVISION.", "01750000"),
    fixed("002290", " BEHANDELING.", "02290000"),
    fixed("002600", "    IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND", "02600000"),
    fixed("002610", "    HELP-DA-CPTAFS-479BFAS NOT = " + ZERO8 + ")", "02610000"),
    fixed("002620", "       INITIALIZE REC-FORM", "02620000"),
    fixed("002630", "       MOVE WS-TELLER TO F-FORM", "02630000"),
    fixed("002640", "       WRITE FORM-REC FROM REC-FORM", "02640000"),
    fixed("002650", "    END-IF.", "02650000"),
    fixed("002660", "710-OPEN-DZBFASC1.", "02660000"),
    fixed("002670", "    CONTINUE.", "02670000"),
]


def test_a_candidate_whose_own_guard_spans_lines_is_still_refused():
    """Narrowing the scope must not weaken rule A1.

    Here the ONLY candidate both contains the WRITE and carries a
    two-line condition. Cutting at if_index + 1 would strand the
    condition tail, so extraction must refuse.
    """
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    composer = OutputWriteParagraphComposer()
    out = composer.compose(text)

    assert "WRITE-FORM-REC." not in out
    assert "PERFORM WRITE-FORM-REC" not in out
    assert out.count("WRITE FORM-REC FROM REC-FORM") == 1


def test_the_refusal_is_reported_with_the_source_paragraph():
    """A refusal with no diagnostic is worse than no guard at all."""
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    composer = OutputWriteParagraphComposer()
    composer.compose(text)

    joined = " ".join(composer.messages)

    assert "BEHANDELING" in joined
    assert "2 lines" in joined or "spans 2" in joined
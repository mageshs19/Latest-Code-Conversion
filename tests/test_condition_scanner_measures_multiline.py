"""Condition measurement, and what the measurement is used for.

REGRESSION 1 - a dangling boolean operator closed a condition
--------------------------------------------------------------
condition_end_index() inspected only the NEXT line's first word, so a
four-line compound condition measured as ONE line. An extraction then
cut the IF away from its own condition tail.

REGRESSION 2 - the guard decided PROGRAM-WIDE
----------------------------------------------
blocks_extraction() refused every extraction in a program when ANY
PROCEDURE DIVISION IF carried a multi-line condition. The decision is
now blocks_candidate(), scoped to one candidate. blocks_extraction()
survives as MEASUREMENT only.

REGRESSION 3 - a multi-line guard was refused instead of positioned
--------------------------------------------------------------------
Scoping the veto to one candidate was still a veto. A write block whose
OWN guard spans lines - the normal shape on a converted program - was
abandoned, so no WRITE-<record> paragraph was built and
WS-NB-OUTPUT-COUNT, which is emitted at the call site that extraction
creates, never came into existence. VMDZ7200 produced one counter where
the manual reference carries two.

The measurement is now the CUT POSITION:

    body_start = condition_end_index(lines, if_index) + 1

Nothing is ever split, so nothing has to be refused. Refusal survives
for the one case that cannot be positioned: a condition whose end
cannot be determined at all.
"""

import pytest

from converter.composers.output_write.output_write_block_finder import (
    CandidateBlock,
)
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


def bodies_of(text: str) -> list[str]:
    return [
        line[7:72].strip()
        for line in text.splitlines()
        if len(line) > 7 and line[7:72].strip()
    ]


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
    lines = HEADER + FOUR_LINE
    if_index = len(HEADER)

    assert scanner.condition_end_index(lines, if_index) > if_index


def test_a_single_line_condition_still_measures_one(scanner):
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
    fixed("002300", "    IF CT-RKTEVPR-479EVEF = " + QUOTE + "0060" + QUOTE + " AND", "02300000"),
    fixed("002310", "    WS-STATUS NOT = " + D_FLAG, "02310000"),
    fixed("002320", "       MOVE " + C_FLAG + " TO WS-STATUS", "02320000"),
    fixed("002330", "    END-IF.", "02330000"),
    fixed("002340", "    IF WS-STATUS = " + C_FLAG, "02340000"),
    fixed("002350", "       INITIALIZE UITRECORD", "02350000"),
    fixed("002360", "       MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE", "02360000"),
    fixed("002370", "       WRITE UITRECORD", "02370000"),
    fixed("002380", "    END-IF.", "02380000"),
    fixed("002390", "710-OPEN-DZBEFFC1.", "02390000"),
    fixed("002400", "    CONTINUE.", "02400000"),
]


def test_an_unrelated_multi_line_condition_does_not_block_a_candidate():
    text = "\n".join(UNRELATED_MULTILINE_THEN_SAFE_WRITE) + "\n"

    out = OutputWriteParagraphComposer().compose(text)

    assert "WRITE-UITRECORD." in out
    assert "PERFORM WRITE-UITRECORD" in out
    assert out.count("WRITE UITRECORD") == 1


def test_the_unrelated_condition_is_left_exactly_as_written():
    text = "\n".join(UNRELATED_MULTILINE_THEN_SAFE_WRITE) + "\n"

    out = OutputWriteParagraphComposer().compose(text)
    bodies = bodies_of(out)

    assert "IF CT-RKTEVPR-479EVEF = " + QUOTE + "0060" + QUOTE + " AND" in bodies
    assert "WS-STATUS NOT = " + D_FLAG in bodies


# =====================================================================
# REGRESSION 3 - a multi-line guard is POSITIONED, not refused
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

CONDITION_LINES = (
    "IF (HELP-DA-CPTAFS-479BFAS < DA-ARCH-YMD  AND",
    "HELP-DA-CPTAFS-479BFAS NOT = " + ZERO8 + ")",
)


def test_a_candidate_whose_own_guard_spans_lines_is_now_extracted():
    """The cut moved past the condition, so nothing has to be refused."""
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    out = OutputWriteParagraphComposer().compose(text)

    assert "WRITE-FORM-REC." in out
    assert "PERFORM WRITE-FORM-REC" in out
    assert out.count("WRITE FORM-REC FROM REC-FORM") == 1


def test_every_condition_line_stays_at_the_call_site():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"
    bodies = bodies_of(OutputWriteParagraphComposer().compose(text))

    call = bodies.index("PERFORM WRITE-FORM-REC")
    paragraph = bodies.index("WRITE-FORM-REC.")

    for fragment in CONDITION_LINES:
        position = bodies.index(fragment)
        assert position < call, fragment
        assert position < paragraph, fragment


def test_the_extracted_body_starts_after_the_condition():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"
    bodies = bodies_of(OutputWriteParagraphComposer().compose(text))

    paragraph = bodies.index("WRITE-FORM-REC.")

    assert bodies[paragraph + 1] == "INITIALIZE REC-FORM"


def test_no_dangling_boolean_operator_survives():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    for body in bodies_of(OutputWriteParagraphComposer().compose(text)):
        assert not body.upper().startswith("AND ")
        assert not body.upper().startswith("OR ")


def test_the_counter_increment_lands_at_the_call_site():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"
    bodies = bodies_of(OutputWriteParagraphComposer().compose(text))

    call = bodies.index("PERFORM WRITE-FORM-REC")
    counter = bodies.index("ADD 1 TO WS-NB-OUTPUT-COUNT")
    paragraph = bodies.index("WRITE-FORM-REC.")

    assert call < counter < paragraph


def test_the_extraction_is_reported_with_the_source_paragraph():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    composer = OutputWriteParagraphComposer()
    composer.compose(text)
    joined = " ".join(composer.messages)

    assert "BEHANDELING" in joined
    assert "WRITE-FORM-REC" in joined


def test_extraction_is_idempotent():
    text = "\n".join(OWN_GUARD_SPANS_LINES) + "\n"

    once = OutputWriteParagraphComposer().compose(text)
    twice = OutputWriteParagraphComposer().compose(once)

    assert once == twice


# =====================================================================
# Refusal survives for the one case that cannot be positioned
# =====================================================================
def _unresolvable_program() -> list[str]:
    """A condition longer than CONDITION_SCAN_LIMIT never resolves."""
    lines = [
        fixed("001750", " PROCEDURE DIVISION.", "01750000"),
        fixed("002290", " BEHANDELING.", "02290000"),
        fixed("002300", "    IF WS-A = " + Y_FLAG + " AND", "02300000"),
    ]
    for step in range(30):
        lines.append(
            fixed(
                "0024{0:02d}".format(step),
                "    WS-B = " + Y_FLAG + " AND",
                "0024{0:02d}00".format(step),
            )
        )
    lines.append(fixed("002500", "       INITIALIZE REC-FORM", "02500000"))
    lines.append(
        fixed("002510", "       WRITE FORM-REC FROM REC-FORM", "02510000")
    )
    lines.append(fixed("002520", "    END-IF.", "02520000"))
    return lines


def test_an_unresolvable_condition_is_still_refused():
    text = "\n".join(_unresolvable_program()) + "\n"

    composer = OutputWriteParagraphComposer()
    out = composer.compose(text)

    assert "WRITE-FORM-REC." not in out
    assert out.count("WRITE FORM-REC FROM REC-FORM") == 1


def test_the_refusal_is_reported_with_the_source_paragraph():
    """A refusal with no diagnostic is worse than no guard at all."""
    text = "\n".join(_unresolvable_program()) + "\n"

    composer = OutputWriteParagraphComposer()
    composer.compose(text)
    joined = " ".join(composer.messages)

    assert "BEHANDELING" in joined
    assert "could not be resolved" in joined


def test_an_unresolved_block_falls_back_to_the_safe_body_start():
    """body_start must never be nonsense when the condition is unknown."""
    block = CandidateBlock(if_index=5, end_index=12, condition_end=-1)

    assert block.has_resolved_condition is False
    assert block.body_start == 6
    assert block.condition_line_count == 0


def test_a_resolved_block_cuts_after_the_condition():
    block = CandidateBlock(if_index=5, end_index=12, condition_end=8)

    assert block.has_resolved_condition is True
    assert block.body_start == 9
    assert block.condition_line_count == 4
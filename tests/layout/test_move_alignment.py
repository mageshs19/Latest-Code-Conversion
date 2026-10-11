# LOCATION: tests/layout/test_move_alignment.py
# ACTION: CREATE NEW FILE
r"""Contract tests for MoveAlignmentComposer.

Three properties matter more than the cosmetics:

  SAFETY       no data-name is ever truncated or lost
  IDEMPOTENCE  running the pass twice equals running it once
  SCOPE        EXEC SQL bodies and literals are never touched

The alignment itself is checked by comparing TO columns, never by
asserting exact strings - an exact-string test would have to be rewritten
every time a width constant moves.
"""

from __future__ import annotations

from converter.composers.move_alignment_composer import (
    MoveAlignmentComposer,
)

SEQ = "010230"
RIGHT = "03170000"
BODY_WIDTH = 65


#
# Fixed-format helpers
#
def _fixed(body: str, seq: str = SEQ, right: str = RIGHT) -> str:
    """One 80-column record: 6 sequence, 1 indicator, 65 body, 8 right.

    A fixture body longer than 65 columns cannot exist in fixed-format
    COBOL. Silently truncating it produced a test that blamed the
    composer for damage the helper had already done, so the helper now
    refuses instead.
    """
    assert len(body) <= BODY_WIDTH, (
        f"test fixture body is {len(body)} columns, limit is {BODY_WIDTH}:\n"
        f"  {body!r}\n"
        f"Shorten the fixture - do not widen the helper."
    )
    return f"{seq} {body.ljust(BODY_WIDTH)}{right}"


def _marked(mark: str, body: str = "", seq: str = SEQ, right: str = RIGHT) -> str:
    """A record carrying `mark` in the indicator column (7)."""
    assert len(body) <= BODY_WIDTH, (
        f"test fixture body is {len(body)} columns, limit is {BODY_WIDTH}."
    )
    return f"{seq}{mark}{body.ljust(BODY_WIDTH)}{right}"


def _bodies(text: str) -> list[str]:
    return [line[7:72].rstrip() for line in text.rstrip("\n").split("\n")]


def _mask(body: str) -> str:
    """Blank the inside of quoted literals, preserving length.

    A literal may legally contain the word TO. The column helper must
    not find it there, or every assertion below measures the wrong gap.
    """
    out: list[str] = []
    quote = ""

    for character in body:
        if quote:
            out.append(character if character == quote else ".")
            if character == quote:
                quote = ""
            continue
        if character in ("'", '"'):
            quote = character
        out.append(character)

    return "".join(out)


def _to_column(body: str) -> int:
    """Column of the TO keyword, ignoring any TO inside a literal."""
    return _mask(body).index(" TO ") + 1


def _words(text: str) -> list[str]:
    """Every token in document order, whitespace discarded."""
    return [word for body in _bodies(text) for word in body.split()]


def _compose(lines: list[str]) -> tuple[list[str], MoveAlignmentComposer]:
    composer = MoveAlignmentComposer()
    return _bodies(composer.compose("\n".join(lines))), composer


#
# Alignment
#
def test_a_run_shares_one_to_column():
    out, _ = _compose([
        _fixed("     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
        _fixed("     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID"),
    ])

    assert len({_to_column(body) for body in out}) == 1


def test_the_to_column_clears_the_longest_source():
    out, _ = _compose([
        _fixed("     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
    ])

    longest = max(len(body.split(" TO ")[0].rstrip()) for body in out)

    assert _to_column(out[0]) > longest


def test_a_split_move_is_joined_then_aligned():
    out, composer = _compose([
        _fixed("     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO"),
        _fixed("     UIT-AM-CN-STOCK"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
    ])

    assert len(out) == 2
    assert "UIT-AM-CN-STOCK" in out[0]
    assert len({_to_column(body) for body in out}) == 1
    assert any("joined" in message.lower() for message in composer.messages)


#
# Run formation
#
def test_a_blank_line_starts_a_new_column():
    out, _ = _compose([
        _fixed("     MOVE A-LONG-SOURCE-NAME TO T1"),
        _fixed("     MOVE B TO T2"),
        _fixed(""),
        _fixed("     MOVE C TO T3"),
        _fixed("     MOVE D TO T4"),
    ])

    assert _to_column(out[0]) == _to_column(out[1])
    assert _to_column(out[3]) == _to_column(out[4])
    assert _to_column(out[0]) != _to_column(out[3])


def test_when_clauses_do_not_break_the_run():
    """WHEN sits at a lesser indent, so the table spans it."""
    out, _ = _compose([
        _fixed("      WHEN DA-DD-MM-CCYY = '01.01.0001'"),
        _fixed("           MOVE ZEROES TO DA-CCYYMMDD-R"),
        _fixed("      WHEN OTHER"),
        _fixed("           MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R"),
    ])

    assert _to_column(out[1]) == _to_column(out[3])


def test_a_statement_at_the_same_indent_breaks_the_run():
    out, _ = _compose([
        _fixed("     MOVE A TO T1"),
        _fixed("     PERFORM SOME-PARAGRAPH"),
        _fixed("     MOVE A-LONG-SOURCE-NAME TO T2"),
        _fixed("     MOVE B TO T3"),
    ])

    assert out[1].strip() == "PERFORM SOME-PARAGRAPH"
    assert _to_column(out[2]) == _to_column(out[3])
    assert _to_column(out[0]) != _to_column(out[2])


def test_a_different_indent_starts_a_new_run():
    out, _ = _compose([
        _fixed("     MOVE A-LONG-SOURCE-NAME TO T1"),
        _fixed("     MOVE B TO T2"),
        _fixed("           MOVE C TO T3"),
        _fixed("           MOVE D TO T4"),
    ])

    assert _to_column(out[0]) == _to_column(out[1])
    assert _to_column(out[2]) == _to_column(out[3])
    assert _to_column(out[0]) != _to_column(out[2])


def test_a_single_move_is_left_alone():
    out, _ = _compose([
        _fixed("     MOVE A TO B"),
        _fixed("     PERFORM SOME-PARAGRAPH"),
    ])

    assert out[0].strip() == "MOVE A TO B"


def test_a_comment_inside_a_run_survives_verbatim():
    out, _ = _compose([
        _fixed("     MOVE A-LONG-SOURCE-NAME TO T1"),
        _marked("*", " a note from the author"),
        _fixed("     MOVE B TO T2"),
    ])

    assert out[1].strip() == "a note from the author"
    assert _to_column(out[0]) == _to_column(out[2])


#
# Multi-receiver
#
def test_a_multi_receiver_move_stands_alone():
    out, _ = _compose([
        _fixed("     MOVE ZEROES TO DA-CCYYMMDD"),
        _fixed("     HELP-DA-CREVTPD-479EVEF"),
        _fixed("     MOVE DA-CREVTPD-479EVEF OF DCLDZEVEFTV TO DA-DD-MM-CCYY"),
    ])

    assert "DA-CCYYMMDD" in out[0]
    assert out[1].strip() == "HELP-DA-CREVTPD-479EVEF"
    assert out[1].index("HELP") > out[0].index(" TO ")


def test_a_continuation_receiver_sits_under_the_first():
    out, _ = _compose([
        _fixed("     MOVE ZEROES TO DA-CCYYMMDD"),
        _fixed("     HELP-DA-CREVTPD-479EVEF"),
    ])

    first_receiver = out[0].index(" TO ") + len(" TO ")
    continuation = len(out[1]) - len(out[1].lstrip())

    assert continuation == first_receiver


#
# Literals
#
def test_a_literal_containing_to_is_not_split_on():
    out, _ = _compose([
        _fixed("     MOVE 'MOVE TO HERE' TO WS-TEXT"),
        _fixed("     MOVE WS-A TO WS-B"),
    ])

    assert "'MOVE TO HERE'" in out[0]
    assert out[0].rstrip().endswith("WS-TEXT")
    assert _to_column(out[0]) == _to_column(out[1])


def test_a_quoted_date_literal_is_preserved():
    out, _ = _compose([
        _fixed("     MOVE '99999999' TO DA-CCYYMMDD-R"),
        _fixed("     MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R"),
    ])

    assert "'99999999'" in out[0]
    assert _to_column(out[0]) == _to_column(out[1])


#
# Scope
#
def test_sql_bodies_are_never_touched():
    """Synthetic: SQL has no MOVE, but the guard must hold regardless."""
    lines = [
        _fixed("     EXEC SQL"),
        _fixed("       MOVE A TO B"),
        _fixed("       MOVE A-MUCH-LONGER-SOURCE TO C"),
        _fixed("     END-EXEC"),
    ]

    out, _ = _compose(lines)

    assert out == _bodies("\n".join(lines))


def test_a_fetch_block_is_returned_unchanged():
    lines = [
        _fixed("     EXEC SQL"),
        _fixed("       FETCH DZBEFFC1"),
        _fixed("        INTO :DCLDZBEFFTV.AM-CNDSTK-479BEFF"),
        _fixed("           , :DCLDZBEFFTV.AM-CNSTK-479BEFF"),
        _fixed("     END-EXEC"),
    ]

    out, _ = _compose(lines)

    assert out == _bodies("\n".join(lines))


#
# Safety
#
def test_an_over_wide_run_is_refused_not_truncated():
    """A short source with a long target, pulled right by a long neighbour.

    Both lines fit unaligned. Aligning pushes the first past column 72,
    so the whole run must fall back rather than truncate a data-name.

        prefix1 = 25, prefix2 = 45  ->  to_col = 46
        aligned1 = 46 + len('TO A-LONG-TARGET-NAME') = 67  > 65
    """
    short_source = "WS-SOURCE-SHORT"                    # 15
    long_target = "A-LONG-TARGET-NAME"                  # 18
    long_source = "A-REALLY-LONG-SOURCE-NAME-FOR-TESTS"  # 35

    out, composer = _compose([
        _fixed(f"     MOVE {short_source} TO {long_target}"),
        _fixed(f"     MOVE {long_source} TO T2"),
    ])

    joined = " ".join(out)

    assert short_source in joined
    assert long_target in joined
    assert long_source in joined
    assert any("does not fit" in message for message in composer.messages)

def test_excessive_padding_is_refused():
    out, composer = _compose([
        _fixed("     MOVE A TO T1"),
        _fixed("     MOVE A-SOURCE-NAME-THAT-IS-VERY-LONG-INDEED TO T2"),
    ])

    assert _to_column(out[0]) != _to_column(out[1])
    assert any("filler blanks" in message for message in composer.messages)

def test_a_refused_run_with_an_interior_line_does_not_crash():
    """Heterogeneous AND refused - the combination that silently
    disabled the whole pass for a session.

    The interior line sits at a DIFFERENT indent on purpose. At the
    SAME indent it would break the run (see
    test_a_statement_at_the_same_indent_breaks_the_run) and the run
    would never become heterogeneous - which is how the first version
    of this test passed through the defect it was written to catch.

    The two sources are the pair from test_excessive_padding_is_refused,
    so the refusal is guaranteed and this test adds exactly one
    variable: the interior Passthrough.
    """
    out, composer = _compose([
        _fixed("     MOVE A TO T1"),
        _fixed("   WHEN OTHER"),
        _fixed("     MOVE A-SOURCE-NAME-THAT-IS-VERY-LONG-INDEED TO T2"),
    ])

    assert any("WHEN OTHER" in body for body in out)
    assert any("filler blanks" in message for message in composer.messages)
    assert not any("[error]" in message for message in composer.messages)
    
def test_the_sentence_terminator_survives():
    out, _ = _compose([
        _fixed("     MOVE A-LONGER-SOURCE-NAME TO B"),
        _fixed("     MOVE C TO D."),
    ])

    assert out[1].rstrip().endswith("D.")
    assert _to_column(out[0]) == _to_column(out[1])


def test_no_token_is_lost_or_invented():
    lines = [
        _fixed("     INITIALIZE UITRECORD"),
        _fixed("     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO"),
        _fixed("     UIT-AM-CN-STOCK"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
        _fixed("     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID"),
        _fixed("     WRITE UITRECORD."),
    ]

    source = "\n".join(lines)
    result = MoveAlignmentComposer().compose(source)

    assert _words(result) == _words(source)


def test_internal_spacing_inside_a_source_is_preserved():
    """'MM   OF X' is the author's column alignment. Keep it."""
    out, _ = _compose([
        _fixed("           MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R"),
        _fixed("           MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R"),
    ])

    assert "MM   OF DA-DD-MM-CCYY" in out[0]
    assert "DD   OF DA-DD-MM-CCYY" in out[1]


#
# Idempotence
#
def test_running_the_pass_twice_equals_running_it_once():
    source = "\n".join([
        _fixed("     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO"),
        _fixed("     UIT-AM-CN-STOCK"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
        _fixed("     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID"),
        _fixed(""),
        _fixed("     MOVE ZEROES TO DA-CCYYMMDD"),
        _fixed("     MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY"),
    ])

    once = MoveAlignmentComposer().compose(source)
    twice = MoveAlignmentComposer().compose(once)

    assert twice == once


def test_an_already_aligned_run_reports_no_join():
    source = "\n".join([
        _fixed("     MOVE A-LONG-SOURCE-NAME   TO T1"),
        _fixed("     MOVE B                    TO T2"),
    ])

    composer = MoveAlignmentComposer()
    composer.compose(source)

    assert not any("joined" in message.lower() for message in composer.messages)


#
# Fixed-format integrity
#
def test_every_emitted_line_is_eighty_columns():
    result = MoveAlignmentComposer().compose("\n".join([
        _fixed("     MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO"),
        _fixed("     UIT-AM-CN-STOCK"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
    ]))

    for line in result.rstrip("\n").split("\n"):
        assert len(line) == 80


def test_no_body_reaches_column_seventy_three():
    result = MoveAlignmentComposer().compose("\n".join([
        _fixed("     MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID"),
        _fixed("     MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
    ]))

    for body in _bodies(result):
        assert len(body) <= BODY_WIDTH


def test_the_right_sequence_area_is_preserved():
    result = MoveAlignmentComposer().compose("\n".join([
        _fixed("     MOVE A-LONG-SOURCE-NAME TO T1"),
        _fixed("     MOVE B TO T2"),
    ]))

    for line in result.rstrip("\n").split("\n"):
        assert line[72:80] == RIGHT


#
# Degenerate input
#
def test_empty_input_is_returned_unchanged():
    assert MoveAlignmentComposer().compose("") == ""


def test_a_document_with_no_moves_is_untouched():
    lines = [
        _fixed("     PERFORM 710-OPEN-DZBEFFC1."),
        _fixed("     PERFORM 720-FETCH-DZBEFFC1 UNTIL DZBEFFC1-EOC."),
        _fixed("     PERFORM 730-CLOSE-DZBEFFC1."),
    ]

    out, composer = _compose(lines)

    assert out == _bodies("\n".join(lines))
    assert composer.messages == []
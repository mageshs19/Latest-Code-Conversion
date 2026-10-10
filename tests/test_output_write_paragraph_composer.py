# LOCATION: tests/test_output_write_paragraph_composer.py
# ACTION: CREATE NEW FILE

"""Output write paragraph extraction tests."""

from converter.composers.output_write_paragraph_composer import (
    OutputWriteParagraphComposer,
)


def _fixed(body: str, seq: str = "001000", right: str = "01000000") -> str:
    """One 80-column fixed-format line."""
    return f"{seq} {body[:65].ljust(65)}{right}"


def _program() -> str:
    return "\n".join([
        _fixed("PROCEDURE DIVISION."),
        _fixed("HOOFDVERWERKING."),
        _fixed("    PERFORM 830-CLOSE-DZEVEFC1"),
        _fixed("    IF NOT SW-STATUS-D = 'Y'"),
        _fixed("       IF WS-STATUS = 'C'"),
        _fixed("          INITIALIZE UITRECORD"),
        _fixed("          MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE"),
        _fixed("          WRITE UITRECORD"),
        _fixed("       END-IF"),
        _fixed("    END-IF."),
        _fixed("710-OPEN-DZBEFFC1."),
        _fixed("    CONTINUE."),
    ])


def test_write_block_is_extracted_into_its_own_paragraph():
    out = OutputWriteParagraphComposer().compose(_program())

    assert "WRITE-UITRECORD." in out
    assert "PERFORM WRITE-UITRECORD" in out
    assert out.count("WRITE UITRECORD") == 1


def test_population_statements_move_into_the_new_paragraph():
    out = OutputWriteParagraphComposer().compose(_program())
    tail = out.split("WRITE-UITRECORD.", 1)[1]

    assert "INITIALIZE UITRECORD" in tail
    assert "MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE" in tail


def test_counter_increment_is_added_at_the_call_site():
    out = OutputWriteParagraphComposer().compose(_program())
    call_site = out.split("WRITE-UITRECORD.", 1)[0]

    assert "ADD 1 TO WS-NB-OUTPUT-COUNT" in call_site


def test_guard_conditions_are_left_untouched():
    out = OutputWriteParagraphComposer().compose(_program())

    assert "IF NOT SW-STATUS-D = 'Y'" in out
    assert "IF WS-STATUS = 'C'" in out


def test_every_line_stays_eighty_columns():
    out = OutputWriteParagraphComposer().compose(_program())

    for line in out.splitlines():
        if line.strip():
            assert len(line) == 80, repr(line)


def test_diagnostics_report_the_extraction():
    composer = OutputWriteParagraphComposer()
    composer.compose(_program())
    joined = " ".join(composer.messages)

    assert "extracted record population" in joined
    assert "WRITE-UITRECORD" in joined


def test_two_writes_are_left_alone():
    text = _program().replace(
        _fixed("          WRITE UITRECORD"),
        _fixed("          WRITE UITRECORD")
        + "\n"
        + _fixed("          WRITE UITRECORD"),
    )
    out = OutputWriteParagraphComposer().compose(text)

    assert "PERFORM WRITE-UITRECORD" not in out


def test_extraction_is_idempotent():
    composer = OutputWriteParagraphComposer()
    once = composer.compose(_program())
    twice = composer.compose(once)

    assert once == twice


def test_program_without_a_write_is_unchanged():
    text = "\n".join([
        _fixed("PROCEDURE DIVISION."),
        _fixed("HOOFDVERWERKING."),
        _fixed("    IF WS-STATUS = 'C'"),
        _fixed("       MOVE 'X' TO WS-STATUS"),
        _fixed("    END-IF."),
    ])
    out = OutputWriteParagraphComposer().compose(text)

    assert "PERFORM WRITE-" not in out

# LOCATION: tests/test_output_write_paragraph_composer.py
# ACTION: ADD
#
# REGRESSION - the OUTER guard was extracted, so the inner write
# decision moved into WRITE-UITRECORD and the call-site counter
# incremented on every attempt instead of every write.

def test_every_guard_stays_at_the_call_site():
    out = OutputWriteParagraphComposer().compose(_program())

    call_site, _, tail = out.partition("WRITE-UITRECORD.")

    # Both guards belong to the caller.
    assert "IF NOT SW-STATUS-D = 'Y'" in call_site
    assert "IF WS-STATUS = 'C'" in call_site

    # The extracted paragraph is pure population - no decision in it.
    assert "IF WS-STATUS = 'C'" not in tail
    assert "IF NOT SW-STATUS-D = 'Y'" not in tail


def test_the_counter_is_guarded_by_the_write_decision():
    """ADD 1 must sit INSIDE the condition that decides the write."""
    out = OutputWriteParagraphComposer().compose(_program())
    bodies = [line[7:72].strip() for line in out.splitlines() if len(line) > 7]

    guard = bodies.index("IF WS-STATUS = 'C'")
    counter = bodies.index("ADD 1 TO WS-NB-OUTPUT-COUNT")
    closer = bodies.index("END-IF", guard)

    assert guard < counter < closer
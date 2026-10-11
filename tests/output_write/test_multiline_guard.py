from __future__ import annotations


def test_a_single_line_guard_still_extracts(
    program, compose, bodies, index_of, single_line_guard
):
    out, _messages = compose(program(single_line_guard))
    text = bodies(out)

    assert index_of(text, "WRITE-UITRECORD.") >= 0
    assert index_of(text, "PERFORM WRITE-UITRECORD") >= 0


def test_a_four_line_guard_now_extracts(
    program, compose, bodies, index_of, four_line_guard
):
    out, _messages = compose(program(four_line_guard))
    text = bodies(out)

    assert index_of(text, "WRITE-REC-FORM.") >= 0
    assert index_of(text, "PERFORM WRITE-REC-FORM") >= 0


def test_the_whole_condition_stays_at_the_call_site(
    program, compose, bodies, index_of, four_line_guard
):
    out, _messages = compose(program(four_line_guard))
    text = bodies(out)

    call = index_of(text, "PERFORM WRITE-REC-FORM")
    paragraph = index_of(text, "WRITE-REC-FORM.")

    for fragment in (
        "IF (HELP-DA-A",
        "HELP-DA-A NOT = '00000000') OR",
        "(HELP-DA-B",
        "HELP-DA-A = '00000000')",
    ):
        position = index_of(text, fragment)
        assert position >= 0, fragment
        assert position < call, fragment
        assert position < paragraph, fragment


def test_the_extracted_body_starts_after_the_condition(
    program, compose, bodies, index_of, four_line_guard
):
    out, _messages = compose(program(four_line_guard))
    text = bodies(out)

    paragraph = index_of(text, "WRITE-REC-FORM.")
    assert text[paragraph + 1].upper().startswith("INITIALIZE REC-FORM")


def test_no_dangling_boolean_operator_survives(
    program, compose, bodies, four_line_guard
):
    out, _messages = compose(program(four_line_guard))

    for body in bodies(out):
        assert not body.upper().startswith("AND ")
        assert not body.upper().startswith("OR ")


def test_the_counter_increment_lands_at_the_call_site(
    program, compose, bodies, index_of, four_line_guard
):
    out, _messages = compose(program(four_line_guard))
    text = bodies(out)

    counter = index_of(text, "ADD 1 TO WS-NB-OUTPUT-COUNT")
    paragraph = index_of(text, "WRITE-REC-FORM.")

    assert counter >= 0
    assert counter < paragraph


def test_the_counter_is_reported(program, compose, four_line_guard):
    _out, messages = compose(program(four_line_guard))
    assert any("WS-NB-OUTPUT-COUNT" in message for message in messages)


def test_two_writes_are_refused(program, compose, bodies, index_of, two_writes):
    out, messages = compose(program(two_writes))

    assert index_of(bodies(out), "WRITE-UITRECORD.") < 0
    assert any("WRITE statements" in message for message in messages)


def test_extraction_is_idempotent(program, compose, four_line_guard):
    once, _messages = compose(program(four_line_guard))
    twice, _again = compose(once)
    assert once == twice
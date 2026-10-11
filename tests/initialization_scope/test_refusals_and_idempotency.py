from __future__ import annotations


def test_a_program_with_no_dclgen_group_is_untouched(program, run):
    source = program(
        [
            "PROCEDURE DIVISION.",
            "DISPLAY 'NOTHING TO DO'",
            "STOP RUN.",
        ]
    )
    result, messages = run(source)

    assert result == source
    assert messages


def test_a_program_with_no_procedure_division_is_untouched(program, run):
    source = program(
        [
            "WORKING-STORAGE SECTION.",
            "EXEC SQL INCLUDE DCLAAATV END-EXEC.",
        ]
    )
    result, messages = run(source)

    assert result == source
    assert messages


def test_a_program_with_no_cursor_open_is_untouched(program, run):
    source = program(
        [
            "WORKING-STORAGE SECTION.",
            "EXEC SQL INCLUDE DCLAAATV END-EXEC.",
            "PROCEDURE DIVISION.",
            "MOVE SPACE TO WS-STATUS",
            "STOP RUN.",
        ]
    )
    result, messages = run(source)

    assert result == source
    assert messages


def test_an_unresolvable_group_rolls_the_pass_back(program, run):
    source = program(
        [
            "WORKING-STORAGE SECTION.",
            "EXEC SQL INCLUDE DCLAAATV END-EXEC.",
            "PROCEDURE DIVISION.",
            "PERFORM 710-OPEN-AAAC1",
            "STOP RUN.",
        ]
    )
    result, messages = run(source)

    assert result == source
    assert any("rolled back" in message.lower() for message in messages)


def test_the_pass_is_idempotent(program, run, parent_child_lines):
    source = program(parent_child_lines)
    first, _messages = run(source)
    second, _again = run(first)

    assert first == second


def test_a_second_run_adds_no_duplicate_initialize(
    program, run, bodies, count_of, parent_child_lines
):
    first, _messages = run(program(parent_child_lines))
    second, _again = run(first)
    items = bodies(second)

    assert count_of(items, "INITIALIZE DCLAAATV") == 1
    assert count_of(items, "INITIALIZE DCLBBBTV") == 1


def test_every_run_reports_something(program, run, single_cursor_lines):
    _result, messages = run(program(single_cursor_lines))
    assert messages


def test_empty_input_is_safe(run):
    assert run("") == ("", [])


def test_whitespace_input_is_safe(run):
    result, messages = run("   \n  \n")
    assert result.strip() == ""
    assert messages == []
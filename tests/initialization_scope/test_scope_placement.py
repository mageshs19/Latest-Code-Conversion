from __future__ import annotations


def _placed_before(items: list[str], open_prefix: str) -> str:
    for position, body in enumerate(items):
        if body.upper().startswith(open_prefix.upper()):
            return items[position - 1].upper() if position else ""
    return ""


def test_single_cursor_is_initialized_before_its_open(
    program, run, bodies, single_cursor_lines
):
    result, _messages = run(program(single_cursor_lines))
    items = bodies(result)

    assert _placed_before(items, "PERFORM 710-OPEN-AAAC1").startswith(
        "INITIALIZE DCLAAATV"
    )


def test_parent_and_child_are_each_initialized(
    program, run, bodies, parent_child_lines
):
    result, _messages = run(program(parent_child_lines))
    items = bodies(result)

    assert _placed_before(items, "PERFORM 710-OPEN-AAAC1").startswith(
        "INITIALIZE DCLAAATV"
    )
    assert _placed_before(items, "PERFORM 810-OPEN-BBBC1").startswith(
        "INITIALIZE DCLBBBTV"
    )


def test_the_child_initialize_sits_inside_the_business_paragraph(
    program, run, bodies, index_of, parent_child_lines
):
    result, _messages = run(program(parent_child_lines))
    items = bodies(result)

    header = index_of(items, "ROW-WORK.")
    child = index_of(items, "INITIALIZE DCLBBBTV")

    assert header >= 0
    assert child > header


def test_the_parent_initialize_sits_in_the_mainline(
    program, run, bodies, index_of, parent_child_lines
):
    result, _messages = run(program(parent_child_lines))
    items = bodies(result)

    division = index_of(items, "PROCEDURE DIVISION")
    parent = index_of(items, "INITIALIZE DCLAAATV")
    stop = index_of(items, "STOP RUN")

    assert division < parent < stop


def test_three_nesting_levels_are_all_scoped(
    program, run, bodies, three_level_lines
):
    result, _messages = run(program(three_level_lines))
    items = bodies(result)

    for open_prefix, group in (
        ("PERFORM 710-OPEN-AAAC1", "INITIALIZE DCLAAATV"),
        ("PERFORM 810-OPEN-BBBC1", "INITIALIZE DCLBBBTV"),
        ("PERFORM 910-OPEN-CCCC1", "INITIALIZE DCLCCCTV"),
    ):
        assert _placed_before(items, open_prefix).startswith(group)


def test_each_group_is_initialized_exactly_once(
    program, run, bodies, count_of, three_level_lines
):
    result, _messages = run(program(three_level_lines))
    items = bodies(result)

    assert count_of(items, "INITIALIZE DCLAAATV") == 1
    assert count_of(items, "INITIALIZE DCLBBBTV") == 1
    assert count_of(items, "INITIALIZE DCLCCCTV") == 1


def test_the_legacy_startup_paragraph_is_removed(
    program, run, bodies, count_of, legacy_startup_lines
):
    result, _messages = run(program(legacy_startup_lines))
    items = bodies(result)

    assert count_of(items, "100-INITIALIZE.") == 0
    assert count_of(items, "PERFORM 100-INITIALIZE") == 0


def test_salvaged_statements_are_not_duplicated(
    program, run, bodies, count_of, legacy_startup_lines
):
    result, _messages = run(program(legacy_startup_lines))
    items = bodies(result)

    assert count_of(items, "MOVE CS-PROGRAM") == 1
    assert count_of(items, "PERFORM 600-GET-TIMESTAMP") == 1


def test_legacy_program_is_rescoped_not_just_stripped(
    program, run, bodies, legacy_startup_lines
):
    result, _messages = run(program(legacy_startup_lines))
    items = bodies(result)

    assert _placed_before(items, "PERFORM 710-OPEN-AAAC1").startswith(
        "INITIALIZE DCLAAATV"
    )
    assert _placed_before(items, "PERFORM 810-OPEN-BBBC1").startswith(
        "INITIALIZE DCLBBBTV"
    )


def test_cursor_names_are_never_assumed(
    program, run, bodies, three_level_lines
):
    result, _messages = run(program(three_level_lines))
    text = result.upper()

    assert "DZBEFF" not in text
    assert "DZEVEF" not in text
    assert "VMDZ" not in text
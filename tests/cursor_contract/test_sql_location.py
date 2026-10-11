from __future__ import annotations

import pytest


def test_entry_point_sql_location_is_emitted_before_the_sql(
    fetch, sql_moves
):
    lines = fetch()
    moves = sql_moves(lines)

    assert moves
    assert lines.index(moves[0]) < lines.index("EXEC SQL")


def test_sql_location_is_set_exactly_once(fetch, sql_moves):
    assert len(sql_moves(fetch())) == 1


@pytest.mark.parametrize(
    "shape, key",
    [
        ("open_paragraph", "open_paragraph"),
        ("close_paragraph", "close_paragraph"),
    ],
)
def test_error_branch_does_not_restate_sql_location(
    cursor_paragraph, names, sql_moves, when_other, shape, key
):
    lines = cursor_paragraph(shape, names[key])

    assert len(sql_moves(lines)) == 1
    assert not any(
        body.endswith(names["suffix"]) for body in when_other(lines)
    )


def test_fetch_error_branch_does_not_restate_sql_location(
    fetch, names, when_other
):
    branch = when_other(fetch())

    assert branch
    assert not any(body.endswith(names["suffix"]) for body in branch)


def test_error_branch_reports_and_routes(fetch, names, when_other):
    branch = when_other(fetch())

    assert any(body.startswith("DISPLAY 'ERROR WHILE") for body in branch)
    assert f"PERFORM {names['sql_error']}" in branch
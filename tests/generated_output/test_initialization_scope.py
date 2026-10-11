from __future__ import annotations

import re

OPEN_PERFORM = re.compile(
    r"^PERFORM\s+\d{3,6}-OPEN-[A-Z0-9-]+\.?$",
    re.IGNORECASE,
)
FETCH_HEADER = re.compile(
    r"^\d{3,6}-FETCH-[A-Z0-9-]+\.$",
    re.IGNORECASE,
)
INITIALIZE_GROUP = "INITIALIZE DCL"
STARTUP_PARAGRAPH = "100-INITIALIZE"
TIMESTAMP_PERFORM = "PERFORM 600-GET-TIMESTAMP"


def _open_indexes(bodies: list[str]) -> list[int]:
    return [
        index
        for index, body in enumerate(bodies)
        if OPEN_PERFORM.match(body)
    ]


def test_the_program_opens_at_least_one_cursor(generated_bodies):
    assert _open_indexes(generated_bodies)


def test_a_dclgen_group_is_initialized_somewhere(generated_bodies):
    assert any(
        body.upper().startswith(INITIALIZE_GROUP)
        for body in generated_bodies
    )


def test_every_cursor_open_is_preceded_by_its_initialize(
    generated_bodies, previous_body
):
    for index in _open_indexes(generated_bodies):
        before = previous_body(index).upper()
        assert before.startswith(INITIALIZE_GROUP), (
            f"{generated_bodies[index]!r} is not preceded by an "
            f"INITIALIZE; found {generated_bodies[index - 1]!r}"
        )


def test_each_cursor_initializes_a_distinct_group(generated_bodies, previous_body):
    groups = [
        previous_body(index).upper().split()[1].rstrip(".")
        for index in _open_indexes(generated_bodies)
    ]
    assert len(groups) == len(set(groups))


def test_no_startup_initialize_paragraph_remains(generated_bodies):
    headers = [
        body.upper().rstrip(".")
        for body in generated_bodies
        if body.endswith(".") and " " not in body
    ]
    assert STARTUP_PARAGRAPH not in headers


def test_no_perform_of_the_startup_paragraph_remains(generated_bodies):
    assert not any(
        body.upper().startswith(f"PERFORM {STARTUP_PARAGRAPH}")
        for body in generated_bodies
    )


def test_the_timestamp_paragraph_is_performed_at_most_once(generated_bodies):
    performs = [
        body
        for body in generated_bodies
        if body.upper().startswith(TIMESTAMP_PERFORM)
    ]
    assert len(performs) <= 1, performs


def test_no_fetch_paragraph_clears_its_host_group(generated_bodies):
    fetches = [
        index
        for index, body in enumerate(generated_bodies)
        if FETCH_HEADER.match(body)
    ]
    assert fetches

    for index in fetches:
        window = generated_bodies[index:index + 4]
        assert not any(
            body.upper().startswith(INITIALIZE_GROUP) for body in window
        ), window


def test_no_empty_initialize_statement(generated_bodies):
    assert "INITIALIZE ." not in generated_bodies
    assert "INITIALIZE" not in generated_bodies
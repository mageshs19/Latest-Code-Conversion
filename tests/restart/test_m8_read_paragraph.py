# LOCATION: tests/restart/test_m8_read_paragraph.py
# ACTION: CREATE NEW FILE
"""M8 contract tests: the reader paragraph.

The generated reader carried two lines and none of the four statements
that make a checkpoint meaningful. Without them NB-READ is always zero
and every restart resumes from record one.
"""

from __future__ import annotations

import dataclasses

import pytest

from converter.generators.restart.read_paragraph_builder import (
    ROLE_READ,
    RestartReadParagraphBuilder,
)
from converter.generators.restart.restart_config import (
    RestartConfig,
    RestartProgramNames,
)

GENERATED_READER = [
    "READ OPERATIES INTO VMDZ205I",
    "   AT END MOVE 'Y' TO SW-EOF.",
]


@pytest.fixture
def builder(config):
    return RestartReadParagraphBuilder(config)


@pytest.fixture
def paragraph(builder):
    return builder.build()


def _body(paragraph):
    return [line.strip() for line in paragraph.body if line.strip()]


def _text(paragraph):
    return "\n".join(paragraph.lines())


# ---------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------

def test_the_paragraph_is_named_from_the_source(config, paragraph):
    assert paragraph.name == config.names.read_paragraph
    assert paragraph.lines()[0] == f"{config.names.read_paragraph}."


def test_the_role_is_not_a_restart_family_role(paragraph):
    from rules import restart_standard_rules as std

    assert paragraph.role == ROLE_READ
    assert ROLE_READ not in std.RESTART_PARAGRAPH_ROLES


def test_a_debug_trace_is_carried(config, paragraph):
    assert config.names.read_paragraph in paragraph.debug_trace


def test_no_placeholder_survives(paragraph):
    text = _text(paragraph)
    assert "{" not in text
    assert "}" not in text


def test_the_paragraph_closes_its_sentence(paragraph):
    assert _body(paragraph)[-1].endswith(".")


def test_the_scope_is_balanced(paragraph):
    body = " ".join(_body(paragraph))
    assert body.count("END-IF") == 1
    assert body.count(" IF ") + body.startswith("IF ") >= 1


# ---------------------------------------------------------------------
# The READ itself
# ---------------------------------------------------------------------

def test_the_record_is_initialised_before_the_read(config, paragraph):
    body = _body(paragraph)
    init = next(i for i, l in enumerate(body) if l.startswith("INITIALIZE"))
    read = next(i for i, l in enumerate(body) if l.startswith("READ "))
    assert init < read
    assert body[init] == f"INITIALIZE {config.names.record_name}."


def test_the_read_names_the_file_and_the_record(config, paragraph):
    text = _text(paragraph)
    assert (
        f"READ {config.names.file_name} INTO {config.names.record_name}"
        in text
    )


def test_at_end_sets_the_88_level(config, paragraph):
    """MOVE 'Y' TO SW-EOF was the shape the manual replaced."""
    text = _text(paragraph)
    assert f"AT END SET {config.names.eof_condition} TO TRUE." in text
    assert "'Y'" not in text


# ---------------------------------------------------------------------
# The four checkpoint statements
# ---------------------------------------------------------------------

def test_the_commit_counter_is_incremented(config, paragraph):
    assert f"ADD +1 TO {config.names.commit_counter}" in _body(paragraph)


def test_the_input_counter_is_incremented(config, paragraph):
    assert f"ADD +1 TO {config.names.input_counter}" in _body(paragraph)


def test_the_record_is_saved_for_the_checkpoint(config, paragraph):
    expected = (
        f"MOVE {config.names.record_name} TO {config.names.input_save_area}"
    )
    assert expected in _body(paragraph)


def test_the_four_statements_are_guarded_by_not_eof(config, paragraph):
    """At end of file there is no record to count or save."""
    body = _body(paragraph)
    guard = next(
        i for i, l in enumerate(body)
        if l == f"IF {config.names.not_eof_condition}"
    )
    for statement in ("ADD +1 TO", "MOVE "):
        position = next(
            i for i, l in enumerate(body) if l.startswith(statement)
        )
        assert position > guard


def test_every_required_statement_is_present(builder, paragraph):
    text = _text(paragraph).upper()
    for statement in builder.required_statements():
        assert statement.upper() in text


def test_four_statements_are_required(builder):
    assert len(builder.required_statements()) == 4


# ---------------------------------------------------------------------
# Inspecting a source reader
# ---------------------------------------------------------------------

def test_the_generated_reader_is_missing_all_four(builder):
    assert len(builder.missing_statements(GENERATED_READER)) == 4


def test_the_generated_reader_needs_a_rebuild(builder):
    assert builder.needs_rebuild(GENERATED_READER) is True


def test_every_gap_is_reported(builder):
    builder.needs_rebuild(GENERATED_READER)
    assert len(builder.messages) == 4
    assert all("lacks" in m for m in builder.messages)


def test_a_complete_reader_needs_no_rebuild(builder, paragraph):
    assert builder.needs_rebuild(list(paragraph.lines())) is False


def test_a_partial_reader_reports_only_its_gaps(config, builder):
    lines = [
        f"INITIALIZE {config.names.record_name}.",
        f"READ {config.names.file_name} INTO {config.names.record_name}",
        f"   AT END SET {config.names.eof_condition} TO TRUE.",
        f"ADD +1 TO {config.names.commit_counter}",
    ]
    missing = builder.missing_statements(lines)
    assert len(missing) == 2
    assert any(config.names.input_counter in m for m in missing)
    assert any(config.names.input_save_area in m for m in missing)


def test_whitespace_differences_do_not_count_as_missing(config, builder):
    lines = [f"ADD    +1    TO    {config.names.commit_counter}"]
    missing = builder.missing_statements(lines)
    assert not any(config.names.commit_counter in m for m in missing)


def test_an_empty_reader_is_missing_everything(builder):
    assert len(builder.missing_statements([])) == 4


# ---------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------

def test_an_unusable_config_renders_nothing(role):
    builder = RestartReadParagraphBuilder(
        RestartConfig.build(role, RestartProgramNames())
    )
    assert builder.build() is None
    assert builder.messages


def test_a_missing_save_area_renders_nothing(role, complete_names):
    names = dataclasses.replace(complete_names, input_save_area="")
    builder = RestartReadParagraphBuilder(RestartConfig.build(role, names))
    assert builder.build() is None
    assert any("input_save_area" in m for m in builder.messages)


def test_a_role_without_retention_renders_nothing(role, complete_names):
    bare = dataclasses.replace(role, retention_days=0)
    builder = RestartReadParagraphBuilder(
        RestartConfig.build(bare, complete_names)
    )
    assert builder.build() is None
    assert any("retention" in m for m in builder.messages)


# ---------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------

def test_building_twice_produces_identical_output(config):
    first = RestartReadParagraphBuilder(config).build()
    second = RestartReadParagraphBuilder(config).build()
    assert first == second


def test_messages_are_reset_between_builds(builder):
    builder.build()
    first = len(builder.messages)
    builder.build()
    assert len(builder.messages) == first


def test_the_build_is_reported(builder):
    builder.build()
    assert any("four checkpoint statements" in m for m in builder.messages)
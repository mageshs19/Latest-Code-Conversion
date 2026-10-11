# LOCATION: tests/restart/test_m5_flow_builder.py
# ACTION: CREATE NEW FILE
"""M5 contract tests: the five restart flow paragraphs.

The two obligations this module exists to enforce:

    a completed previous run must ABEND, never silently re-run
    a resumed run must REPOSITION the input file by replaying the reader

The generated 810-JOB-IS-RESTART honoured neither.
"""

from __future__ import annotations

import dataclasses

import pytest

from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_flow_builder import (
    FLOW_TEMPLATES,
    RestartFlowBuilder,
)
from converter.generators.restart.restart_paragraph import RestartParagraph
from rules import restart_standard_rules as std


@pytest.fixture
def builder(config):
    return RestartFlowBuilder(config)


@pytest.fixture
def paragraphs(builder):
    return {p.role: p for p in builder.build_all()}


def _text(paragraph: RestartParagraph) -> str:
    return "\n".join(paragraph.lines())


# ---------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------

def test_five_paragraphs_are_produced(paragraphs):
    assert set(paragraphs) == {
        std.ROLE_CONTROL,
        std.ROLE_RESTART_FOUND,
        std.ROLE_WRITE_RESTART,
        std.ROLE_COMMIT,
        std.ROLE_ABEND,
    }


def test_the_emission_order_is_fixed(builder):
    roles = [p.role for p in builder.build_all()]
    assert roles == [role for role, _template in FLOW_TEMPLATES]


def test_each_header_matches_the_config(config, paragraphs):
    for role, paragraph in paragraphs.items():
        assert paragraph.name == config.paragraph(role)
        assert paragraph.lines()[0] == f"{config.paragraph(role)}."


def test_each_paragraph_closes_its_sentence(paragraphs):
    for paragraph in paragraphs.values():
        assert paragraph.executable()[-1].endswith(".")


def test_each_paragraph_carries_a_debug_trace(config, paragraphs):
    for role, paragraph in paragraphs.items():
        assert config.paragraph(role) in paragraph.debug_trace


def test_no_rendered_line_keeps_a_placeholder(paragraphs):
    for paragraph in paragraphs.values():
        text = _text(paragraph)
        assert "{" not in text
        assert "}" not in text


def test_paragraphs_are_frozen(paragraphs):
    with pytest.raises(dataclasses.FrozenInstanceError):
        paragraphs[std.ROLE_CONTROL].name = "OTHER"


def test_the_build_is_reported(builder):
    builder.build_all()
    assert any("generated 5 paragraph" in m for m in builder.messages)


def test_build_by_role_returns_one_paragraph(builder):
    paragraph = builder.build(std.ROLE_COMMIT)
    assert paragraph is not None
    assert paragraph.role == std.ROLE_COMMIT


# ---------------------------------------------------------------------
# control
# ---------------------------------------------------------------------

def test_control_sets_the_whole_checkpoint_key(config, paragraphs):
    text = _text(paragraphs[std.ROLE_CONTROL])
    assert config.names.program_constant in text
    assert config.role.program_field in text
    assert config.names.run_date_field in text
    assert config.role.date_field in text
    assert str(config.phase_number) in text
    assert config.role.phase_field in text


def test_control_routes_every_sqlcode(config, paragraphs):
    text = _text(paragraphs[std.ROLE_CONTROL])
    assert f"WHEN {std.SQLCODE_OK}" in text
    assert f"WHEN {std.SQLCODE_NOT_FOUND}" in text
    assert "WHEN OTHER" in text
    assert config.paragraph(std.ROLE_RESTART_FOUND) in text
    assert config.paragraph(std.ROLE_WRITE_RESTART) in text
    assert config.names.error_paragraph in text


def test_control_performs_the_select(config, paragraphs):
    text = _text(paragraphs[std.ROLE_CONTROL])
    assert f"PERFORM {config.paragraph(std.ROLE_SELECT)}." in text


def test_control_zeroes_the_commit_counter(config, paragraphs):
    text = _text(paragraphs[std.ROLE_CONTROL])
    assert f"MOVE 0 TO {config.names.commit_counter}." in text


# ---------------------------------------------------------------------
# restart_found - the two obligations
# ---------------------------------------------------------------------

def test_a_completed_previous_run_abends(config, paragraphs):
    text = _text(paragraphs[std.ROLE_RESTART_FOUND])
    assert f"= '{std.STATUS_COMPLETE}'" in text
    assert f"PERFORM {config.paragraph(std.ROLE_ABEND)}" in text
    assert "PREVIOUS RUN COMPLETE" in text


def test_a_completed_previous_run_never_merely_continues(paragraphs):
    """CONTINUE here is what allowed a double run."""
    body = paragraphs[std.ROLE_RESTART_FOUND].executable()
    assert "CONTINUE" not in body


def test_a_resumed_run_replays_the_reader(config, paragraphs):
    text = _text(paragraphs[std.ROLE_RESTART_FOUND])
    assert f"PERFORM {config.names.read_count_field} OF " in text
    assert "TIMES" in text
    assert f"PERFORM {config.names.read_paragraph}" in text
    assert "END-PERFORM" in text


def test_a_resumed_run_restores_the_input_counter(config, paragraphs):
    text = _text(paragraphs[std.ROLE_RESTART_FOUND])
    assert config.names.input_counter in text


def test_restart_found_loads_the_payload_first(config, paragraphs):
    body = paragraphs[std.ROLE_RESTART_FOUND].executable()
    load = next(
        i for i, l in enumerate(body) if config.role.payload_text_field in l
    )
    test = next(i for i, l in enumerate(body) if l.startswith("IF "))
    assert load < test


# ---------------------------------------------------------------------
# write_restart
# ---------------------------------------------------------------------

def test_write_restart_marks_the_run_incomplete(config, paragraphs):
    text = _text(paragraphs[std.ROLE_WRITE_RESTART])
    assert f"MOVE '{std.STATUS_INCOMPLETE}'" in text
    assert config.role.status_field in text


def test_write_restart_uses_the_supplied_retention(config, paragraphs):
    text = _text(paragraphs[std.ROLE_WRITE_RESTART])
    assert f"MOVE {config.retention_days}" in text
    assert config.role.retention_field in text


def test_write_restart_starts_at_record_zero(config, paragraphs):
    text = _text(paragraphs[std.ROLE_WRITE_RESTART])
    assert f"MOVE 0" in text
    assert config.names.input_counter in text
    assert f"INITIALIZE {config.names.restart_key_field}." in text


def test_write_restart_uses_the_measured_length(config, paragraphs):
    text = _text(paragraphs[std.ROLE_WRITE_RESTART])
    assert str(config.payload_full_length) in text
    assert config.role.payload_len_field in text


def test_write_restart_performs_the_insert(config, paragraphs):
    text = _text(paragraphs[std.ROLE_WRITE_RESTART])
    assert f"PERFORM {config.paragraph(std.ROLE_INSERT)}." in text


# ---------------------------------------------------------------------
# commit
# ---------------------------------------------------------------------

def test_commit_resets_the_commit_counter(config, paragraphs):
    text = _text(paragraphs[std.ROLE_COMMIT])
    assert f"MOVE 0" in text
    assert config.names.commit_counter in text


def test_commit_saves_the_counter_and_the_last_record(config, paragraphs):
    text = _text(paragraphs[std.ROLE_COMMIT])
    assert config.names.input_counter in text
    assert config.names.read_count_field in text
    assert config.names.input_save_area in text
    assert config.names.restart_key_field in text


def test_commit_marks_complete_only_at_eof(config, paragraphs):
    text = _text(paragraphs[std.ROLE_COMMIT])
    assert config.names.eof_condition in text
    assert f"'{std.STATUS_COMPLETE}'" in text
    assert f"'{std.STATUS_INCOMPLETE}'" in text


def test_commit_uses_the_manual_commit_length(config, paragraphs):
    text = _text(paragraphs[std.ROLE_COMMIT])
    assert str(config.payload_length_on_commit) in text


def test_commit_updates_then_commits(config, paragraphs):
    body = paragraphs[std.ROLE_COMMIT].executable()
    update = next(
        i for i, l in enumerate(body)
        if config.paragraph(std.ROLE_UPDATE) in l
    )
    commit = next(i for i, l in enumerate(body) if l == "COMMIT")
    assert update < commit


# ---------------------------------------------------------------------
# abend
# ---------------------------------------------------------------------

def test_abend_calls_the_resolved_module(config, paragraphs):
    text = _text(paragraphs[std.ROLE_ABEND])
    assert f"CALL {config.names.abend_module}." in text


# ---------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------

def test_an_unusable_config_writes_nothing(role):
    from converter.generators.restart.restart_config import (
        RestartProgramNames,
    )

    builder = RestartFlowBuilder(
        RestartConfig.build(role, RestartProgramNames())
    )
    assert builder.build_all() == []
    assert builder.messages


def test_a_role_without_retention_writes_nothing(role, complete_names):
    bare = dataclasses.replace(role, retention_days=0)
    builder = RestartFlowBuilder(RestartConfig.build(bare, complete_names))
    assert builder.build_all() == []
    assert any("retention" in m for m in builder.messages)


def test_an_unmeasured_payload_writes_nothing(role, complete_names):
    names = dataclasses.replace(complete_names, restart_key_size=0)
    builder = RestartFlowBuilder(RestartConfig.build(role, names))
    assert builder.build_all() == []
    assert any("restart_key_size" in m for m in builder.messages)


def test_build_by_role_returns_none_when_refused(role):
    from converter.generators.restart.restart_config import (
        RestartProgramNames,
    )

    builder = RestartFlowBuilder(
        RestartConfig.build(role, RestartProgramNames())
    )
    assert builder.build(std.ROLE_COMMIT) is None


# ---------------------------------------------------------------------
# Determinism and scheme independence
# ---------------------------------------------------------------------

def test_building_twice_produces_identical_output(config):
    first = RestartFlowBuilder(config).build_all()
    second = RestartFlowBuilder(config).build_all()
    assert first == second


def test_messages_are_reset_between_builds(builder):
    builder.build_all()
    first = len(builder.messages)
    builder.build_all()
    assert len(builder.messages) == first


def test_a_different_scheme_only_renames_paragraphs(role, complete_names):
    seven = RestartFlowBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_SEVEN_SERIES)
    ).build_all()
    eight = RestartFlowBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_EIGHT_SERIES)
    ).build_all()

    assert [p.role for p in seven] == [p.role for p in eight]
    for a, b in zip(seven, eight):
        assert a.name != b.name or a.role in (std.ROLE_SELECT,)
        assert len(a.body) == len(b.body)
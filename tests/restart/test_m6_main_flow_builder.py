# LOCATION: tests/restart/test_m6_main_flow_builder.py
# ACTION: CREATE NEW FILE
"""M6 contract tests: the mainline.

Three defects in the generated mainline this module makes impossible:

    the control paragraph was never performed
    the commit paragraph was never performed
    there was no STOP RUN, so the program fell through into the first
    restart paragraph and executed the whole family in source order
"""

from __future__ import annotations

import dataclasses

import pytest

from converter.generators.restart.restart_config import (
    RestartConfig,
    RestartProgramNames,
)
from converter.generators.restart.restart_main_flow_builder import (
    STOP_RUN,
    RestartMainFlowBuilder,
)
from rules import restart_standard_rules as std

TOTALS = (
    "DISPLAY 'NUMBER OF RECORDS PROCESSED: ' WS-NB-INPUT-UPD-I.",
    "DISPLAY 'NUMBER OF UPDATE BFAR      : ' WS-NB-BFAR-UPD-I.",
)


@pytest.fixture
def builder(config):
    return RestartMainFlowBuilder(config)


@pytest.fixture
def body(builder):
    return builder.statements()


def _index(body, marker: str) -> int:
    return next(i for i, line in enumerate(body) if marker in line)


# ---------------------------------------------------------------------
# The three fixed defects
# ---------------------------------------------------------------------

def test_the_control_paragraph_is_performed(config, body):
    assert f"PERFORM {config.paragraph(std.ROLE_CONTROL)}." in body


def test_the_commit_paragraph_is_performed(config, body):
    assert f"PERFORM {config.paragraph(std.ROLE_COMMIT)}." in body


def test_stop_run_is_the_last_statement(body):
    assert body[-1] == STOP_RUN


def test_stop_run_appears_exactly_once(body):
    assert body.count(STOP_RUN) == 1


# ---------------------------------------------------------------------
# Order
# ---------------------------------------------------------------------

def test_the_statement_order_is_fixed(config, body):
    open_at = _index(body, "OPEN INPUT")
    control = _index(body, config.paragraph(std.ROLE_CONTROL))
    read = _index(body, f"PERFORM {config.names.read_paragraph}.")
    process = _index(body, config.names.process_paragraph)
    commit = _index(body, config.paragraph(std.ROLE_COMMIT))
    close = _index(body, "CLOSE ")
    assert open_at < control < read < process < commit < close


def test_control_runs_before_the_first_read(config, body):
    """A read before repositioning would consume record one twice."""
    control = _index(body, config.paragraph(std.ROLE_CONTROL))
    read = _index(body, f"PERFORM {config.names.read_paragraph}.")
    assert control < read


def test_close_is_the_statement_before_stop_run(config, body):
    assert body[-2] == f"CLOSE {config.names.file_name}."


def test_the_file_is_opened_and_closed_once(config, body):
    opens = [l for l in body if l.startswith("OPEN INPUT")]
    closes = [l for l in body if l.startswith("CLOSE ")]
    assert opens == [f"OPEN INPUT {config.names.file_name}."]
    assert closes == [f"CLOSE {config.names.file_name}."]


# ---------------------------------------------------------------------
# The driving loop
# ---------------------------------------------------------------------

def test_the_loop_drives_the_business_paragraph(config, body):
    expected = (
        f"PERFORM {config.names.process_paragraph} "
        f"UNTIL {config.names.eof_condition}."
    )
    assert expected in body


def test_the_loop_uses_the_88_level_not_a_literal(config, body):
    """IF SW-EOF = 'Y' was the shape the manual replaced."""
    loop = next(l for l in body if " UNTIL " in l)
    assert "'Y'" not in loop
    assert "=" not in loop
    assert config.names.eof_condition in loop


def test_the_first_read_is_unconditional(config, body):
    """The generated mainline wrapped it in an IF that could never fire."""
    read = f"PERFORM {config.names.read_paragraph}."
    assert read in body
    assert not any(l.startswith("IF ") for l in body)


# ---------------------------------------------------------------------
# Totals come from the shared composer
# ---------------------------------------------------------------------

def test_no_totals_are_authored_by_default(builder):
    assert not any("DISPLAY" in line for line in builder.statements())


def test_supplied_totals_are_spliced_before_close(config, builder):
    body = builder.statements(TOTALS)
    for line in TOTALS:
        assert line in body
    assert _index(body, "DISPLAY") < _index(body, "CLOSE ")


def test_supplied_totals_are_spliced_after_the_commit(config, builder):
    body = builder.statements(TOTALS)
    commit = _index(body, config.paragraph(std.ROLE_COMMIT))
    assert commit < _index(body, "DISPLAY")


def test_supplied_totals_are_unchanged(builder):
    body = builder.statements(TOTALS)
    assert [l for l in body if l.startswith("DISPLAY")] == list(TOTALS)


def test_the_totals_decision_is_reported(builder):
    builder.build(TOTALS)
    assert any("spliced 2 totals" in m for m in builder.messages)
    builder.build()
    assert any("no totals supplied" in m for m in builder.messages)


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------

def test_no_placeholder_survives(builder):
    text = "\n".join(builder.build(TOTALS))
    assert "{" not in text
    assert "}" not in text


def test_every_statement_closes_its_sentence(body):
    for line in body:
        assert line.endswith(".")


def test_blank_separators_are_present_in_the_raw_build(builder):
    """Readability is part of the manual reference layout."""
    assert any(line == "" for line in builder.build())


# ---------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------

def test_an_unusable_config_builds_nothing(role):
    builder = RestartMainFlowBuilder(
        RestartConfig.build(role, RestartProgramNames())
    )
    assert builder.build() == ()
    assert builder.messages


def test_a_role_without_retention_builds_nothing(role, complete_names):
    bare = dataclasses.replace(role, retention_days=0)
    builder = RestartMainFlowBuilder(RestartConfig.build(bare, complete_names))
    assert builder.build() == ()
    assert any("retention" in m for m in builder.messages)


def test_an_unmeasured_payload_builds_nothing(role, complete_names):
    names = dataclasses.replace(complete_names, restart_key_size=0)
    builder = RestartMainFlowBuilder(RestartConfig.build(role, names))
    assert builder.build() == ()
    assert any("restart_key_size" in m for m in builder.messages)


def test_a_missing_process_paragraph_builds_nothing(role, complete_names):
    names = dataclasses.replace(complete_names, process_paragraph="")
    builder = RestartMainFlowBuilder(RestartConfig.build(role, names))
    assert builder.build() == ()
    assert any("process_paragraph" in m for m in builder.messages)


# ---------------------------------------------------------------------
# Determinism and scheme independence
# ---------------------------------------------------------------------

def test_building_twice_produces_identical_output(config):
    first = RestartMainFlowBuilder(config).build(TOTALS)
    second = RestartMainFlowBuilder(config).build(TOTALS)
    assert first == second


def test_messages_are_reset_between_builds(builder):
    builder.build()
    first = len(builder.messages)
    builder.build()
    assert len(builder.messages) == first


def test_a_different_scheme_changes_only_the_performed_names(
    role, complete_names
):
    seven = RestartMainFlowBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_SEVEN_SERIES)
    ).statements()
    eight = RestartMainFlowBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_EIGHT_SERIES)
    ).statements()

    assert len(seven) == len(eight)
    assert seven[-1] == eight[-1] == STOP_RUN
    assert seven[-2] == eight[-2]


def test_the_mainline_performs_only_resolved_paragraphs(config, body):
    performed = {
        line.split()[1].rstrip(".")
        for line in body
        if line.startswith("PERFORM ")
    }
    known = {
        config.paragraph(std.ROLE_CONTROL),
        config.paragraph(std.ROLE_COMMIT),
        config.names.read_paragraph,
        config.names.process_paragraph,
    }
    assert performed == known
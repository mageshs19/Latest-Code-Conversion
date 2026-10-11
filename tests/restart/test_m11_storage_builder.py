# LOCATION: tests/restart/test_m11_storage_builder.py
# ACTION: CREATE NEW FILE
"""M11 - the restart working-storage builder.

    contract    - three groups, names resolved, sizes measured
    refusal     - one missing name or size emits NOTHING
    determinism - building twice produces identical lines

WHY THE SIZES MATTER MOST

The legacy generator hardcoded PIC X(1200). This builder renders the
size M3 MEASURED, so a program with a shorter restart key gets a
shorter field. That is the whole point of principle B, and the test
below changes the measurement to prove the output follows it.
"""

from __future__ import annotations

import dataclasses

import pytest

from catalogs.restart_storage_catalog import (
    DATE_GROUP,
    HELP_GROUP,
    SWITCH_GROUP,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_storage_builder import (
    RestartStorageBuilder,
)


@pytest.fixture
def builder(config):
    return RestartStorageBuilder(config)


@pytest.fixture
def lines(builder):
    return [line.strip() for line in builder.build() if line.strip()]


#
# Contract
#
def test_all_three_groups_are_declared(lines):
    for group in (SWITCH_GROUP, HELP_GROUP, DATE_GROUP):
        assert any(line.startswith(f"01  {group}") for line in lines), group


def test_the_switch_is_named_after_the_record(config, builder):
    assert builder.eof_switch() == f"SW-{config.names.record_name}"


def test_the_conditions_are_named_after_the_record(config, builder):
    record = config.names.record_name
    assert builder.eof_condition() == f"{record}-EOF"
    assert builder.not_eof_condition() == f"{record}-NOT-EOF"


def test_both_88_levels_are_declared(builder, lines):
    assert any(
        line.startswith("88") and builder.eof_condition() in line
        for line in lines
    )
    assert any(
        line.startswith("88") and builder.not_eof_condition() in line
        for line in lines
    )


def test_the_eof_condition_carries_the_true_value(builder, lines):
    line = next(l for l in lines if builder.eof_condition() in l and "88" in l)
    assert "'Y'" in line


def test_the_not_eof_condition_carries_the_false_value(builder, lines):
    line = next(
        l for l in lines if builder.not_eof_condition() in l and "88" in l
    )
    assert "'N'" in line


def test_every_resolved_name_appears(config, lines):
    names = config.names
    text = "\n".join(lines)
    for name in (
        names.restart_record,
        names.read_count_field,
        names.restart_key_field,
        names.input_save_area,
        names.commit_counter,
        names.input_counter,
    ):
        assert name in text, name


def test_no_placeholder_survives(lines):
    text = "\n".join(lines)
    assert "{" not in text
    assert "}" not in text


#
# MEASURED, not declared
#
def test_the_key_picture_uses_the_measured_size(config, lines):
    assert any(f"PIC X({config.names.restart_key_size})" in l for l in lines)


def test_the_count_picture_uses_the_measured_size(config, lines):
    assert any(f"PIC 9({config.names.read_count_size})" in l for l in lines)


def test_a_shorter_key_produces_a_shorter_field(role, complete_names):
    """1200 was never a constant; it is this program's measurement."""
    names = dataclasses.replace(complete_names, restart_key_size=800)
    built = RestartStorageBuilder(RestartConfig.build(role, names)).build()
    text = "\n".join(built)
    assert "PIC X(800)" in text
    assert "PIC X(1200)" not in text


def test_the_save_area_matches_the_key_length(config, lines):
    """The save area is copied into the key; a shorter one truncates."""
    size = config.names.restart_key_size
    save = config.names.input_save_area
    assert any(save in l and f"PIC X({size})" in l for l in lines)


#
# Refusal
#
@pytest.mark.parametrize(
    "field",
    [
        "record_name",
        "restart_record",
        "read_count_field",
        "restart_key_field",
        "input_save_area",
        "commit_counter",
        "input_counter",
    ],
)
def test_one_missing_name_emits_nothing(role, complete_names, field):
    names = dataclasses.replace(complete_names, **{field: ""})
    builder = RestartStorageBuilder(RestartConfig.build(role, names))
    assert builder.build() == ()
    assert any(field in message for message in builder.messages)


@pytest.mark.parametrize("field", ["read_count_size", "restart_key_size"])
def test_an_unmeasured_size_emits_nothing(role, complete_names, field):
    names = dataclasses.replace(complete_names, **{field: 0})
    builder = RestartStorageBuilder(RestartConfig.build(role, names))
    assert builder.build() == ()
    assert any("never measured" in message for message in builder.messages)


def test_a_refusal_is_never_partial(role, complete_names):
    names = dataclasses.replace(complete_names, restart_key_field="")
    built = RestartStorageBuilder(RestartConfig.build(role, names)).build()
    assert built == ()


#
# Determinism
#
def test_building_twice_produces_identical_lines(config):
    first = RestartStorageBuilder(config).build()
    second = RestartStorageBuilder(config).build()
    assert first == second


def test_the_build_is_reported(builder):
    builder.build()
    assert any("generated" in message for message in builder.messages)
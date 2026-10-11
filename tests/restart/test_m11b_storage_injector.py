# LOCATION: tests/restart/test_m11b_storage_injector.py
# ACTION: CREATE NEW FILE
"""M11b - placing the restart working storage.

    contract    - missing groups are declared, in WORKING-STORAGE
    refusal     - no section header, no insertion
    determinism - a second run inserts nothing
"""

from __future__ import annotations

import dataclasses

import pytest

from catalogs.restart_storage_catalog import (
    DATE_GROUP,
    HELP_GROUP,
    SWITCH_GROUP,
)
from converter.composers.restart.restart_storage_injector import (
    WORKING_STORAGE_TOKEN,
    RestartStorageInjector,
)
from converter.generators.restart.restart_config import RestartConfig

BARE = [
    "000100 DATA DIVISION.",
    "000110 FILE SECTION.",
    "000120 FD   OPERATIES",
    "000130 01   OPERATIES-REC             PIC X(1200).",
    "000140 WORKING-STORAGE SECTION.",
    "000150 77  USERABEN                   PIC X(8).",
    "000160 PROCEDURE DIVISION.",
    "000170     STOP RUN.",
]


@pytest.fixture
def injector(config, line_utils):
    return RestartStorageInjector(config, line_utils)


def _logical(line_utils, lines):
    out = []
    for raw in lines:
        body = str(line_utils.logical(raw) or "").strip().upper()
        if body:
            out.append(" ".join(body.split()))
    return out


#
# Contract
#
def test_every_group_is_declared(injector, line_utils):
    body = _logical(line_utils, injector.inject(BARE))
    for group in (SWITCH_GROUP, HELP_GROUP, DATE_GROUP):
        assert any(line.startswith(f"01 {group}") for line in body), group


def test_the_storage_lands_in_working_storage(injector, line_utils):
    body = _logical(line_utils, injector.inject(BARE))
    section = next(
        i for i, l in enumerate(body) if l.startswith(WORKING_STORAGE_TOKEN)
    )
    group = next(
        i for i, l in enumerate(body) if l.startswith(f"01 {SWITCH_GROUP}")
    )
    assert group > section


def test_nothing_lands_in_the_file_section(injector, line_utils):
    """VALUE under an FD is illegal, and hides the FD's real record."""
    body = _logical(line_utils, injector.inject(BARE))
    file_section = next(
        i for i, l in enumerate(body) if l.startswith("FILE SECTION")
    )
    working = next(
        i for i, l in enumerate(body) if l.startswith(WORKING_STORAGE_TOKEN)
    )
    for index, line in enumerate(body):
        if file_section < index < working:
            assert SWITCH_GROUP not in line
            assert HELP_GROUP not in line


def test_the_decision_is_reported(injector):
    injector.inject(BARE)
    assert any("was absent; declared it" in m for m in injector.messages)


#
# Only what is missing
#
def test_an_existing_group_is_left_alone(injector, line_utils):
    existing = BARE[:5] + [f"000155 01  {SWITCH_GROUP}."] + BARE[5:]
    body = _logical(line_utils, injector.inject(existing))
    assert len([l for l in body if l.startswith(f"01 {SWITCH_GROUP}")]) == 1
    assert any("already declared" in m for m in injector.messages)


def test_the_other_groups_are_still_added(injector, line_utils):
    existing = BARE[:5] + [f"000155 01  {SWITCH_GROUP}."] + BARE[5:]
    body = _logical(line_utils, injector.inject(existing))
    assert any(l.startswith(f"01 {HELP_GROUP}") for l in body)


#
# Refusal
#
def test_no_working_storage_means_no_insertion(injector, line_utils):
    lines = [l for l in BARE if WORKING_STORAGE_TOKEN not in l.upper()]
    assert injector.inject(lines) == lines
    assert any("must never go under an FD" in m for m in injector.messages)


def test_an_unusable_config_places_nothing(role, complete_names, line_utils):
    names = dataclasses.replace(complete_names, restart_key_size=0)
    injector = RestartStorageInjector(
        RestartConfig.build(role, names), line_utils
    )
    assert injector.inject(BARE) == BARE
    assert any("never measured" in m for m in injector.messages)


#
# Determinism
#
def test_running_twice_inserts_nothing_the_second_time(injector):
    once = injector.inject(BARE)
    twice = injector.inject(once)
    assert twice == once
    assert any("already declared" in m for m in injector.messages)
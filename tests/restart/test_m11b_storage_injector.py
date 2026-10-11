# LOCATION: tests/restart/test_m11b_storage_injector.py
# ACTION: REPLACE ENTIRE FILE
"""M11b - placing the restart working storage and its DCLGEN include.

    contract    - missing groups are declared, in WORKING-STORAGE
    completion  - an existing group receives only the members it lacks
    include     - the restart host group is declared before it is used
    refusal     - no section header, no insertion
    determinism - a second run inserts nothing

CORRECTION - "left alone" was asserted at GROUP level

test_an_existing_group_is_left_alone built a fixture carrying

    01  WS-SWITCHES.

with no members, and asserted the injector reported "already declared"
and did nothing. That was the behaviour, and it was a defect:
RestartNameResolver had by then SUPPLIED the member names on the promise
that this composer would declare them, so the generated family moved to
fields that do not exist.

The judgement is now per FIELD, so the old fixture describes an
INCOMPLETE group, not an untouched one. The test is split along the line
the behaviour actually divides:

    complete   -> nothing inserted, reported as already declared
    incomplete -> only the missing subtrees appended, own members kept

and the anti-duplication guard - one 01 header, never two - is kept as
its own test, because it holds in both cases and is the thing that
mattered.

THE INCLUDE HAD NO TEST AT ALL

That is how INCLUDE DZ01RSTV : 0 survived three full conversion runs
while 700-SELECT-DZ01RSTV scored 2. The paragraph existed; the host
group it moved through did not.
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
    INCLUDE_NAME_ATTRIBUTES,
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

# The same program, but the switch group HEADER already exists with an
# unrelated member under it.
HEADER_ONLY = BARE[:5] + [f"000155 01  {SWITCH_GROUP}."] + BARE[5:]
HEADER_PLUS_MEMBER = BARE[:5] + [
    f"000155 01  {SWITCH_GROUP}.",
    "000156     02  WS-SOMETHING-ELSE          PIC X.",
] + BARE[5:]


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


def _include_member(config) -> str:
    """The DCLGEN member, resolved the way production resolves it."""
    role = getattr(config, "role", None)
    for attribute in INCLUDE_NAME_ATTRIBUTES:
        value = str(getattr(role, attribute, "") or "").strip().upper()
        if value:
            return value
    return ""


def _count_headers(body, group) -> int:
    return len([line for line in body if line.startswith(f"01 {group}")])


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


def test_the_groups_keep_declaration_order(injector, line_utils):
    """All four blocks share one anchor; ties must not reverse them."""
    body = _logical(line_utils, injector.inject(BARE))
    positions = [
        next(i for i, l in enumerate(body) if l.startswith(f"01 {group}"))
        for group in (SWITCH_GROUP, HELP_GROUP, DATE_GROUP)
    ]
    assert positions == sorted(positions)


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
# The restart DCLGEN include
#
def test_the_restart_include_is_emitted(injector, line_utils, config):
    """The generated SQL moves through the host group; something has to
    declare it."""
    member = _include_member(config)
    assert member, "the role carries no DCLGEN member name"

    body = _logical(line_utils, injector.inject(BARE))
    statement = f"EXEC SQL INCLUDE {member} END-EXEC."
    assert len([l for l in body if l.startswith(statement)]) == 1


def test_the_include_lands_in_working_storage(injector, line_utils, config):
    member = _include_member(config)
    body = _logical(line_utils, injector.inject(BARE))
    section = next(
        i for i, l in enumerate(body) if l.startswith(WORKING_STORAGE_TOKEN)
    )
    include = next(
        i
        for i, l in enumerate(body)
        if l.startswith(f"EXEC SQL INCLUDE {member}")
    )
    assert include > section


def test_the_include_is_not_added_twice(injector, line_utils, config):
    member = _include_member(config)
    once = injector.inject(BARE)
    twice = injector.inject(once)
    body = _logical(line_utils, twice)
    statement = f"EXEC SQL INCLUDE {member} END-EXEC."
    assert len([l for l in body if l.startswith(statement)]) == 1
    assert any("already included" in m for m in injector.messages)


def test_an_include_already_present_is_left_alone(
    injector, line_utils, config
):
    member = _include_member(config)
    supplied = BARE[:5] + [
        f"000145      EXEC SQL INCLUDE {member} END-EXEC."
    ] + BARE[5:]
    body = _logical(line_utils, injector.inject(supplied))
    statement = f"EXEC SQL INCLUDE {member} END-EXEC."
    assert len([l for l in body if l.startswith(statement)]) == 1


#
# Only what is missing
#
def test_an_existing_group_header_is_never_duplicated(injector, line_utils):
    """Holds whether the group is complete or not."""
    body = _logical(line_utils, injector.inject(HEADER_ONLY))
    assert _count_headers(body, SWITCH_GROUP) == 1


def test_an_incomplete_group_is_completed(injector, line_utils):
    """Was: 'an existing group is left alone'.

    The resolver has already SUPPLIED these member names. Skipping the
    group leaves the generated family moving to fields that do not
    exist.
    """
    before = _logical(line_utils, HEADER_ONLY)
    after = _logical(line_utils, injector.inject(HEADER_ONLY))

    assert len(after) > len(before)
    assert _count_headers(after, SWITCH_GROUP) == 1
    assert any("appended" in m for m in injector.messages)


def test_an_incomplete_group_keeps_its_own_members(injector, line_utils):
    after = _logical(line_utils, injector.inject(HEADER_PLUS_MEMBER))
    assert any("WS-SOMETHING-ELSE" in line for line in after)
    assert _count_headers(after, SWITCH_GROUP) == 1


def test_a_complete_group_is_left_alone(injector, line_utils):
    """A group this composer itself declared is complete by definition."""
    once = injector.inject(BARE)
    twice = injector.inject(once)
    assert twice == once
    assert any(
        "already declared and complete" in m for m in injector.messages
    )


def test_the_other_groups_are_still_added(injector, line_utils):
    body = _logical(line_utils, injector.inject(HEADER_ONLY))
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
    assert any(
        "already declared and complete" in m for m in injector.messages
    )
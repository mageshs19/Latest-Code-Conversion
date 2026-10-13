# LOCATION: tests/restart/test_m5_storage_builder_derives_record.py
# ACTION: CREATE NEW FILE
"""M5 regression contract: the switch and its 88-levels are always
built from the DERIVED record name.

THE DEFECT THIS MODULE EXISTS TO PREVENT

RestartStorageBuilder._record() used to return
RestartConfig.names.record_name verbatim. That value is MEASURED from
the source during the FINISHING phase, before the VM..BD../VM..BZ..
-> VMDZ.. derivation runs in POSTPROCESS, so SW-<record>,
<record>-EOF and <record>-NOT-EOF were all composed from the SOURCE
spelling.

Proven on disk (VM1BD567_13-10-2026_072742.cbl): the storage injector
ran twice against the same program, each time from a DIFFERENT
_record() snapshot (VMBD205I, then VMDZ205I), and produced TWO
complete switch groups instead of one. Neither downstream renamer can
repair a compound built on the record name after the fact - one is
blocked by a leading hyphen, the other by a trailing one, regardless
of which is used.

_record() now derives its own answer, so eof_switch(),
eof_condition() and not_eof_condition() always agree with EACH OTHER
and with every other invocation against the same config, however many
times the builder is constructed or the storage injection runs. This
does not by itself prevent the double-injection - that is a separate,
still-open defect in RestartStorageInjector's idempotency check - but
it guarantees that if a duplicate group IS emitted, both copies carry
the SAME, correctly derived name, which is what the test/set pair the
mainline depends on actually needs.

WHY THESE FIXTURES

role and complete_names come from tests/restart/conftest.py, the same
fixtures every other M-numbered restart test builds on. complete_names
already carries the DERIVED spelling (VMDZ205I, per
test_m3_name_resolver.py's own fixture); these tests override it with
dataclasses.replace() to simulate the UNDERIVED measurement the
resolver actually hands the builder during the FINISHING phase - the
exact gap that let NEW-2 through.
"""
from __future__ import annotations

import dataclasses

import pytest

from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_storage_builder import (
    RestartStorageBuilder,
)

#
# Contract: the derived spelling wins
#
def test_switch_and_conditions_use_the_derived_record_name(role, complete_names):
    names = dataclasses.replace(complete_names, record_name="VMBD205I")
    builder = RestartStorageBuilder(RestartConfig.build(role, names))

    assert builder.eof_switch() == "SW-VMDZ205I"
    assert builder.eof_condition() == "VMDZ205I-EOF"
    assert builder.not_eof_condition() == "VMDZ205I-NOT-EOF"


def test_an_already_derived_record_name_is_unchanged(role, complete_names):
    names = dataclasses.replace(complete_names, record_name="VMDZ205I")
    builder = RestartStorageBuilder(RestartConfig.build(role, names))

    assert builder.eof_switch() == "SW-VMDZ205I"
    assert builder.eof_condition() == "VMDZ205I-EOF"


def test_a_non_derivable_record_name_passes_through(role, complete_names):
    """A record whose marker is not BD/BZ (e.g. a non-IDMS-origin file
    name) is not this builder's concern to invent a derivation for.
    NameDerivationResolver returns it unchanged, so the switch is named
    after it literally, same as before this fix."""
    names = dataclasses.replace(complete_names, record_name="OPERATIES")
    builder = RestartStorageBuilder(RestartConfig.build(role, names))

    assert builder.eof_switch() == "SW-OPERATIES"
    assert builder.eof_condition() == "OPERATIES-EOF"


#
# Regression: the actual NEW-2 shape - two independent invocations,
# simulating the observed double-injection, must never disagree
#
def test_two_builders_never_disagree_on_the_switch_name(role, complete_names):
    names = dataclasses.replace(complete_names, record_name="VMBD205I")
    config = RestartConfig.build(role, names)

    first = RestartStorageBuilder(config)
    second = RestartStorageBuilder(config)

    assert first.eof_switch() == second.eof_switch()
    assert first.eof_condition() == second.eof_condition()
    assert first.not_eof_condition() == second.not_eof_condition()


def test_the_switch_and_its_88_levels_are_internally_consistent(role, complete_names):
    """Whatever the switch is named, PERFORM...UNTIL and SET are both
    built from eof_condition()/not_eof_condition() downstream, so the
    one invariant that actually prevents the runtime hang is: the
    record fragment inside the switch name equals the record fragment
    inside the condition names."""
    names = dataclasses.replace(complete_names, record_name="VMBD205I")
    builder = RestartStorageBuilder(RestartConfig.build(role, names))

    switch_record = builder.eof_switch().removeprefix("SW-")
    condition_record = builder.eof_condition().removesuffix("-EOF")

    assert switch_record == condition_record == "VMDZ205I"


#
# build() end-to-end: the rendered lines carry the derived spelling,
# never the source spelling, anywhere in the switch group
#
def test_build_renders_only_the_derived_spelling(role, complete_names):
    names = dataclasses.replace(complete_names, record_name="VMBD205I")
    builder = RestartStorageBuilder(RestartConfig.build(role, names))

    lines = builder.build()
    switch_block = "\n".join(lines)

    assert "VMBD205I" not in switch_block
    assert "SW-VMDZ205I" in switch_block
    assert "VMDZ205I-EOF" in switch_block
    assert "VMDZ205I-NOT-EOF" in switch_block


#
# Refusal is untouched by this change
#
def test_an_unusable_config_still_renders_nothing(role):
    from converter.generators.restart.restart_config import RestartProgramNames

    builder = RestartStorageBuilder(RestartConfig.build(role, RestartProgramNames()))
    assert builder.build() == ()
    assert builder.messages
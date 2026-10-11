# LOCATION: tests/restart/test_m10b_stage_adapter.py
# ACTION: CREATE NEW FILE
"""M10b - RestartStageAdapter.

    contract    - pipeline shape, role resolved, text injected
    refusal     - no context, no role, retrieval
    determinism - running twice reproduces the first output

WHY THE FIXTURES COME FROM M9B AND M10A

The adapter owns nothing but the hand-off. Re-asserting what the
composer or the resolver already guarantee would test them twice and
the adapter not at all.
"""

from __future__ import annotations

import dataclasses
import types

import pytest

from catalogs.restart_paragraph_catalog import RestartDclgenRole
from converter.composers.restart.restart_stage_adapter import (
    RestartRunContext,
    RestartStageAdapter,
)
from converter.resolvers.restart_role_resolver import SITE_AUTHORITY_FIELD

RECORD = "RESTART-REC"
RETENTION = 7
TOTALS = ("           DISPLAY 'TOTAL INPUT RECORDS : ' WS-TOTALS-LINE.",)
WORKING_STORAGE = "WORKING-STORAGE SECTION"
INCLUDE_TEMPLATE = "           EXEC SQL INCLUDE {name} END-EXEC."


class _Mapping:
    def __init__(self, table: str) -> None:
        self.table = table

    def db2_table_for_record(self, record_name: str) -> str:
        return self.table if record_name == RECORD else ""

    def has_table(self, table_name: str) -> bool:
        return table_name.upper() == self.table.upper()


@pytest.fixture
def dclgen(role):
    """A DCLGEN role carrying the same spellings as the M2 fixture."""
    values = {}
    for item in dataclasses.fields(RestartDclgenRole):
        if item.name == SITE_AUTHORITY_FIELD:
            continue
        values[item.name] = getattr(role, item.name)
    values["host_record_name"] = values.pop("host_record")
    return types.SimpleNamespace(**values)


@pytest.fixture
def source_text(source_lines, role):
    table = str(role.table_name).upper()
    out = list(source_lines)
    if not any(table in str(line).upper() for line in out):
        for index, line in enumerate(out):
            if WORKING_STORAGE in str(line).upper():
                out.insert(index + 1, INCLUDE_TEMPLATE.format(name=table))
                break
    return "\n".join(out)


@pytest.fixture
def context(dclgen):
    return RestartRunContext(
        record_name=RECORD,
        retention_days=RETENTION,
        dclgen_role=dclgen,
        totals=TOTALS,
    )


@pytest.fixture
def adapter(line_utils, context, role):
    return RestartStageAdapter(
        line_utils,
        context=context,
        mapping_repository=_Mapping(role.table_name),
    )


#
# Contract
#
def test_the_adapter_has_the_pipeline_shape(adapter):
    assert callable(adapter.compose)
    assert isinstance(adapter.messages, list)


def test_compose_returns_text_not_a_tuple(adapter, source_text):
    assert isinstance(adapter.compose(source_text), str)


def test_the_restart_family_is_injected(adapter, source_text, role):
    out = adapter.compose(source_text)
    assert role.table_name in out
    assert "STOP RUN" in out


def test_the_supplied_totals_are_carried_through(adapter, source_text):
    assert TOTALS[0].strip() in adapter.compose(source_text)


def test_the_role_resolution_is_reported(adapter, source_text):
    adapter.compose(source_text)
    assert any("Restart role:" in message for message in adapter.messages)


def test_the_injection_is_reported(adapter, source_text):
    adapter.compose(source_text)
    assert any("generated" in message for message in adapter.messages)


#
# Refusal
#
def test_no_context_is_a_reported_wiring_gap(line_utils, source_text):
    adapter = RestartStageAdapter(line_utils, context=None)
    assert adapter.compose(source_text) == source_text
    assert any("WIRING gap" in message for message in adapter.messages)


def test_a_retrieval_program_is_untouched(line_utils, context, source_text, role):
    adapter = RestartStageAdapter(
        line_utils,
        context=dataclasses.replace(context, program_kind="retrieval"),
        mapping_repository=_Mapping(role.table_name),
    )
    assert adapter.compose(source_text) == source_text


def test_a_retrieval_program_is_never_asked_for_a_role(
    line_utils, context, source_text
):
    """Three refusals for a correct program is noise, not a diagnostic."""
    adapter = RestartStageAdapter(
        line_utils,
        context=dataclasses.replace(context, program_kind="retrieval"),
    )
    adapter.compose(source_text)
    assert not any("Restart role:" in m for m in adapter.messages)


def test_a_missing_retention_leaves_the_program_unchanged(
    line_utils, context, source_text, role
):
    adapter = RestartStageAdapter(
        line_utils,
        context=dataclasses.replace(context, retention_days=0),
        mapping_repository=_Mapping(role.table_name),
    )
    assert adapter.compose(source_text) == source_text
    assert any("retention" in message for message in adapter.messages)


def test_an_unmapped_record_leaves_the_program_unchanged(
    line_utils, context, source_text, role
):
    adapter = RestartStageAdapter(
        line_utils,
        context=dataclasses.replace(context, record_name="NOT-MAPPED"),
        mapping_repository=_Mapping(role.table_name),
    )
    assert adapter.compose(source_text) == source_text


#
# Determinism
#
def test_running_twice_produces_identical_output(adapter, source_text):
    first = adapter.compose(source_text)
    assert adapter.compose(first) == first


def test_messages_do_not_accumulate_across_runs(adapter, source_text):
    adapter.compose(source_text)
    count = len(adapter.messages)
    adapter.compose(source_text)
    assert len(adapter.messages) == count
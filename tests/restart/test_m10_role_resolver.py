# LOCATION: tests/restart/test_m10_role_resolver.py
# ACTION: CREATE NEW FILE
"""M10 - RestartRoleResolver.

    contract    - three authorities, one role
    refusal     - any missing authority refuses the WHOLE role
    determinism - same inputs, same role

WHY THE FAKE DCLGEN IS BUILT BY INTROSPECTION

Hand-listing the role's fields in the test would be a second
declaration of the role. When M2 gains a column the test would still
pass while the resolver silently left it empty. The fake is generated
from dataclasses.fields(RestartDclgenRole), so a new field fails here
first.
"""

from __future__ import annotations

import dataclasses
import types

import pytest

from catalogs.restart_paragraph_catalog import RestartDclgenRole
from converter.resolvers.restart_role_resolver import (
    SHEET_AUTHORITY_FIELD,
    SITE_AUTHORITY_FIELD,
    RestartRoleResolver,
)

RECORD = "RESTART-REC"
SHEET_TABLE = "SITE_RESTART_TABLE"
DCLGEN_TABLE = "SITE_RESTART_STRUCTURE"
RETENTION = 7


class _Mapping:
    """Minimal stand-in for MappingRepository."""

    def __init__(self, table: str = SHEET_TABLE) -> None:
        self.table = table

    def db2_table_for_record(self, record_name: str) -> str:
        return self.table if record_name == RECORD else ""

    def has_table(self, table_name: str) -> bool:
        return bool(self.table) and table_name.upper() == self.table.upper()


def _dclgen(**overrides):
    """A complete DCLGEN role, generated from the role's own fields."""
    values = {}
    for field in dataclasses.fields(RestartDclgenRole):
        if field.name == SITE_AUTHORITY_FIELD:
            continue
        if field.name == SHEET_AUTHORITY_FIELD:
            values[field.name] = DCLGEN_TABLE
            continue
        values[field.name] = f"SITE-{field.name.upper()}"
    # The resolved metadata spells this one differently.
    values["host_record_name"] = values.pop("host_record")
    values.update(overrides)
    return types.SimpleNamespace(**values)


@pytest.fixture
def resolver():
    return RestartRoleResolver(mapping_repository=_Mapping())


@pytest.fixture
def resolved(resolver):
    role, messages = resolver.resolve(
        dclgen_role=_dclgen(),
        record_name=RECORD,
        retention_days=RETENTION,
    )
    return role, messages


#
# Contract
#
def test_a_complete_input_builds_a_role(resolved):
    role, _messages = resolved
    assert isinstance(role, RestartDclgenRole)


def test_every_declared_field_is_filled(resolved):
    role, _messages = resolved
    for field in dataclasses.fields(RestartDclgenRole):
        value = getattr(role, field.name)
        assert value not in ("", 0, None), field.name


def test_the_table_name_comes_from_sheet_mapping(resolved):
    """The DCLGEN member names something else on purpose."""
    role, _messages = resolved
    assert role.table_name == SHEET_TABLE
    assert role.table_name != DCLGEN_TABLE


def test_the_disagreement_is_reported(resolved):
    _role, messages = resolved
    assert any(DCLGEN_TABLE in message for message in messages)
    assert any("authority" in message for message in messages)


def test_the_columns_come_from_the_dclgen(resolved):
    role, _messages = resolved
    assert role.program_column == "SITE-PROGRAM_COLUMN"
    assert role.payload_group == "SITE-PAYLOAD_GROUP"


def test_the_host_record_alias_is_translated(resolved):
    role, _messages = resolved
    assert role.host_record == "SITE-HOST_RECORD"


def test_the_retention_comes_from_site_metadata(resolved):
    role, _messages = resolved
    assert role.retention_days == RETENTION


def test_a_confirmed_hint_is_accepted(resolver):
    role, messages = resolver.resolve(
        dclgen_role=_dclgen(),
        table_hint=SHEET_TABLE,
        retention_days=RETENTION,
    )
    assert role.table_name == SHEET_TABLE
    assert any("confirmed" in message for message in messages)


#
# Refusal
#
def test_a_missing_dclgen_refuses(resolver):
    role, messages = resolver.resolve(dclgen_role=None, retention_days=RETENTION)
    assert role is None
    assert messages


def test_no_mapping_repository_refuses():
    role, messages = RestartRoleResolver().resolve(
        dclgen_role=_dclgen(), record_name=RECORD, retention_days=RETENTION
    )
    assert role is None
    assert any("Sheet Mapping" in message for message in messages)


def test_an_unmapped_record_refuses(resolver):
    role, messages = resolver.resolve(
        dclgen_role=_dclgen(), record_name="NOT-MAPPED", retention_days=RETENTION
    )
    assert role is None
    assert any("names no DB2 table" in message for message in messages)


def test_no_retention_refuses(resolver):
    """Principle C: the generator never picks a number."""
    role, messages = resolver.resolve(
        dclgen_role=_dclgen(), record_name=RECORD, retention_days=0
    )
    assert role is None
    assert any("retention" in message for message in messages)


def test_one_empty_dclgen_entry_refuses_the_whole_role(resolver):
    role, messages = resolver.resolve(
        dclgen_role=_dclgen(payload_len_field=""),
        record_name=RECORD,
        retention_days=RETENTION,
    )
    assert role is None
    assert any("payload_len_field" in message for message in messages)


def test_a_refusal_never_returns_a_partial_role(resolver):
    role, _messages = resolver.resolve(
        dclgen_role=_dclgen(status_field=""),
        record_name=RECORD,
        retention_days=RETENTION,
    )
    assert role is None


#
# Determinism
#
def test_resolving_twice_produces_an_equal_role(resolver):
    first, _ = resolver.resolve(
        dclgen_role=_dclgen(), record_name=RECORD, retention_days=RETENTION
    )
    second, _ = resolver.resolve(
        dclgen_role=_dclgen(), record_name=RECORD, retention_days=RETENTION
    )
    assert first == second


def test_the_catalogued_role_is_never_used():
    """M10 exists to stop a catalogued name reaching generated SQL."""
    import converter.resolvers.restart_role_resolver as module

    assert not hasattr(module, "production_restart_role")
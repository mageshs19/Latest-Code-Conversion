"""Fixtures for the cursor-spec builder unit-test package."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from converter.generators.db2_infrastructure.spec_builder.spec_relationship_policy import (
    SpecRelationshipPolicy,
)
from converter.generators.db2_infrastructure.spec_builder.spec_select_augmenter import (
    SpecSelectAugmenter,
)


CHILD_RECORD = "VMBFAS"
PARENT_RECORD = "VMBSIAS"
CHILD_TABLE = "DZBFASTV"
PARENT_TABLE = "DZBSIASTV"
KEY_COLUMN = "KY_SIFORM"
ORDER_COLUMN = "NR_ID_479BFAS"


class StubHostVariableResolver:
    """Returns deterministic DCLGEN host references."""

    @staticmethod
    def host_references_for_columns(
        table_name: str,
        columns: list[str],
    ) -> list[str]:
        group = f"DCL{str(table_name).upper()}"
        return [
            f": {group}.{str(column).replace('_', '-')}"
            for column in columns
        ]


class StubLineUtils:
    """Only the reporter contract is needed."""

    @staticmethod
    def normalize_include_name(table_name: str) -> str:
        return str(table_name or "").strip().upper()


class StubWhereBuilder:
    """Keeps relationship-policy tests independent of predicate parsing."""

    messages: list[str]

    def __init__(self) -> None:
        self.messages = []

    @staticmethod
    def predicates(_conditions) -> list[str]:
        return [
            "KY_SIFORM = : DCLDZBSIASTV.KY-SIFORM",
        ]


@dataclass
class StubRelationship:
    parent_record: str = PARENT_RECORD
    conditions: list[object] | None = None

    def __post_init__(self) -> None:
        if self.conditions is None:
            self.conditions = [object()]


class StubRelationshipResolver:
    """Returns a relationship with one parent-side predicate."""

    @staticmethod
    def resolve_for_child_record(_record: str) -> StubRelationship:
        return StubRelationship()


@pytest.fixture
def owner_without_line_utils():
    """Minimum owner used to prove reporter creation is lazy."""
    return SimpleNamespace(
        host_variable_resolver=StubHostVariableResolver(),
        relationship_resolver=StubRelationshipResolver(),
    )


@pytest.fixture
def owner_with_line_utils():
    """Owner used by include-name/reporting tests."""
    return SimpleNamespace(
        host_variable_resolver=StubHostVariableResolver(),
        relationship_resolver=StubRelationshipResolver(),
        line_utils=StubLineUtils(),
    )


@pytest.fixture
def relationship_policy():
    """Policy with deterministic relationship and predicate collaborators."""
    return SpecRelationshipPolicy(
        relationship_resolver=StubRelationshipResolver(),
        where_builder=StubWhereBuilder(),
    )


@pytest.fixture
def augmenter():
    """Actual select augmenter with only required dependencies."""
    return SpecSelectAugmenter(
        host_variable_resolver=StubHostVariableResolver(),
        where_builder=StubWhereBuilder(),
    )
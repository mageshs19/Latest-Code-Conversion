# LOCATION: tests/cursor_where/test_join_resolver.py
# ACTION: CREATE NEW FILE
"""CursorJoinResolver - predicate resolution.

    D-1  fallback constants were never imported      -> NameError
    D-2  host_for_column() is not a resolver method  -> AttributeError
    D-3  fallback built a self-referential predicate -> meaningless filter
    D-4  only resolve() was tolerated on the facade  -> AttributeError
    D-5  condition.child_table read without getattr  -> AttributeError
"""

from __future__ import annotations

from converter.resolvers.cursor_join_resolver import CursorJoinResolver
from rules.cursor_declaration_rules import EMIT_DRIVING_KEY_PREDICATE
from tests.cursor_where._support import (
    CHILD_GROUP,
    CHILD_RECORD,
    ColumnNameResolver,
    Condition,
    EXPECTED_PREDICATE,
    FOREIGN_COLUMN,
    HostVariableResolver,
    LegacyRelationshipResolver,
    PARENT_GROUP,
    PartialCondition,
    RelationshipResolver,
    Resolution,
    join,
)


# ---- D-1
def test_driving_key_fallback_constants_are_importable():
    """The fallback used names it never imported and raised NameError."""
    assert EMIT_DRIVING_KEY_PREDICATE in (True, False)


def test_fallback_path_never_raises_name_error():
    """D-1 is about NOT RAISING.

    The earlier form asserted `== [] or True`, which could not fail
    whatever came back.
    """
    resolver = join(RelationshipResolver(resolution=None))
    assert isinstance(resolver.where_conditions(CHILD_RECORD), list)


# ---- D-2
def test_resolver_never_calls_a_missing_host_method():
    """host_for_command/host_for_column do not exist on the resolver."""
    hosts = HostVariableResolver()
    assert not hasattr(hosts, "host_for_column")

    resolver = CursorJoinResolver(
        relationship_resolver=RelationshipResolver(
            resolution=Resolution(conditions=[])
        ),
        column_name_resolver=ColumnNameResolver(),
        host_variable_resolver=hosts,
    )
    # Must complete without AttributeError.
    resolver.where_conditions(CHILD_RECORD)


# ---- D-3
def test_driving_key_predicate_targets_the_parent_group():
    resolver = join(RelationshipResolver(resolution=Resolution(conditions=[])))
    assert resolver.where_conditions(CHILD_RECORD) == [EXPECTED_PREDICATE]


def test_driving_key_predicate_is_never_self_referential():
    """'KY_SIFORM = :DCLDZBFASTV.KY-SIFORM' is a filter, not a join."""
    resolver = join(RelationshipResolver(resolution=Resolution(conditions=[])))
    for predicate in resolver.where_conditions(CHILD_RECORD):
        assert CHILD_GROUP not in predicate


def test_no_parent_side_refuses_instead_of_guessing():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(conditions=[], parent_table="")
        )
    )
    assert resolver.where_conditions(CHILD_RECORD) == []
    assert any("WHERE not generated" in m for m in resolver.diagnostics)


def test_caller_supplied_driving_host_is_honoured():
    """The LRF path keyword can supply the parent host directly."""
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(conditions=[], parent_table="")
        )
    )
    conditions = resolver.where_conditions(
        CHILD_RECORD,
        driving_host_reference=f":{PARENT_GROUP}.KY-SIFORM",
    )
    assert conditions == [EXPECTED_PREDICATE]


# ---- D-4
def test_legacy_facade_method_name_is_tolerated():
    resolver = CursorJoinResolver(
        relationship_resolver=LegacyRelationshipResolver(
            resolution=Resolution(conditions=[Condition()])
        ),
        column_name_resolver=ColumnNameResolver(),
        host_variable_resolver=HostVariableResolver(),
    )
    assert resolver.where_conditions(CHILD_RECORD) == [EXPECTED_PREDICATE]


# ---- D-5
def test_a_condition_without_child_table_is_skipped_not_fatal():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(conditions=[PartialCondition()])
        )
    )
    # Falls through to the driving key rather than raising.
    assert resolver.where_conditions(CHILD_RECORD) == [EXPECTED_PREDICATE]
    assert any("is not a column of" in m for m in resolver.diagnostics)


# ---- Attempt 1 wins when it can
def test_relationship_predicate_is_preferred_over_the_fallback():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(
                conditions=[Condition(child_column=FOREIGN_COLUMN)]
            )
        )
    )
    conditions = resolver.where_conditions(CHILD_RECORD)
    assert conditions == [f"{FOREIGN_COLUMN} = :{PARENT_GROUP}.KY-SIFORM"]


def test_duplicate_predicates_are_collapsed():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(conditions=[Condition(), Condition()])
        )
    )
    assert len(resolver.where_conditions(CHILD_RECORD)) == 1


def test_a_predicate_without_a_parent_host_is_skipped_and_reported():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(
                conditions=[Condition(parent_host_reference="NO-GROUP-HERE")],
                parent_table="",
            )
        )
    )
    assert resolver.where_conditions(CHILD_RECORD) == []
    assert any("host variable" in m for m in resolver.diagnostics)


def test_an_empty_record_name_returns_no_predicate():
    assert join(RelationshipResolver()).where_conditions("") == []


def test_diagnostics_are_reset_between_calls():
    resolver = join(
        RelationshipResolver(
            resolution=Resolution(conditions=[], parent_table="")
        )
    )
    resolver.where_conditions(CHILD_RECORD)
    first = len(resolver.diagnostics)

    resolver.where_conditions(CHILD_RECORD)
    assert len(resolver.diagnostics) == first
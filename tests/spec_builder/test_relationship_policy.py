"""Tests for safe cursor relationship predicate generation."""

from __future__ import annotations


def test_parent_not_navigated_returns_no_predicates_and_reports_reason(
    relationship_policy,
):
    predicates = relationship_policy.where_conditions(
        record="VMBFAS",
        navigated_records=set(),
        lrf_cursors={},
    )

    assert predicates == []
    assert any(
        "never positions" in message
        for message in relationship_policy.messages
    )


def test_lrf_marker_does_not_add_duplicate_predicates(
    relationship_policy,
):
    predicates = relationship_policy.where_conditions(
        record="VMBFAS",
        navigated_records={"VMBSIAS"},
        lrf_cursors={"VMBFAS": object()},
    )

    assert predicates == [
        "KY_SIFORM = : DCLDZBSIASTV.KY-SIFORM",
    ]
    assert any(
        "no duplicate was added" in message
        for message in relationship_policy.messages
    )
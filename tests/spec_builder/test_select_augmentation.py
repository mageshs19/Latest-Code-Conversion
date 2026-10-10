"""Tests for cross-spec SELECT-column augmentation."""

from __future__ import annotations


def test_child_order_by_key_is_added_to_select(augmenter):
    spec = {
        "cursor_name": "DZBFASC1",
        "table_name": "DZBFASTV",
        "select_columns": ["DA_CPTAFS_479BFAS"],
        "order_by_columns": ["NR_ID_479BFAS ASC"],
        "where_conditions": [],
        "host_variables": [],
    }

    augmenter.augment([spec])

    assert spec["select_columns"] == [
        "DA_CPTAFS_479BFAS",
        "NR_ID_479BFAS",
    ]


def test_order_by_key_is_not_added_twice(augmenter):
    spec = {
        "cursor_name": "DZBFASC1",
        "table_name": "DZBFASTV",
        "select_columns": [
            "DA_CPTAFS_479BFAS",
            "NR_ID_479BFAS",
        ],
        "order_by_columns": ["NR_ID_479BFAS DESC"],
        "where_conditions": [],
        "host_variables": [],
    }

    augmenter.augment([spec])

    assert spec["select_columns"].count("NR_ID_479BFAS") == 1


def test_host_variables_are_resynchronised_after_augmentation(augmenter):
    spec = {
        "cursor_name": "DZBFASC1",
        "table_name": "DZBFASTV",
        "select_columns": ["DA_CPTAFS_479BFAS"],
        "order_by_columns": ["NR_ID_479BFAS ASC"],
        "where_conditions": [],
        "host_variables": [],
    }

    augmenter.augment([spec])

    assert len(spec["host_variables"]) == len(spec["select_columns"])
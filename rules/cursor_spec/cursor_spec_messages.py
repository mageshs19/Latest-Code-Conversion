# LOCATION: rules/cursor_spec/cursor_spec_messages.py
# ACTION: CREATE NEW FILE
"""Cursor specification diagnostics. ONE dictionary literal."""

from __future__ import annotations

SPEC_MESSAGES = {
    "no_table": (
        "DB2 infrastructure: cursor {cursor} has no resolved DB2 table "
        "for record {record}."
    ),
    "no_select_columns": (
        "DB2 infrastructure: cursor {cursor} has no resolved SELECT "
        "columns for record {record}."
    ),
    "no_host_variables": (
        "DB2 infrastructure: cursor {cursor} has no resolved FETCH host "
        "variables for record {record}."
    ),
    "parent_not_navigated": (
        "Cursor spec: {record} resolves a parent {parent} that this "
        "program never positions; WHERE not generated because the parent "
        "host variables would never be populated."
    ),
    "lrf_where_already_present": (
        "Cursor spec: {record} is LRF-expanded and already carries "
        "{count} relationship predicate(s); no duplicate was added."
    ),
    "parent_group_unresolved": (
        "Cursor spec: could not resolve a DB2 table for host group "
        "{group}; the parent SELECT was not augmented for {column}."
    ),
    "select_augmented": (
        "Cursor spec: added {column} to the {cursor} SELECT so the "
        "{reason} can read fetched data."
    ),
}

__all__ = ["SPEC_MESSAGES"]
# LOCATION: rules/cursor_declaration_messages.py
# ACTION: CREATE NEW FILE
"""Diagnostic catalogues for cursor declaration, join and ORDER BY.

ONE dictionary literal each. Post-hoc "MESSAGES[key] = ..." assignments
are what let a duplicate QUERYNO block hide in this module's ancestor.

KEY-SPACE CONTRACT
------------------
CursorOrderByResolver merges ORDER_BY_KEY_MESSAGES with
CURSOR_ORDER_BY_MESSAGES into one catalogue. The two key sets MUST stay
DISJOINT - a collision would silently shadow a diagnostic.
tests/test_rules_no_duplicate_constants.py asserts that.

CORRECTION 22 - two refusals had no message key.

cursor_declare/declare_refusal.py logs "missing_cursor_name" and
"missing_table". Neither existed, so _message() returned "" and both
refusals stayed SILENT - a cursor vanished from the program and the
conversion report did not say why. That is precisely the gap
CORRECTION 3 was supposed to close.
"""

from __future__ import annotations

DECLARATION_MESSAGES = {
    "declared_cursor": (
        "Cursor declaration: declared {cursor} on {table} "
        "with {count} column(s), QUERYNO {queryno}."
    ),
    "where_declared": (
        "Cursor declaration: {cursor} qualified by {count} predicate(s)."
    ),
    "join_key_unresolved": (
        "Cursor declaration: join key {column} is not a column of {table}; "
        "cursor {cursor} was not declared."
    ),
    "select_all_refused": (
        "Cursor declaration: {cursor} has no explicit column list; "
        "SELECT * refused."
    ),
    # ---- spec-level refusals. See CORRECTION 22.
    "missing_cursor_name": (
        "Cursor declaration: refused a spec with no cursor name; "
        "nothing was declared."
    ),
    "missing_table": (
        "Cursor declaration: no DB2 table on the spec for {cursor}; "
        "cursor was not declared."
    ),
    # ---- ORDER BY
    "order_by_kept": (
        "Cursor declaration: {cursor} keeps ORDER BY on {count} column(s)."
    ),
    "order_by_none": (
        "Cursor declaration: {cursor} has no resolvable ORDER BY; row "
        "sequence is whatever DB2 chooses. Confirm the extract does not "
        "depend on order."
    ),
    "order_by_column_dropped": (
        "Cursor declaration: dropped ORDER BY entry '{entry}' from "
        "{cursor}; {column} is not a column of {table}."
    ),
    "order_by_duplicate_dropped": (
        "Cursor declaration: dropped duplicate ORDER BY entry '{entry}' "
        "from {cursor}; {column} is already ordered. One column cannot "
        "carry two directions."
    ),
    "order_by_all_dropped": (
        "Cursor declaration: every ORDER BY entry for {cursor} was "
        "rejected; the clause is omitted and rows return in DB2 sequence."
    ),
    # Retained for the legacy path, reachable only when
    # ENFORCE_ORDER_BY_RETENTION is switched off for a diff.
    "order_by_removed": (
        "Cursor declaration: removed ORDER BY from parent cursor {cursor}."
    ),
    # ---- ownership guard stand-downs
    #
    # A guard that stands down in SILENCE is how an unguarded builder
    # reached production and stayed invisible across several runs.
    "ownership_no_resolver": (
        "Cursor declaration: no column resolver supplied for {table}; "
        "the WHERE and ORDER BY ownership guards stood down."
    ),
    "ownership_unavailable": (
        "Cursor declaration: no DCLGEN column list resolved for {table}; "
        "the WHERE and ORDER BY ownership guards stood down."
    ),
    "ownership_lookup_failed": (
        "Cursor declaration: column lookup failed for {table} ({reason}); "
        "the ownership guards stood down."
    ),
}

SWEEP_CURSOR_NO_WHERE_TEMPLATE = (
    "Cursor declaration: {cursor} on {table} declared WITHOUT a WHERE "
    "clause (root/sweep access). Confirm this is a full-table read."
)

JOIN_MESSAGES = {
    "no_resolution": (
        "Cursor join: no relationship resolution for {record}; "
        "attempting driving-key qualification."
    ),
    "no_fk_rows": (
        "Cursor join: {record} has no foreign-key row in the Sheet "
        "Mapping; attempting driving-key qualification."
    ),
    "unowned_column": (
        "Cursor join: {column} is not a column of {table}; "
        "predicate skipped."
    ),
    "no_parent_host": (
        "Cursor join: no DCLGEN host variable for parent column "
        "{column}; predicate skipped."
    ),
    "no_parent_side": (
        "Cursor join: {record} has no resolvable parent table and no "
        "driving host was supplied; WHERE not generated."
    ),
    "no_child_table": (
        "Cursor join: no DB2 table for {record}; WHERE not generated."
    ),
    # NOTE - currently UNCONSUMED. The CursorJoinResolver patch that
    # would emit it was withdrawn once the manual reference proved the
    # parent-suffixed FK columns ARE columns of the child table.
    # tools/rules_probe.py will report it; keep or delete deliberately.
    "no_owned_driving_key": (
        "Cursor join: no driving-key column of {table} survived the "
        "ownership test; WHERE not generated."
    ),
    "sweep": (
        "Cursor join: {record} resolves to an unqualified root/sweep "
        "read; no WHERE generated."
    ),
}

CURSOR_ORDER_BY_MESSAGES = {
    "resolved": (
        "Cursor ORDER BY: {record} resolved {count} column(s) from the "
        "{source}: {columns}."
    ),
    "empty_no_primary_key": (
        "Cursor ORDER BY: {record} has no primary-key column in the "
        "Sheet Mapping, so no ORDER BY can be inferred. The cursor will "
        "return rows in whatever sequence DB2 chooses. Flag the key "
        "column in the Sheet Mapping, or supply the IDMS schema so the "
        "set sort key can be used."
    ),
    "empty_all_foreign": (
        "Cursor ORDER BY: every primary-key column of {record} is also "
        "a foreign key, so none survived; no ORDER BY inferred."
    ),
    "dropped_not_a_column": (
        "Cursor ORDER BY: dropped '{column}' for {record}; it is not a "
        "DB2 column of that record."
    ),
    "dropped_audit": (
        "Cursor ORDER BY: dropped audit column '{column}' for {record}."
    ),
    "dropped_sentinel": (
        "Cursor ORDER BY: dropped '{column}' for {record}; it is a COBOL "
        "placeholder, not a DB2 column."
    ),
    "none": (
        "Cursor ORDER BY: {record} yielded no orderable column; the "
        "cursor returns rows in whatever sequence DB2 chooses."
    ),
    "direction_disabled": (
        "Cursor ORDER BY: direction inference is OFF; {count} column(s) "
        "default to {direction}."
    ),
    "calc_dn_no_order_by": (
        "Cursor ORDER BY: {record} is CALC DN (Duplicate Not Allowed); "
        "no ORDER BY clause generated."
    ),
    "access_type_calc_dl_asc": (
        "Cursor ORDER BY: {record} is CALC DL with seq.no field and "
        "{count} primary key(s); ORDER BY direction set to ASC."
    ),
    "access_type_via_desc": (
        "Cursor ORDER BY: {record} is VIA accessed with seq.no field and "
        "single primary key; ORDER BY direction set to DESC."
    ),
}

ORDER_BY_KEY_MESSAGES = {
    "single_key": (
        "Cursor ORDER BY: {record} already orders on a single column: "
        "{columns}."
    ),
    "narrowed_to_identity": (
        "Cursor ORDER BY: {record} has a {total}-part composite key; "
        "narrowed to {kept} identity key column(s): {columns}. A "
        "surrogate key is unique on its own, so the wider key adds sort "
        "cost without adding determinism; row sequence is unchanged."
    ),
    "kept_composite": (
        "Cursor ORDER BY: {record} has no identity-style key column; "
        "ordering by the full {total}-part composite key so the cursor "
        "remains deterministic."
    ),
    "kept_composite_child": (
        "Cursor ORDER BY: {record} is a child cursor and identity "
        "narrowing is disabled for children; {total} column(s) retained."
    ),
}

__all__ = [
    "DECLARATION_MESSAGES", "SWEEP_CURSOR_NO_WHERE_TEMPLATE",
    "JOIN_MESSAGES", "CURSOR_ORDER_BY_MESSAGES", "ORDER_BY_KEY_MESSAGES",
]
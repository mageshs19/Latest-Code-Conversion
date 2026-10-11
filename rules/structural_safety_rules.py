# LOCATION: rules/structural_safety_rules.py
# ACTION: REPLACE ENTIRE FILE

"""Structural safety constants.

CONSTANTS ONLY. No regex, no parser logic, no service logic, and no
program, record, table, DCLGEN, cursor or host variable name.

CORRECTION 1 - the generated banner reached WORKING-STORAGE as a
               data description
-----------------------------------------------------------------
The output carried

    000870     DB2 GENERATED WORKING STORAGE
    000880 01  WS-DB2-GENERATED.

The first line is not a data description and will not compile.

THE FIRST DIAGNOSIS WAS WRONG, AND IS RECORDED HERE SO IT IS NOT
REPEATED. The theory was that these constants are comment BODIES that
the emitter writes verbatim, so the column-7 indicator had to be part
of the value. Both markers were therefore wrapped in
COMMENT_MARKER_TEMPLATE. The output did not change, which disproved it.

The emitter does not write them verbatim. It calls

    converter/composers/counter_declaration/counter_line_factory.py
        def comment(self, template, body):
            text  = str(body or "").lstrip("*").strip()
            built = self.fixed_format.build_or_none(left, "*", text, right)

which already OWNS the indicator and strips any leading '*' from the
title. Wrapping the value simply had the star stripped straight back
off. A title carrying its own indicator is also a layering error: this
module owns shape and policy, not rendering.

The real fault was one level further down, in
converter/services/fixed_format_line_service.py::build(), which
discarded the indicator whenever BOTH sequence areas were empty - the
normal case for any line built before the final resequencer runs. That
is fixed there, as CORRECTION 5 of that module.

These values are therefore plain TITLES. The renderer supplies the
indicator.

CORRECTION 2 - the same literal was declared in two layers
-----------------------------------------------------------
"DB2 GENERATED WORKING STORAGE" existed here AND in
catalogs/output_sections.py. catalogs/ is the layer that owns labels;
this module owns the SHAPE that wraps them. The titles are imported.

The precedent is rules/sql_error_rules.py, which re-exports
DECLARE_SQL_LOCATION_FIELD from the same catalogue rather than
re-declaring it.

CORRECTION 3 - a marker overflowed the body window
----------------------------------------------------
ORPHANED_RECORD_MARKER_TEMPLATE rendered as

    *DB2-KEEP: VMBD205I is an IDMS record with no DB2 layout after
    conversion - re-map this reference manually.

106 characters against a 65-column body window (columns 8-72). The
emitted line ran past column 72 into the right sequence area. The text
is shortened to fit the worst-case record name, and MARKER_BODY_WIDTH
is published so the emitter can assert it.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

from catalogs.output_sections import (
    DB2_GENERATED_ROW_COUNTERS_MARKER,
    DB2_GENERATED_WORKING_STORAGE_MARKER,
)

# =====================================================================
# Fixed-format geometry
# =====================================================================
# Columns 8-72. A generated comment body must fit this window; the
# leading indicator occupies column 7 and does not consume it.
MARKER_BODY_WIDTH = 65

# Refuse to emit a generated line wider than the window rather than let
# it run into the right sequence area.
ENFORCE_MARKER_BODY_WIDTH = True

# =====================================================================
# Condition integrity
# =====================================================================
ENFORCE_CONDITION_INTEGRITY = True
CONDITION_SCAN_LIMIT = 24

CONDITION_CONTINUATION_TOKENS = (
    "AND",
    "OR",
    "NOT",
)

CONDITION_TERMINATING_VERBS = (
    "ACCEPT", "ADD", "CALL", "CLOSE", "COMPUTE", "CONTINUE", "DELETE",
    "DISPLAY", "DIVIDE", "ELSE", "END-IF", "EVALUATE", "EXEC", "EXIT",
    "GO", "GOBACK", "IF", "INITIALIZE", "INSPECT", "MOVE", "MULTIPLY",
    "OPEN", "PERFORM", "READ", "RETURN", "REWRITE", "SEARCH", "SET",
    "STOP", "STRING", "SUBTRACT", "UNSTRING", "WRITE",
)

# =====================================================================
# Orphaned record guard
# =====================================================================
ENFORCE_ORPHANED_RECORD_GUARD = True

# These two DO carry their own '*': they are whole comment LINES passed
# to a plain line writer, not titles handed to comment(). Measured
# against MARKER_BODY_WIDTH with an eleven-character DCLGEN group name:
#     *DB2-KEEP: DCLDZBFARTV has no DB2 layout after conversion.
#     = 57 columns.
ORPHANED_RECORD_MARKER_TEMPLATE = (
    "*DB2-KEEP: {record} has no DB2 layout after conversion."
)

# Emitted on the line below when the composer wants the full advice.
# Separate constant so neither line can overflow.
ORPHANED_RECORD_MARKER_DETAIL = (
    "*DB2-KEEP: re-map this reference manually."
)

ORPHANED_LINE_PREFIX = "*DB2-KEEP "

# =====================================================================
# Unreachable statement guard
# =====================================================================
ENFORCE_UNREACHABLE_STATEMENT_GUARD = True

# 63 columns. Fits the window.
UNREACHABLE_MARKER = (
    "*DB2-KEEP: statement follows a paragraph EXIT and is unreachable."
)

PARAGRAPH_EXIT_WORDS = (
    "EXIT",
    "GOBACK",
    "STOP RUN",
)

MAX_UNREACHABLE_STATEMENTS = 3

# =====================================================================
# Generated field and counter groups
# =====================================================================
ENFORCE_SAFE_COUNTER_GROUP = True
PREFER_GENERATED_COUNTER_GROUP = True

UNIFY_GENERATED_FIELD_GROUP = True

PREFERRED_WORK_GROUP_NAMES = (
    "WS-TE-WORK",
)

GENERATED_FIELD_GROUP_NAME = "WS-DB2-GENERATED"
GENERATED_FIELD_GROUP_ALIASES = (
    "WS-DB2-GENERATED",
    "WS-DB2-COUNTERS",
)
GENERATED_FIELD_GROUP_TEMPLATE = "01  {name}."

# A TITLE, not a comment line. generated_field_anchor.py renders it with
# counter_line_factory.comment(), which supplies the column-7 indicator.
# Do not prefix a '*' here - see CORRECTION 1.
GENERATED_FIELD_GROUP_MARKER = DB2_GENERATED_WORKING_STORAGE_MARKER

GENERATED_FIELD_CHILD_INDENT = "    "
GENERATED_FIELD_CHILD_LEVEL = "10"

GENERATED_COUNTER_GROUP_NAME = "WS-DB2-COUNTERS"
GENERATED_COUNTER_GROUP_TEMPLATE = "01  {name}."

# Same contract as GENERATED_FIELD_GROUP_MARKER.
GENERATED_COUNTER_GROUP_MARKER = DB2_GENERATED_ROW_COUNTERS_MARKER

GENERATED_COUNTER_CHILD_INDENT = "    "

# =====================================================================
# Record layout detection
# =====================================================================
RECORD_LAYOUT_VERBS = (
    "WRITE",
    "READ",
    "REWRITE",
    "RELEASE",
    "RETURN",
)

# =====================================================================
# Diagnostics - ONE dictionary literal
# =====================================================================
STRUCTURAL_SAFETY_MESSAGES = {
    "extraction_refused": (
        "Structural safety: output write extraction refused - the guard "
        "condition spans {count} lines and cannot be split."
    ),
    "orphaned_record_commented": (
        "Structural safety: commented whole-record reference to {record}; "
        "the IDMS layout no longer exists."
    ),
    "unreachable_commented": (
        "Structural safety: commented {count} unreachable statement(s) "
        "after a paragraph EXIT."
    ),
    "unreachable_aborted": (
        "Structural safety: unreachable-statement guard matched {count} "
        "lines, above the limit of {limit}; the pass was reverted and no "
        "line was commented."
    ),
    "counter_group_created": (
        "Structural safety: created {group} for generated row counters."
    ),
    "counter_group_reused": (
        "Structural safety: reused work group {group} for row counters."
    ),
    "counter_group_rejected": (
        "Structural safety: {group} is a record layout; counters were not "
        "declared inside it."
    ),
    "field_group_reused": (
        "Structural safety: generated fields share work group {group}."
    ),
    "field_group_created": (
        "Structural safety: created {group} for generated working-storage "
        "fields."
    ),
    "field_group_childless": (
        "Structural safety: {group} declares no subordinate entry and "
        "cannot take a generated field."
    ),
    "extraction_refused_block": (
        "Structural safety: output write extraction skipped for the block "
        "in {source}; its guard condition spans {count} lines and cannot "
        "be split. Other candidates were still considered."
    ),
    "field_group_no_section": (
        "Structural safety: no WORKING-STORAGE SECTION found; no "
        "generated field group was created."
    ),
    "extraction_condition_unresolved": (
        "Structural safety: the guard condition in {source} could not be "
        "resolved; the output write block was left in place."
    ),
    "marker_overflow": (
        "Structural safety: generated comment needs {length} columns, "
        "only {width} are available; the marker was not emitted: {body}"
    ),
    "orphaned_record_referenced": (
        "Structural safety: {record} is referenced {count} time(s) but "
        "declared nowhere; REPORTED, not commented. First at line "
        "{line}: {body}"
    ),
}

__all__ = [
    "CONDITION_CONTINUATION_TOKENS",
    "CONDITION_SCAN_LIMIT",
    "CONDITION_TERMINATING_VERBS",
    "ENFORCE_CONDITION_INTEGRITY",
    "ENFORCE_MARKER_BODY_WIDTH",
    "ENFORCE_ORPHANED_RECORD_GUARD",
    "ENFORCE_SAFE_COUNTER_GROUP",
    "ENFORCE_UNREACHABLE_STATEMENT_GUARD",
    "GENERATED_COUNTER_CHILD_INDENT",
    "GENERATED_COUNTER_GROUP_MARKER",
    "GENERATED_COUNTER_GROUP_NAME",
    "GENERATED_COUNTER_GROUP_TEMPLATE",
    "GENERATED_FIELD_CHILD_INDENT",
    "GENERATED_FIELD_CHILD_LEVEL",
    "GENERATED_FIELD_GROUP_ALIASES",
    "GENERATED_FIELD_GROUP_MARKER",
    "GENERATED_FIELD_GROUP_NAME",
    "GENERATED_FIELD_GROUP_TEMPLATE",
    "MARKER_BODY_WIDTH",
    "MAX_UNREACHABLE_STATEMENTS",
    "ORPHANED_LINE_PREFIX",
    "ORPHANED_RECORD_MARKER_DETAIL",
    "ORPHANED_RECORD_MARKER_TEMPLATE",
    "PARAGRAPH_EXIT_WORDS",
    "PREFERRED_WORK_GROUP_NAMES",
    "PREFER_GENERATED_COUNTER_GROUP",
    "RECORD_LAYOUT_VERBS",
    "STRUCTURAL_SAFETY_MESSAGES",
    "UNIFY_GENERATED_FIELD_GROUP",
    "UNREACHABLE_MARKER",
]
from __future__ import annotations

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

ENFORCE_ORPHANED_RECORD_GUARD = True

ORPHANED_RECORD_MARKER_TEMPLATE = (
    "*DB2-KEEP: {record} is an IDMS record with no DB2 layout after "
    "conversion - re-map this reference manually."
)
ORPHANED_LINE_PREFIX = "*DB2-KEEP "

ENFORCE_UNREACHABLE_STATEMENT_GUARD = True

UNREACHABLE_MARKER = (
    "*DB2-KEEP: statement follows a paragraph EXIT and is unreachable."
)

PARAGRAPH_EXIT_WORDS = (
    "EXIT",
    "GOBACK",
    "STOP RUN",
)

MAX_UNREACHABLE_STATEMENTS = 3

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
GENERATED_FIELD_GROUP_MARKER = "DB2 GENERATED WORKING STORAGE"
GENERATED_FIELD_CHILD_INDENT = "    "
GENERATED_FIELD_CHILD_LEVEL = "10"

GENERATED_COUNTER_GROUP_NAME = "WS-DB2-COUNTERS"
GENERATED_COUNTER_GROUP_TEMPLATE = "01  {name}."
GENERATED_COUNTER_GROUP_MARKER = "DB2 GENERATED ROW COUNTERS"
GENERATED_COUNTER_CHILD_INDENT = "    "

RECORD_LAYOUT_VERBS = (
    "WRITE",
    "READ",
    "REWRITE",
    "RELEASE",
    "RETURN",
)

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
}

__all__ = [
    "CONDITION_CONTINUATION_TOKENS",
    "CONDITION_SCAN_LIMIT",
    "CONDITION_TERMINATING_VERBS",
    "ENFORCE_CONDITION_INTEGRITY",
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
    "MAX_UNREACHABLE_STATEMENTS",
    "ORPHANED_LINE_PREFIX",
    "ORPHANED_RECORD_MARKER_TEMPLATE",
    "PARAGRAPH_EXIT_WORDS",
    "PREFERRED_WORK_GROUP_NAMES",
    "PREFER_GENERATED_COUNTER_GROUP",
    "RECORD_LAYOUT_VERBS",
    "STRUCTURAL_SAFETY_MESSAGES",
    "UNIFY_GENERATED_FIELD_GROUP",
    "UNREACHABLE_MARKER",
]
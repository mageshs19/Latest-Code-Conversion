from __future__ import annotations
from rules.timestamp_audit_rules import (  # noqa: F401
    CS_PROGRAM_FIELD as PROGRAM_CONSTANT_FIELD,
    PROGRAM_NAME_FIELD,
    PROGRAM_NAME_MOVE_TEMPLATE,
)
ENFORCE_CURSOR_SCOPED_INITIALIZATION = True
EMIT_STARTUP_INITIALIZE_PARAGRAPH = False
REMOVE_LEGACY_STARTUP_PARAGRAPH = True
SALVAGE_LEGACY_STARTUP_STATEMENTS = True
EMIT_INITIALIZE_PERIOD = False

STARTUP_PARAGRAPH_NAME = "100-INITIALIZE"
TIMESTAMP_PARAGRAPH_NAME = "600-GET-TIMESTAMP"


INITIALIZE_TEMPLATE = "INITIALIZE {group}"
PERFORM_TEMPLATE = "PERFORM {paragraph}"

STATEMENT_TERMINATOR = "."

LINE_WIDTH = 80
SEQUENCE_WIDTH = 6
BODY_START = 7
BODY_END = 72
STATEMENT_INDENT = " " * 4
ACTIVE_INDICATORS = (" ", "D", "-")
COMMENT_INDICATORS = ("*", "/")

DCLGEN_GROUP_PREFIX = "DCL"
CURSOR_SCOPE_LOOKAHEAD = 200

NON_PARAGRAPH_WORDS = frozenset({
    "CONTINUE", "EXIT", "GOBACK", "END-IF", "END-EVALUATE", "END-EXEC",
    "END-PERFORM", "END-READ", "END-SEARCH", "END-STRING", "END-WRITE",
    "STOP",
})

SCOPE_RUN = "RUN"
SCOPE_ROW = "ROW"
SCOPE_UNKNOWN = "UNKNOWN"

ENFORCE_INITIALIZATION_PLACEMENT = True
INITIALIZATION_PARAGRAPH_PREFIX = STARTUP_PARAGRAPH_NAME
INITIALIZATION_PARAGRAPH_TEMPLATE = "{prefix}-{token}"
INITIALIZATION_FORBIDDEN_AFTER = (
    "PROCEDURE DIVISION.",
    "OPEN",
    "FETCH",
)
INITIALIZATION_PLACEMENT_ANCHORS = (
    STARTUP_PARAGRAPH_NAME,
    "MAIN-PROCEDURE",
)
DCLGEN_INITIALIZATION_PATTERNS = (
    r"INITIALIZE\s+\w*DCL\w+\s*\.",
    r"INITIALIZE\s+\w*STRUCT\w+\s*\.",
)

INITIALIZATION_PLACEMENT_MESSAGES = {
    "no_groups": (
        "Initialization: no DCLGEN group is referenced; pass skipped."
    ),
    "no_procedure_division": (
        "Initialization: no PROCEDURE DIVISION found; pass skipped."
    ),
    "no_cursor_open": (
        "Initialization: no PERFORM of a cursor OPEN paragraph was "
        "found; pass skipped."
    ),
    "group_unresolved": (
        "Initialization: cursor {cursor} has no resolvable DCLGEN group; "
        "no INITIALIZE was placed for it."
    ),
    "placed_run_scope": (
        "Initialization: placed INITIALIZE {group} in the mainline "
        "before {paragraph}."
    ),
    "placed_row_scope": (
        "Initialization: placed INITIALIZE {group} in {scope} before "
        "{paragraph}; the child group is cleared once per parent row."
    ),
    "already_placed": (
        "Initialization: INITIALIZE {group} is already correctly scoped "
        "before {paragraph}."
    ),
    "removed_statements": (
        "Initialization: removed {count} out-of-scope INITIALIZE "
        "statement(s)."
    ),
    "removed_startup_paragraph": (
        "Initialization: removed the {paragraph} paragraph; "
        "initialization is now cursor scoped."
    ),
    "removed_startup_perform": (
        "Initialization: removed PERFORM {paragraph}."
    ),
    "salvaged_statement": (
        "Initialization: moved {statement} from {paragraph} to the "
        "mainline."
    ),
    "dropped_duplicate": (
        "Initialization: dropped a duplicate {statement}."
    ),
    "program_name_rewritten": (
        "Initialization: replaced {count} hardcoded PROGRAM-NAME move(s) "
        "with {constant}."
    ),
    "rolled_back": (
        "Initialization: post-condition failed ({reason}); the pass was "
        "rolled back and the program is unchanged."
    ),
    "summary": (
        "Initialization: scoped {run} run-level and {row} row-level "
        "DCLGEN group(s)."
    ),
}

__all__ = [
    "ENFORCE_CURSOR_SCOPED_INITIALIZATION",
    "EMIT_STARTUP_INITIALIZE_PARAGRAPH",
    "REMOVE_LEGACY_STARTUP_PARAGRAPH",
    "SALVAGE_LEGACY_STARTUP_STATEMENTS",
    "EMIT_INITIALIZE_PERIOD",
    "STARTUP_PARAGRAPH_NAME",
    "TIMESTAMP_PARAGRAPH_NAME",
    "PROGRAM_CONSTANT_FIELD",
    "PROGRAM_NAME_FIELD",
    "INITIALIZE_TEMPLATE",
    "PERFORM_TEMPLATE",
    "PROGRAM_NAME_MOVE_TEMPLATE",
    "STATEMENT_TERMINATOR",
    "LINE_WIDTH",
    "SEQUENCE_WIDTH",
    "BODY_START",
    "BODY_END",
    "STATEMENT_INDENT",
    "ACTIVE_INDICATORS",
    "COMMENT_INDICATORS",
    "DCLGEN_GROUP_PREFIX",
    "CURSOR_SCOPE_LOOKAHEAD",
    "NON_PARAGRAPH_WORDS",
    "SCOPE_RUN",
    "SCOPE_ROW",
    "SCOPE_UNKNOWN",
    "ENFORCE_INITIALIZATION_PLACEMENT",
    "INITIALIZATION_PARAGRAPH_PREFIX",
    "INITIALIZATION_PARAGRAPH_TEMPLATE",
    "INITIALIZATION_FORBIDDEN_AFTER",
    "INITIALIZATION_PLACEMENT_ANCHORS",
    "DCLGEN_INITIALIZATION_PATTERNS",
    "INITIALIZATION_PLACEMENT_MESSAGES",
]
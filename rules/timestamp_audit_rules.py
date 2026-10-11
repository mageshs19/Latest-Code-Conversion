from __future__ import annotations

TIMESTAMP_AUDIT_RULES = [
    "Sheet Mapping decides DB2 table and column names.",
    "DCLGEN supplies COBOL host variable spelling and group names.",
    "DCLGEN must not introduce audit fields absent from Sheet Mapping.",
    "For UPDATE flows, generate TS_UPDATE and USER-ID moves only.",
    "TS_CREATE is insert-only and is not generated for update-only flows.",
    "Timestamp paragraph must be a safe paragraph with a terminating boundary.",
    "CS-PROGRAM is declared inside an existing work-area group, never in a "
    "record layout.",
]

AUDIT_COLUMN_PREFIXES = [
    "TS_CREATE",
    "TS_UPDATE",
    "ID_USERID",
    "NR_USERID",
    "ID_USER",
    "NR_USER",
    "NS_IDMSKEY",
]

UPDATE_AUDIT_COLUMN_PREFIXES = [
    "TS_UPDATE",
    "ID_USERID",
    "NR_USERID",
    "ID_USER",
    "NR_USER",
]

INSERT_EXCLUDE_AUDIT_PREFIXES = [
    "TS_UPDATE",
]

DATE_COLUMN_PREFIXES = [
    "DA_",
    "DT_",
]

TIMESTAMP_WS_MARKER = "DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE"
TIMESTAMP_DEFAULT_PROGRAM_ID = "DB2PGM"
TIMESTAMP_PROGRAM_ID_LENGTH = 8

CS_PROGRAM_FIELD = "CS-PROGRAM"
PROGRAM_NAME_FIELD = "PROGRAM-NAME"
PROGRAM_NAME_MOVE_TEMPLATE = "MOVE {constant}   TO {field}"
CS_PROGRAM_PICTURE = "PIC X(8)"
CS_PROGRAM_PREFERRED_LEVEL = "10"
CS_PROGRAM_FALLBACK_LEVEL = "77"
CS_PROGRAM_LEVELS = ("05", "10", "15", "77")
CS_PROGRAM_NAME_COLUMN = 4
CS_PROGRAM_PICTURE_COLUMN = 29
CS_PROGRAM_VALUE_COLUMN = 41
CS_PROGRAM_CHILD_INDENT = " " * 4
PREFER_WORK_GROUP_FOR_CS_PROGRAM = True
ALLOW_STANDALONE_CS_PROGRAM_FALLBACK = True

CS_PROGRAM_TEMPLATE = (
    "{level}{name_pad}{field}{picture_pad}{picture}{value_pad}"
    "VALUE '{program_id}'."
)

TIMESTAMP_CS_PROGRAM_TEMPLATE = (
    "77  CS-PROGRAM               PIC X(8)    VALUE '{program_id:<8}'."
)

TIMESTAMP_WS_LINES = [
    "01  WS-TIMESTAMP-FIELDS.",
    "    05 TS-SYSTEM.",
    "       10  DA-SYS.",
    "           15  DA-SYS-CCYY.",
    "               20  CC            PIC X(2).",
    "               20  YY            PIC X(2).",
    "           15  MM                PIC X(2).",
    "           15  DD                PIC X(2).",
    "       10  HR-SYS.",
    "           15  HH                PIC X(2).",
    "           15  MI                PIC X(2).",
    "           15  SS                PIC X(2).",
    "           15  TT                PIC X(2).",
    "    05 TS-TIMESTAMP.",
    "       10  CC                    PIC X(2).",
    "       10  YY                    PIC X(2).",
    "       10  TE-MARKER1            PIC X             VALUE '-'.",
    "       10  MM                    PIC X(2).",
    "       10  TE-MARKER2            PIC X             VALUE '-'.",
    "       10  DD                    PIC X(2).",
    "       10  TE-MARKER3            PIC X             VALUE '-'.",
    "       10  HH                    PIC X(2).",
    "       10  TE-MARKER4            PIC X             VALUE '.'.",
    "       10  MI                    PIC X(2).",
    "       10  TE-MARKER5            PIC X             VALUE '.'.",
    "       10  SS                    PIC X(2).",
    "       10  TE-MARKER6            PIC X             VALUE '.'.",
    "       10  TT                    PIC X(2).",
    "       10  NNNN                  PIC 9(04)         VALUE 0.",
]

TIMESTAMP_MOVE_FIELDS = (
    "CC",
    "YY",
    "MM",
    "DD",
    "HH",
    "MI",
    "SS",
    "TT",
)

TIMESTAMP_PARAGRAPH_NAME = "600-GET-TIMESTAMP"
TIMESTAMP_PARAGRAPH_EXIT_NAME = "600-GET-TIMESTAMP-EXIT"
TIMESTAMP_PARAGRAPH_HEADER_TEMPLATE = "{paragraph_name}."
TIMESTAMP_PARAGRAPH_DEBUG_TEMPLATE = "D    DISPLAY '{paragraph_name}.'"
TIMESTAMP_PARAGRAPH_SOURCE_MOVE = (
    "     MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM."
)
TIMESTAMP_PARAGRAPH_FIELD_MOVE_TEMPLATE = (
    "     MOVE {field} OF TS-SYSTEM{pad}TO {field} OF TS-TIMESTAMP"
)
TIMESTAMP_PARAGRAPH_DISPLAY = "     DISPLAY 'TIMESTAMP: ' TS-TIMESTAMP"
TIMESTAMP_PARAGRAPH_TERMINATOR = "     ."
TIMESTAMP_PERFORM_TEMPLATE = "    PERFORM {paragraph_name}."
TIMESTAMP_MOVE_ALIGN_COLUMN = 38
EMIT_TIMESTAMP_DEBUG_LINE = True
ENFORCE_PROGRAM_NAME_CONSTANT = True

TIMESTAMP_MESSAGES = {
    "cs_program_present": (
        "Timestamp: {field} is already declared at level {level}; "
        "left unchanged."
    ),
    "cs_program_in_group": (
        "Timestamp: declared {field} as a level {level} inside {group}."
    ),
    "cs_program_standalone": (
        "Timestamp: no safe work-area group was found; declared {field} "
        "as a standalone level {level}."
    ),
    "cs_program_refused": (
        "Timestamp: no safe work-area group and standalone fallback is "
        "disabled; {field} was not declared."
    ),
    "working_storage_added": (
        "Timestamp: added the timestamp working-storage block."
    ),
    "working_storage_present": (
        "Timestamp: timestamp working storage already present."
    ),
    "paragraph_added": "Timestamp: generated the {paragraph} paragraph.",
    "paragraph_present": "Timestamp: {paragraph} already present.",
    "perform_added": (
        "Timestamp: added PERFORM {paragraph} at the start of the mainline."
    ),
    "perform_present": (
        "Timestamp: {paragraph} is already performed; no second call added."
    ),
    "no_working_storage": (
        "Timestamp: no WORKING-STORAGE SECTION found; the block was "
        "prepended."
    ),
    "summary": (
        "Timestamp generator: timestamp working storage and paragraph "
        "ensured."
    ),
        "program_name_bound": (
        "Timestamp: replaced {count} hardcoded PROGRAM-NAME move(s) "
        "with {constant}."
    ),
    "program_name_present": (
        "Timestamp: PROGRAM-NAME is already set from {constant}."
    ),
    "program_name_refused": (
        "Timestamp: {constant} is not declared; the hardcoded "
        "PROGRAM-NAME move was left in place."
    ),
}

__all__ = [
    "ALLOW_STANDALONE_CS_PROGRAM_FALLBACK",
    "AUDIT_COLUMN_PREFIXES",
    "CS_PROGRAM_CHILD_INDENT",
    "CS_PROGRAM_FALLBACK_LEVEL",
    "CS_PROGRAM_FIELD",
    "CS_PROGRAM_LEVELS",
    "CS_PROGRAM_NAME_COLUMN",
    "CS_PROGRAM_PICTURE",
    "CS_PROGRAM_PICTURE_COLUMN",
    "CS_PROGRAM_PREFERRED_LEVEL",
    "CS_PROGRAM_TEMPLATE",
    "CS_PROGRAM_VALUE_COLUMN",
    "DATE_COLUMN_PREFIXES",
    "EMIT_TIMESTAMP_DEBUG_LINE",
    "INSERT_EXCLUDE_AUDIT_PREFIXES",
    "PREFER_WORK_GROUP_FOR_CS_PROGRAM",
    "TIMESTAMP_AUDIT_RULES",
    "TIMESTAMP_CS_PROGRAM_TEMPLATE",
    "TIMESTAMP_DEFAULT_PROGRAM_ID",
    "TIMESTAMP_MESSAGES",
    "TIMESTAMP_MOVE_ALIGN_COLUMN",
    "TIMESTAMP_MOVE_FIELDS",
    "TIMESTAMP_PARAGRAPH_DEBUG_TEMPLATE",
    "TIMESTAMP_PARAGRAPH_DISPLAY",
    "TIMESTAMP_PARAGRAPH_EXIT_NAME",
    "TIMESTAMP_PARAGRAPH_FIELD_MOVE_TEMPLATE",
    "TIMESTAMP_PARAGRAPH_HEADER_TEMPLATE",
    "TIMESTAMP_PARAGRAPH_NAME",
    "TIMESTAMP_PARAGRAPH_SOURCE_MOVE",
    "TIMESTAMP_PARAGRAPH_TERMINATOR",
    "TIMESTAMP_PERFORM_TEMPLATE",
    "TIMESTAMP_PROGRAM_ID_LENGTH",
    "TIMESTAMP_WS_LINES",
    "TIMESTAMP_WS_MARKER",
    "UPDATE_AUDIT_COLUMN_PREFIXES",
    "program_name_bound",
    "program_name_present",
    "program_name_refused",
    "ENFORCE_PROGRAM_NAME_CONSTANT",
    "PROGRAM_NAME_FIELD",
    "PROGRAM_NAME_MOVE_TEMPLATE",

]


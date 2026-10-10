# LOCATION: rules/fixed_format_rules.py
# ACTION: REPLACE ENTIRE FILE

# Fixed-format COBOL layout rules. Constants only. No regex.
#
#   columns 1-6    left sequence number
#   column  7      indicator area
#   columns 8-72   COBOL body
#   columns 73-80  right sequence number

# ---------------------------------------------------------------------
# Column geometry. Zero based, end exclusive. SINGLE SOURCE OF TRUTH.
#
# Every width below is DERIVED from these boundaries, so a boundary and
# a width can never disagree. The literals 6 / 8 / 65 / 80 previously
# sat beside the boundaries as independent assignments; one of them
# drifting is how a record came out 79 columns and had its own sequence
# area copied into the body of a new record:
#
#     000380 000380* 2004/12 REPRENDRE N DE TITRE EN OUTPUT (12 POS
# ---------------------------------------------------------------------
LEFT_SEQUENCE_START = 0
LEFT_SEQUENCE_END = 6
INDICATOR_INDEX = 6
BODY_START = 7
BODY_END = 72
RIGHT_SEQUENCE_START = 72
RIGHT_SEQUENCE_END = 80

LEFT_SEQUENCE_WIDTH = LEFT_SEQUENCE_END - LEFT_SEQUENCE_START      # 6
INDICATOR_WIDTH = BODY_START - INDICATOR_INDEX                     # 1
BODY_WIDTH = BODY_END - BODY_START                                 # 65
RIGHT_SEQUENCE_WIDTH = RIGHT_SEQUENCE_END - RIGHT_SEQUENCE_START   # 8
TOTAL_WIDTH = RIGHT_SEQUENCE_END                                   # 80

# Shortest record on which columns 1-6 and column 7 can be read at all.
# Requiring TOTAL_WIDTH here is what made a record short by ONE character
# classify as unsequenced.
MIN_ADDRESSABLE_LENGTH = BODY_START                                # 7

# Only the line ending may be removed from a raw record. Trailing blanks
# position the right sequence at column 73; rstrip() destroys them.
LINE_ENDINGS = "\r\n"

# ---------------------------------------------------------------------
# Sequence numbering defaults
#
#   left 000010 -> right 00010000
#   left 000020 -> right 00020000
#
# Layout fallback, not program-specific hardcoding.
# ---------------------------------------------------------------------
DEFAULT_LEFT_START = 10
DEFAULT_LEFT_STEP = 10
DEFAULT_RIGHT_START = 10000
DEFAULT_RIGHT_STEP = 10000

# ---------------------------------------------------------------------
# WHITESPACE-SENSITIVE. Verify these four against the lengths captured
# before this file was replaced. A collapsed value silently re-indents
# every generated line.
# ---------------------------------------------------------------------
AREA_A_INDENT = ""
AREA_B_INDENT = "    "
SQL_INDENT = "    "
SQL_CONTINUATION_INDENT = "      "

# ---------------------------------------------------------------------
# Indicator area
# ---------------------------------------------------------------------
SPACE_INDICATOR = " "
COMMENT_INDICATOR = "*"
PAGE_INDICATOR = "/"
DEBUG_INDICATOR = "D"
DEBUG_INDICATOR_LOWER = "d"
CONTINUATION_INDICATOR = "-"

VALID_INDICATORS = {
    SPACE_INDICATOR,
    COMMENT_INDICATOR,
    PAGE_INDICATOR,
    DEBUG_INDICATOR,
    DEBUG_INDICATOR_LOWER,
    CONTINUATION_INDICATOR,
}

# Indicators whose body is preserved verbatim, never Area A/B reformatted.
PRESERVE_VERBATIM_INDICATORS = {
    COMMENT_INDICATOR,
    PAGE_INDICATOR,
    DEBUG_INDICATOR,
    CONTINUATION_INDICATOR,
}

# ---------------------------------------------------------------------
# COBOL vocabulary
# ---------------------------------------------------------------------
PROCEDURE_DIVISION_NAME = "PROCEDURE"

NON_PARAGRAPH_WORDS = {
    "ACCEPT",
    "ADD",
    "ALTER",
    "CALL",
    "CANCEL",
    "CLOSE",
    "COMMIT",
    "COMPUTE",
    "CONTINUE",
    "DELETE",
    "DISPLAY",
    "DIVIDE",
    "ELSE",
    "END-ADD",
    "END-CALL",
    "END-DELETE",
    "END-DIVIDE",
    "END-EVALUATE",
    "END-EXEC",
    "END-IF",
    "END-MULTIPLY",
    "END-PERFORM",
    "END-READ",
    "END-RETURN",
    "END-REWRITE",
    "END-SEARCH",
    "END-START",
    "END-STRING",
    "END-SUBTRACT",
    "END-UNSTRING",
    "END-WRITE",
    "EVALUATE",
    "EXEC",
    "EXIT",
    "FETCH",
    "GOBACK",
    "IF",
    "INITIALIZE",
    "INSPECT",
    "MOVE",
    "MULTIPLY",
    "NEXT",
    "OPEN",
    "PERFORM",
    "READ",
    "RETURN",
    "REWRITE",
    "ROLLBACK",
    "SEARCH",
    "SET",
    "SKIP1",
    "SKIP2",
    "SKIP3",
    "SORT",
    "SPACE",
    "SPACES",
    "START",
    "STOP",
    "STRING",
    "SUBTRACT",
    "UNSTRING",
    "WHEN",
    "WRITE",
}

PROCEDURE_VERBS = (
    "ACCEPT ",
    "ADD ",
    "ALTER ",
    "CALL ",
    "CANCEL ",
    "CLOSE ",
    "COMMIT",
    "COMPUTE ",
    "CONTINUE",
    "DELETE ",
    "DISPLAY ",
    "DIVIDE ",
    "ELSE",
    "END-ADD",
    "END-CALL",
    "END-DELETE",
    "END-DIVIDE",
    "END-EVALUATE",
    "END-EXEC",
    "END-IF",
    "END-MULTIPLY",
    "END-PERFORM",
    "END-READ",
    "END-RETURN",
    "END-REWRITE",
    "END-SEARCH",
    "END-START",
    "END-STRING",
    "END-SUBTRACT",
    "END-UNSTRING",
    "END-WRITE",
    "EVALUATE ",
    "EXEC SQL",
    "EXIT",
    "FETCH ",
    "GOBACK",
    "IF ",
    "INITIALIZE ",
    "INSPECT ",
    "MOVE ",
    "MULTIPLY ",
    "NEXT ",
    "OPEN ",
    "PERFORM ",
    "READ ",
    "RETURN ",
    "REWRITE ",
    "ROLLBACK",
    "SEARCH ",
    "SET ",
    "SORT ",
    "START ",
    "STOP ",
    "STRING ",
    "SUBTRACT ",
    "UNSTRING ",
    "WHEN ",
    "WRITE ",
)

# Statement starters used to confirm a trailing 8-digit token is a right
# sequence number rather than part of the body.
COBOL_STATEMENT_STARTERS = (
    "ACCEPT ",
    "ADD ",
    "CALL ",
    "CLOSE ",
    "COMPUTE ",
    "CONTINUE",
    "DISPLAY ",
    "ELSE",
    "END-",
    "EVALUATE ",
    "EXEC ",
    "EXIT",
    "IF ",
    "INITIALIZE ",
    "MOVE ",
    "OPEN ",
    "PERFORM ",
    "READ ",
    "SET ",
    "STOP ",
    "TO ",
    "WHEN ",
    "WRITE ",
)

# Marker used when detecting a generated right sequence (00000010 style).
RIGHT_SEQUENCE_GENERATED_PREFIX = "0000"

# ---------------------------------------------------------------------
# Embedded SQL
# ---------------------------------------------------------------------
SQL_LEVEL_1_KEYWORDS = (
    "SELECT ",
    "INTO ",
    "FROM ",
    "WHERE ",
    "ORDER BY ",
    "GROUP BY ",
    "HAVING ",
    "FETCH ",
    "OPEN ",
    "CLOSE ",
    "COMMIT",
    "ROLLBACK",
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "SET ",
    "VALUES ",
    "FOR READ ONLY",
    "QUERYNO ",
)

SQL_LEVEL_2_KEYWORDS = (
    "AND ",
    "OR ",
    ",",
)

# ---------------------------------------------------------------------
# Area A / Area B classification
# ---------------------------------------------------------------------
AREA_A_HEADER_PREFIXES = (
    "PROGRAM-ID.",
    "AUTHOR.",
    "INSTALLATION.",
    "DATE-WRITTEN.",
    "DATE-COMPILED.",
    "SECURITY.",
)

AREA_A_DATA_LEVELS = {
    "01",
    "66",
    "77",
}

AREA_B_DATA_LEVELS = {
    "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37", "38", "39", "40",
    "41", "42", "43", "44", "45", "46", "47", "48", "49",
    "88",
}

# ---------------------------------------------------------------------
# Body wrapper
# ---------------------------------------------------------------------
WRAP_IF_PREFIX = "IF "
WRAP_MOVE_PREFIX = "MOVE "
WRAP_TO_PREFIX = "TO "

BOOLEAN_OPERATOR_WORDS = frozenset({"AND", "OR"})

# COBOL qualifier connectors. Never leave one dangling at the end of a
# wrapped fragment: a trailing OF / IN strands the qualified name on the
# next line as "NAME.", which later passes misread as a paragraph header.
QUALIFIER_CONNECTOR_WORDS = frozenset({"OF", "IN"})

# ---------------------------------------------------------------------
# Diagnostics
#
# A four-line IF condition was joined into two lines and cut mid-name,
# losing 25 characters, because the continuation merge did not check the
# 65-column window. Neither the merge nor the cut said anything.
# ---------------------------------------------------------------------
FIXED_FORMAT_MESSAGES = {
    "merge_refused": (
        "Fixed format: continuation merge refused, {width} columns "
        "exceeds the {limit}-column body window; the author's line "
        "break was kept ({body}...)."
    ),
    "body_truncated": (
        "Fixed format: body of {width} columns exceeded the {limit}-"
        "column window and was cut ({body}...). Wrapping failed upstream."
    ),
    "geometry_drift": (
        "Fixed format: record assembled to {width} columns, expected "
        "{limit}. A width constant has drifted."
    ),
}
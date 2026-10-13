# LOCATION: rules/cursor_paragraph_rules.py
# ACTION: REPLACE ENTIRE FILE

"""Cursor paragraph generation rules.

This module contains constants only.

No regex patterns, parser logic, generator logic, or hardcoded program,
record, table, cursor, or host variable names belong here.

Layout follows the COBOL team's manual reference program:

    *---------------------------------------------------------------*
    *    OPEN CURSOR
    *---------------------------------------------------------------*
     710-OPEN-DZBEFFC1.
    D    DISPLAY '710-OPEN-DZBEFFC1.'
         MOVE 710    TO SQL-LOCATION

         EXEC SQL
           OPEN DZBEFFC1
         END-EXEC

         EVALUATE SQLCODE
           WHEN ZERO
                SET DZBEFFC1-NOT-EOC TO TRUE
           WHEN OTHER
                DISPLAY 'ERROR WHILE OPENING CURSOR DZBEFFC1'
                PERFORM SQLERROR
         END-EVALUATE
         .

and, in a child FETCH error branch:

         WHEN OTHER
              DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'
              DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF
                                       OF DCLDZBEFFTV
              DISPLAY 'NR-ID-STOCK = ' NR-IDSTOCK-479BEFF
                                       OF DCLDZBEFFTV
              PERFORM SQLERROR


CORRECTION 1 - ONE FEATURE WAS DECLARED TWICE
----------------------------------------------
This module carried two template families for the same DISPLAY block:

    JOIN_KEY_DISPLAY_TEMPLATE  = "DISPLAY '{label} = ' {host}"   w=13
    FETCH_KEY_DISPLAY_TEMPLATE = "DISPLAY '{label} : ' {host}"   w=18

with two switches for one block. The FETCH_KEY family was live, so the
generated program carried

    DISPLAY 'CT-RKTPROD-479BEFF : ' CT-RKTPROD-479BEFF

while the JOIN_KEY family read as authoritative and was never emitted.
Editing the wrong one changes nothing and looks like a tooling fault.

There is now ONE family. The FETCH_KEY_* names are RE-EXPORTED from it
so existing importers keep working; they are never re-assigned.


CORRECTION 2 - THE LABEL WAS THE DCLGEN HOST NAME
--------------------------------------------------
The operator reads the job log against the IDMS record layout, so the
label must be the IDMS COBOL field name that Sheet Mapping pairs with
the DB2 column. It is NOT derivable from the host name:

    CT-RKTPROD-479BEFF  ->  CT-RKT-PROD
    NR-IDSTOCK-479BEFF  ->  NR-ID-STOCK
    NR-CDSTK-479BEFF    ->  NR-CD-STOCK
    NS-DBSTK-479BEFF    ->  NR-DB-STOCK      NS becomes NR

No string rule produces that last line. The label is RESOLVED from
Sheet Mapping, or the builder falls back to the host name and REPORTS
the fallback. A silent fallback is how this shipped unnoticed.


CORRECTION 3 - THE QUALIFIER INDENT WAS HARD-CODED
---------------------------------------------------
IND_WHEN_BODY_CONT was 33 literal spaces, so "OF <group>" landed under
whatever the previous label width happened to produce. The offset is
now DERIVED from the rendered prefix at build time and this constant is
deleted. A fixed indent drifts the moment a label width changes.


CORRECTION 4 - THE LABEL WIDTH WAS A MAGIC NUMBER
--------------------------------------------------
13 in one family, 18 in the other. Both truncate or over-pad depending
on the program. The width is now the widest label in THAT branch, so
the hosts form a column without a constant that can be wrong.


CORRECTION 5 - AN APPEND BLOCK LANDED BELOW THE CLOSING MARKER
---------------------------------------------------------------
Four constants were pasted after the "NO CONSTANT MAY BE ADDED BELOW
THIS LINE" comment:

    COUNT_PARENT_FETCH_ONLY = True
    DEBUG_BODY_INDENT = " " * (COLUMN_STATEMENT - BODY_FIRST_COLUMN - 1)
    COLUMN_SQL_INTO = 15          <- ALREADY declared above
    COLUMN_SQL_INTO_NEXT = 18     <- ALREADY declared above
    IND_SQL_INTO = ...            <- ALREADY declared above
    IND_SQL_INTO_NEXT = ...       <- ALREADY declared above

Two defects followed.

  a. DEBUG_BODY_INDENT subtracted one for the 'D' indicator. The 'D'
     occupies column 7; the body still begins at column 8, so the
     indicator is not part of the body and must not be deducted. Three
     spaces put DISPLAY at column 11, inside AREA A:

         003860D   DISPLAY '710-OPEN-DZBEFFC1.'      column 11  WRONG
         003880D    DISPLAY '710-OPEN-DZBEFFC1.'     column 12  right

  b. The four INTO names were assigned TWICE. Python keeps the LAST
     assignment, so the geometry section read as authoritative while
     the append was live. The values happened to match, so nothing
     broke - which is precisely how the QUERYNO 254-vs-119 divergence
     began. Every constant is now declared exactly once, in its own
     section, and nothing follows the closing marker.
"""

from __future__ import annotations

# DECLARE_SQL_LOCATION_FIELD is owned by catalogs/output_sections.py.
# Re-exported, never re-declared: a second copy diverges the day one of
# them flips. That direction must not reverse.
from catalogs.output_sections import (  # noqa: F401
    DECLARE_SQL_LOCATION_FIELD,
)
from rules.sql_location_rules import (  # noqa: F401
    SQL_LOCATION_FIELD,
    SQL_LOCATION_NAME_TEMPLATE,
    SQL_LOCATION_NUMBER_PAD,
    SQL_LOCATION_NUMBER_TEMPLATE,
    SQL_LOCATION_USES_PARAGRAPH_NUMBER,
)

# =====================================================================
# Fixed process / error paragraph names (COBOL-shop standard)
# =====================================================================
SQL_ERROR_PARAGRAPH_NAME = "SQLERROR"
LEGACY_SQL_ERROR_PARAGRAPH_NAME = "SQL-ERROR"


# =====================================================================
# Termination rule
# =====================================================================
# The paragraph body is ONE COBOL sentence. No period on MOVE, END-EXEC
# or END-EVALUATE; a single period on its own line closes the paragraph.
# A period inside EVALUATE closes the scope early and orphans
# END-EVALUATE.
LONE_PERIOD = "."

# =====================================================================
# SQL-LOCATION form
# =====================================================================
# RESOLVED by the COBOL team's manual reference program:
#
#     MOVE 710    TO SQL-LOCATION
#
# SQL-LOCATION is supplied by the SQLERRWS copybook, NOT declared by the
# converter.


# The error branch does NOT restate SQL-LOCATION.
#
# The original guard protected against a STALE value: a paragraph that
# sets it at entry, runs other statements, then fails. A GENERATED
# cursor paragraph has nothing in between - entry MOVE, EXEC SQL,
# EVALUATE - so the WHEN OTHER move is always identical to the entry
# move and adds a line the manual reference does not carry.
#
# The ENTRY move remains mandatory. Set True only if a pass starts
# inserting statements between paragraph entry and the EXEC SQL.
ENFORCE_SQL_LOCATION_IN_ERROR_BRANCH = False

# =====================================================================
# Body geometry
#
# Target COLUMN first, indent DERIVED from it. Never hand-type an indent
# string: a retyped space count is invisible in review and shifts a
# whole generated block.
#
# Columns 1-6 left sequence, column 7 indicator, columns 8-72 body.
# =====================================================================
BODY_FIRST_COLUMN = 8
BODY_LAST_COLUMN = 72
BODY_WIDTH = BODY_LAST_COLUMN - BODY_FIRST_COLUMN + 1      # 65

COLUMN_STATEMENT = 12       # MOVE, EXEC SQL, EVALUATE, END-EVALUATE
COLUMN_SQL_BODY = 14        # OPEN / FETCH / CLOSE, END-EXEC
COLUMN_SQL_INTO = 15        # INTO
COLUMN_SQL_INTO_NEXT = 18   # , :GROUP.HOST
COLUMN_WHEN = 14            # WHEN ZERO / WHEN 100 / WHEN OTHER
COLUMN_WHEN_BODY = 19       # the statement inside a WHEN branch

IND_STATEMENT = " " * (COLUMN_STATEMENT - BODY_FIRST_COLUMN)
IND_SQL_BODY = " " * (COLUMN_SQL_BODY - BODY_FIRST_COLUMN)
IND_SQL_INTO = " " * (COLUMN_SQL_INTO - BODY_FIRST_COLUMN)
IND_SQL_INTO_NEXT = " " * (COLUMN_SQL_INTO_NEXT - BODY_FIRST_COLUMN)
IND_WHEN = " " * (COLUMN_WHEN - BODY_FIRST_COLUMN)
IND_WHEN_BODY = " " * (COLUMN_WHEN_BODY - BODY_FIRST_COLUMN)

# IND_WHEN_BODY_CONT is DELETED. See CORRECTION 3. The DISPLAY
# continuation offset is derived from the rendered prefix at build time.

# =====================================================================
# COBOL tokens
# =====================================================================
TOKEN_EXEC_SQL = "EXEC SQL"
TOKEN_END_EXEC = "END-EXEC"
TOKEN_EVALUATE_SQLCODE = "EVALUATE SQLCODE"
TOKEN_END_EVALUATE = "END-EVALUATE"
TOKEN_WHEN_ZERO = "WHEN ZERO"
TOKEN_WHEN_100 = "WHEN 100"
TOKEN_WHEN_OTHER = "WHEN OTHER"
TOKEN_CONTINUE = "CONTINUE"
TOKEN_INTO = "INTO"
TOKEN_HOST_SEPARATOR = ", "
TOKEN_OF = "OF"

# =====================================================================
# Cursor operations and flag suffixes
# =====================================================================
CURSOR_OPERATIONS = ("OPEN", "FETCH", "CLOSE")
CURSOR_EOC_SUFFIX = "-EOC"
CURSOR_NOT_EOC_SUFFIX = "-NOT-EOC"
CURSOR_FLAG_TEMPLATE = "WS-{cursor}-FLAG"

# =====================================================================
# Row counter inside the FETCH paragraph
# =====================================================================
# Only the PARENT cursor's FETCH increments a row counter.
#
# The manual reference VMDZ4420 counts 720-FETCH (parent) and does NOT
# count 820-FETCH (child):
#
#     720-FETCH-DZBEFFC1          <- parent
#         WHEN ZERO
#              ADD 1 TO WS-NB-BEFF-COUNT
#              PERFORM HOOFDVERWERKING
#
#     820-FETCH-DZEVEFC1          <- child
#         WHEN ZERO
#              PERFORM VERWERK-VMBEVEF
#
# A child row is a detail of a parent row that has ALREADY been counted,
# so a per-child counter is always larger than the number of units of
# work and answers no question an operator asks. WS-NB-EVEF-COUNT was
# declared, incremented and displayed, and meant nothing.
#
# The reference carries exactly TWO counters: one parent cursor, plus
# WS-NB-OUTPUT-COUNT from the output-write pass. Never one per cursor.
#
# Set False only if a site wants a counter per cursor. Expect one extra
# declared field and one extra total line per child cursor.
COUNT_PARENT_FETCH_ONLY = True

# =====================================================================
# Generated statement templates
# =====================================================================


PARAGRAPH_HEADER_TEMPLATE = "{paragraph}."
OPEN_STATEMENT_TEMPLATE = "OPEN {cursor}"
FETCH_STATEMENT_TEMPLATE = "FETCH {cursor}"
CLOSE_STATEMENT_TEMPLATE = "CLOSE {cursor}"
SET_NOT_EOC_TEMPLATE = "SET {cursor}{suffix} TO TRUE"
# One shape, two call sites. Separate NAMES, never separate VALUES.
SET_EOC_TEMPLATE = SET_NOT_EOC_TEMPLATE
DISPLAY_ERROR_TEMPLATE = "DISPLAY '{text}'"
PERFORM_TEMPLATE = "PERFORM {paragraph}"
COMMENT_BLOCK_TEMPLATE = "*{title:<62}*"
INTO_FIRST_TEMPLATE = "INTO :{group}.{host}"
INTO_NEXT_TEMPLATE = ", :{group}.{host}"

# =====================================================================
# Manual reference banners
# =====================================================================
BANNER_RULE = (
    "*---------------------------------------------------------------*"
)
BANNER_TITLE_TEMPLATE = "*    {title}"

BANNER_OPEN_CURSOR = "OPEN CURSOR"
BANNER_FETCH_CURSOR = "FETCH CURSOR"
BANNER_CLOSE_CURSOR = "CLOSE CURSOR"

EMIT_PARAGRAPH_BANNERS = True

# =====================================================================
# Debug (column 7 = 'D') trace lines
# =====================================================================
EMIT_DEBUG_TRACE_LINES = True
DEBUG_INDICATOR = "D"
DEBUG_TRACE_TEMPLATE = "DISPLAY '{paragraph}.'"

# The 'D' occupies column 7, the INDICATOR. The body still starts at
# column 8, so the trace body takes the FULL statement offset to reach
# column 12. The indicator is not part of the body and must not be
# subtracted from it. See CORRECTION 5a.
#
#     003880D    DISPLAY '710-OPEN-DZBEFFC1.'
#            ^col 7      ^col 12
DEBUG_BODY_INDENT = " " * (COLUMN_STATEMENT - BODY_FIRST_COLUMN)

# Sentinel prefix used to mark a body line that must carry the 'D'
# indicator in column 7. The fixed-format writer strips it.
DEBUG_SENTINEL = "\x01D"

# =====================================================================
# Row-identity diagnostics in a FETCH WHEN OTHER branch
#
# ONE family. See CORRECTION 1. Both paths - driving key and fetched
# columns - render through the SAME template, so the two can never
# diverge again.
# =====================================================================
EMIT_KEY_DIAGNOSTICS = True

# Label source. SHEET_MAPPING is the manual-reference behaviour.
# HOST reproduces the old output and exists only for a byte-diff.
KEY_LABEL_SOURCE_MAPPING = "SHEET_MAPPING"
KEY_LABEL_SOURCE_HOST = "HOST"
KEY_LABEL_SOURCE = KEY_LABEL_SOURCE_MAPPING

# The ONE display template. Separator is '=', matching the manual.
KEY_DISPLAY_TEMPLATE = "DISPLAY '{label} = ' {host}"
KEY_QUALIFIER_TEMPLATE = "OF {group}"

# Pad every label in ONE branch to the widest label in THAT branch.
# 0 = derive. A positive value only forces a MINIMUM; it never truncates.
KEY_LABEL_MIN_WIDTH = 0

# Align "OF <group>" under the host variable on the line above.
ALIGN_KEY_QUALIFIER = True

# How many leading hosts to display. The manual shows five. An unbounded
# list would bury the failure in the job log.
KEY_DIAGNOSTIC_LIMIT = 5

# A DISPLAY that does not fit columns 8-72 is split at the OF keyword
# and the continuation aligned under the operand. Truncation is never
# acceptable: a cut data-name does not compile.
KEY_BODY_END_COLUMN = BODY_LAST_COLUMN

KEY_HOST_TEMPLATE = "{field} OF {group}"

SKIP_UNQUALIFIED_KEY_HOSTS = True
WRAP_KEY_DISPLAY = True
KEY_DISPLAY_LITERAL_TEMPLATE = "DISPLAY '{label} = '"
COLUMN_KEY_CONTINUATION = 24
IND_KEY_CONTINUATION = " " * (COLUMN_KEY_CONTINUATION - BODY_FIRST_COLUMN)
DCLGEN_TABLE_SUFFIX = "TV"
MAPPING_TABLE_SUFFIX = "TB"
MAPPING_TABLE_SEPARATOR = "_"

KEY_DIAGNOSTIC_MESSAGES = {
    "emitted": (
        "Cursor paragraphs: {cursor} FETCH error branch displays "
        "{count} column(s) before PERFORM {paragraph}."
    ),
    "no_hosts": (
        "Cursor paragraphs: {cursor} FETCH error branch has no "
        "qualified host to display; generic error text only."
    ),
    "label_fallback": (
        "Cursor paragraphs: WARNING - no Sheet Mapping COBOL field "
        "name for column {column} of {table}. The DCLGEN host name "
        "was displayed in the error branch instead. Add the COBOL "
        "Zone cell for this row, or wire the mapping repository into "
        "CursorParagraphBodyBuilder."
    ),
    "truncated": (
        "Cursor paragraphs: {cursor} FETCH error branch limited to "
        "{limit} of {total} column(s)."
    ),
        "label_lookup_failed": (
        "Cursor paragraphs: the Sheet Mapping lookup {method} raised "
        "{error}. The label fell back to the DCLGEN host name. This is "
        "a converter defect, not a workbook gap."
    ),
}

# ---- Backward-compatible aliases -------------------------------------
# RE-EXPORTS of the names above, so existing importers keep working.
# DERIVED, never re-assigned: a second value here restores CORRECTION 1.
EMIT_JOIN_KEY_DIAGNOSTICS = EMIT_KEY_DIAGNOSTICS
EMIT_FETCH_KEY_DIAGNOSTICS = EMIT_KEY_DIAGNOSTICS
JOIN_KEY_DISPLAY_TEMPLATE = KEY_DISPLAY_TEMPLATE
FETCH_KEY_DISPLAY_TEMPLATE = KEY_DISPLAY_TEMPLATE
FETCH_KEY_WHERE_DISPLAY_TEMPLATE = KEY_DISPLAY_TEMPLATE
JOIN_KEY_QUALIFIER_TEMPLATE = KEY_QUALIFIER_TEMPLATE
FETCH_KEY_HOST_TEMPLATE = KEY_HOST_TEMPLATE
FETCH_KEY_DIAGNOSTIC_LIMIT = KEY_DIAGNOSTIC_LIMIT
FETCH_KEY_BODY_END_COLUMN = KEY_BODY_END_COLUMN
FETCH_KEY_MESSAGES = KEY_DIAGNOSTIC_MESSAGES

# JOIN_KEY_LABEL_WIDTH and FETCH_KEY_LABEL_WIDTH are DELETED.
# See CORRECTION 4. Width is derived per branch.

# =====================================================================
# Error display text
# =====================================================================
ERROR_OPEN_TEMPLATE = "ERROR WHILE OPENING CURSOR {cursor}"
ERROR_FETCH_TEMPLATE = "ERROR WHILE FETCHING CURSOR {cursor}"
ERROR_CLOSE_TEMPLATE = "ERROR WHILE CLOSING CURSOR {cursor}"

# =====================================================================
# FETCH prologue and host references
# =====================================================================
ENFORCE_FETCH_PROLOGUE = False
INITIALIZE_HOST_GROUP_TEMPLATE = "INITIALIZE {group}."

# Separator between a host group and its field in a FETCH INTO item,
# e.g. :DCLDZBFASTV.DA-CPTAFS-479BFAS
HOST_GROUP_SEPARATOR = "."
HOST_REFERENCE_PREFIX = ":"
DCLGEN_GROUP_PREFIX = "DCL"

# =====================================================================
# Diagnostics
# =====================================================================
DIAG_NO_CURSOR_OPERATIONS = (
    "DB2 cursor paragraphs: no cursor operations found."
)
DIAG_BLOCK_EXISTS = (
    "DB2 cursor paragraphs: generated cursor paragraph block already "
    "exists."
)
DIAG_GENERATED_TEMPLATE = (
    "DB2 cursor paragraphs: generated {count} cursor paragraph set(s)."
)
DIAG_NO_HOST_VARIABLES_TEMPLATE = (
    "DB2 cursor paragraphs: no FETCH host variables resolved for "
    "cursor {cursor} record {record} table {table}."
)

# NO CONSTANT MAY BE ADDED BELOW THIS LINE. An append lands here, and an
# append is exactly what produced the duplicate template family and the
# duplicate INTO geometry this file has now had removed TWICE. A new
# constant belongs in its subject section above.
STRIP_REDEFINES_SUFFIX_FROM_KEY_LABEL = False
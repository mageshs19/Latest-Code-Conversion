# LOCATION: rules/move_alignment_rules.py
# ACTION: REPLACE ENTIRE FILE
"""Column alignment for runs of MOVE statements.

Constants only. No regex, no runtime logic, no program / record / table
/ cursor / host variable names.

A run of MOVE statements reads as a table. Aligning the TO keyword
turns it into one:

    MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV   TO UIT-AM-CN-STOCK
    MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV  TO UIT-AM-CND-STOCK
    MOVE WS-NR-CIO-CRE                     TO UIT-NR-CIO-CRE
    MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID

The sources become one column and the targets another, so a missing or
duplicated target is visible at a glance instead of being buried in
prose.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
tests/test_rules_no_duplicate_constants.py enforces it. A second
assignment silently wins and the first becomes dead code that still
reads as authoritative.
"""

from __future__ import annotations

#
# Master switch
#
ENFORCE_MOVE_ALIGNMENT = True

#
# Run formation
#
# A run of one has nothing to align against.
MIN_RUN_SIZE = 2

# A blank line is an authored separation. It ends the run, so each
# visual block gets its own column and a long statement in block 2
# cannot push block 1's targets to the right margin.
BLANK_LINE_BREAKS_RUN = True

# A statement that cannot be rendered on ONE line - a MOVE with more
# than one receiver - is rendered alone. Aligning it against its
# neighbours would place its continuation receiver under the wrong
# column.
MULTI_RECEIVER_STANDS_ALONE = True

#
# Geometry
#
# Minimum blanks between the source and TO. One is legal COBOL; the
# alignment pass normally supplies more.
MIN_GAP_BEFORE_TO = 1

# Refuse to align when a member would need more than this many filler
# blanks. Beyond it the "table" is mostly whitespace and the unaligned
# form reads better.
#
# 32, not 24. The reference layout pairs
#
#     MOVE ZEROES                            TO DA-CCYYMMDD
#     MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY
#
# which needs 28 blanks on the short member. A 24 limit refuses that
# run, so the pass would silently decline the very layout it exists to
# produce.
MAX_ALIGN_PADDING = 32

# Continuation receivers sit under the FIRST receiver, i.e. at
# to_col + len("TO ").
RECEIVER_OFFSET = 3

#
# Vocabulary
#
VERB_MOVE = "MOVE"
TOKEN_TO = "TO"
SENTENCE_TERMINATOR = "."

QUOTE_CHARACTERS = ("'", '"')

# Opening a line with any of these makes it a NEW statement, never a
# continuation receiver.
STATEMENT_OPENERS = (
    "ACCEPT", "ADD", "CALL", "CANCEL", "CLOSE", "COMPUTE", "CONTINUE",
    "DELETE", "DISPLAY", "DIVIDE", "ELSE", "END-ADD", "END-CALL",
    "END-DELETE", "END-DIVIDE", "END-EVALUATE", "END-EXEC", "END-IF",
    "END-MULTIPLY", "END-PERFORM", "END-READ", "END-SEARCH",
    "END-STRING", "END-SUBTRACT", "END-WRITE", "EVALUATE", "EXEC",
    "EXIT", "GOBACK", "IF", "INITIALIZE", "INSPECT", "MOVE", "MULTIPLY",
    "OPEN", "PERFORM", "READ", "REWRITE", "SEARCH", "SET", "SORT",
    "START", "STOP", "STRING", "SUBTRACT", "UNSTRING", "WHEN", "WRITE",
)

# Indicator column characters whose line is passed through untouched.
SKIPPABLE_INDICATORS = ("*", "/", "D", "d", "-")

# EXEC SQL bodies are placed at fixed clause positions by the cursor
# generator. This pass must not touch them.
SQL_BLOCK_START = "EXEC SQL"
SQL_BLOCK_END = "END-EXEC"

#
# Diagnostics
#
MOVE_ALIGNMENT_MESSAGES = {
    "aligned": (
        "Move alignment: aligned TO across {runs} run(s), "
        "{statements} statement(s)."
    ),
    "joined": (
        "Move alignment: joined {count} MOVE statement(s) that had been "
        "split across two lines."
    ),
    "refused_width": (
        "Move alignment: run left unaligned; the aligned form does not "
        "fit columns 8-72."
    ),
    "refused_padding": (
        "Move alignment: run left unaligned; alignment would need "
        "{padding} filler blanks, over the {limit} limit."
    ),
}

# NO CONSTANT MAY BE ADDED BELOW THIS LINE. An append lands here, and a
# second assignment of a name declared above would shadow it silently.

__all__ = [
    "ENFORCE_MOVE_ALIGNMENT",
    "MIN_RUN_SIZE",
    "BLANK_LINE_BREAKS_RUN",
    "MULTI_RECEIVER_STANDS_ALONE",
    "MIN_GAP_BEFORE_TO",
    "MAX_ALIGN_PADDING",
    "RECEIVER_OFFSET",
    "VERB_MOVE",
    "TOKEN_TO",
    "SENTENCE_TERMINATOR",
    "QUOTE_CHARACTERS",
    "STATEMENT_OPENERS",
    "SKIPPABLE_INDICATORS",
    "SQL_BLOCK_START",
    "SQL_BLOCK_END",
    "MOVE_ALIGNMENT_MESSAGES",
]
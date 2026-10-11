# LOCATION: rules/statement_layout_rules.py
# ACTION: REPLACE ENTIRE FILE
"""Paragraph separation in the generated PROCEDURE DIVISION.

Constants only. No regex, no runtime logic, no program / record / table
/ cursor / host variable names.

SCOPE - deliberately ONE rule

This composer inserts a blank line before a paragraph header, nothing
else. Two neighbouring rules were considered here and rejected:

  joining a split MOVE          owned by MoveAlignmentComposer
  the TO continuation indent    owned by MoveAlignmentComposer

Both are decided while that pass parses a MOVE into source and
receivers. Implementing them here as well would give two passes the
same lines, and the second would undo the first.

CORRECTION - __all__ was in DECLARATION order

The project rule is that __all__ is sorted and duplicate-free in every
rules/, patterns/ and catalogs/ module, sorted with Python rather than
by eye. Declaration order reads as "sorted enough" and is how a
duplicate survives review: two entries for the same name sit far apart
and look like two different names. The list below is the output of
sorted(), and NON_PARAGRAPH_WORDS is now written one member per line
for the same reason - a twelve-member set packed four to a line cannot
be scanned for a repeat. No member was added or removed.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
tests/test_rules_no_duplicate_constants.py enforces it.
"""

from __future__ import annotations

#
# Master switch
#
ENFORCE_STATEMENT_LAYOUT = True

#
# The one rule
#
BLANK_LINE_BEFORE_PARAGRAPH = True

#
# Vocabulary
#
SENTENCE_TERMINATOR = "."

# Single words ending in a period that are NOT paragraph headers.
# Kept deliberately identical to NON_PARAGRAPH_SINGLE_WORDS in
# rules/cobol_cleanup_rules.py: two passes that disagree about what a
# paragraph header is will cut the same program at different places.
NON_PARAGRAPH_WORDS = frozenset({
    "CONTINUE",
    "END-EVALUATE",
    "END-EXEC",
    "END-IF",
    "END-PERFORM",
    "END-READ",
    "END-SEARCH",
    "END-STRING",
    "END-WRITE",
    "EXIT",
    "GOBACK",
    "STOP",
})

# Indicator column characters whose line is passed through untouched.
SKIPPABLE_INDICATORS = ("*", "/", "D", "d", "-")

# A line already carrying one of these separates well enough; a second
# blank would just add noise.
SEPARATOR_INDICATORS = ("*", "/")

# EXEC SQL bodies sit at fixed clause positions set by the cursor
# generator. This pass must not touch them.
SQL_BLOCK_START = "EXEC SQL"
SQL_BLOCK_END = "END-EXEC"

#
# Diagnostics
#
STATEMENT_LAYOUT_MESSAGES = {
    "blank_inserted": (
        "Statement layout: inserted {count} blank line(s) before a "
        "paragraph header."
    ),
    "none_needed": (
        "Statement layout: every paragraph header was already separated."
    ),
}

PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"


# NO CONSTANT MAY BE ADDED BELOW THIS LINE.

__all__ = [
    "BLANK_LINE_BEFORE_PARAGRAPH",
    "ENFORCE_STATEMENT_LAYOUT",
    "NON_PARAGRAPH_WORDS",
    "PROCEDURE_DIVISION_TOKEN",
    "SENTENCE_TERMINATOR",
    "SEPARATOR_INDICATORS",
    "SKIPPABLE_INDICATORS",
    "SQL_BLOCK_END",
    "SQL_BLOCK_START",
    "STATEMENT_LAYOUT_MESSAGES",
]
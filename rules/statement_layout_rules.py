# LOCATION: rules/statement_layout_rules.py
# ACTION: CREATE NEW FILE
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
NON_PARAGRAPH_WORDS = frozenset({
    "CONTINUE", "EXIT", "GOBACK", "STOP",
    "END-EXEC", "END-EVALUATE", "END-IF", "END-PERFORM",
    "END-READ", "END-SEARCH", "END-STRING", "END-WRITE",
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

# NO CONSTANT MAY BE ADDED BELOW THIS LINE.

__all__ = [
    "ENFORCE_STATEMENT_LAYOUT",
    "BLANK_LINE_BEFORE_PARAGRAPH",
    "SENTENCE_TERMINATOR",
    "NON_PARAGRAPH_WORDS",
    "SKIPPABLE_INDICATORS",
    "SEPARATOR_INDICATORS",
    "SQL_BLOCK_START",
    "SQL_BLOCK_END",
    "STATEMENT_LAYOUT_MESSAGES",
]
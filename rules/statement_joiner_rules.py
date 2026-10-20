# LOCATION: rules/statement_joiner_rules.py
# ACTION: CREATE NEW FILE
"""Statement-joining vocabulary.

Constants only. No regex, no runtime logic, no program / record / table
/ cursor / host variable names.

OWNERSHIP
---------
rules/program_flow_rules.py already owns CONTINUATION_OPENERS,
CONTINUATION_TRAILERS and STATEMENT_VERBS. They are IMPORTED here, never
restated. This module adds only what that set lacks for IDMS source:
the IDMS verbs and the COBOL scope terminators.

The two should merge into one owner. They are kept apart for now because
program_flow_rules has other consumers and this change must stay
measurable. A SECOND copy of the base vocabulary is what this module
exists to prevent, so nothing here duplicates a name declared there.

NOTE - a second, partial copy already exists elsewhere in the tree as
STATEMENT_CONTINUATION_TOKENS. It must be deleted and its importers
pointed at program_flow_rules, or the drift this work removes simply
moves one file over.
"""

from __future__ import annotations

from rules.program_flow_rules import (  # noqa: F401 - re-exported
    CONTINUATION_OPENERS,
    CONTINUATION_TRAILERS,
    STATEMENT_VERBS,
)

# IDMS verbs. program_flow_rules carries COBOL verbs only, so without
# these an "OBTAIN NEXT ..." following an unterminated line could be
# read as its continuation. The opener/trailer test already refuses it,
# but a verb list that knows the language of the source it is reading is
# a guard, not a duplicate.
IDMS_STATEMENT_VERBS = frozenset({
    "OBTAIN",
    "FIND",
    "ERASE",
    "STORE",
    "MODIFY",
    "CONNECT",
    "DISCONNECT",
    "BIND",
    "READY",
    "FINISH",
    "COMMIT",
    "ROLLBACK",
    "ACCEPT",
    "KEEP",
})

# A line opening with one of these closes or branches a scope. It can
# never continue the statement above it, however that statement ends.
#
# Measured: VMDZ4310 line 210 is "END-PERFORM." directly under an
# unterminated "OBTAIN NEXT ...". Without this list a terminator-seeking
# joiner swallows the loop body and its END-PERFORM into the PERFORM
# UNTIL condition.
SCOPE_OPENERS = frozenset({
    "ELSE",
    "WHEN",
    "THEN",
    "END-IF",
    "END-PERFORM",
    "END-EVALUATE",
    "END-READ",
    "END-SEARCH",
    "END-STRING",
    "END-UNSTRING",
    "END-WRITE",
    "END-CALL",
    "END-ADD",
    "END-SUBTRACT",
    "END-MULTIPLY",
    "END-DIVIDE",
    "END-COMPUTE",
    "END-EXEC",
    "AT",
    "NOT",
})

# EXEC SQL ... END-EXEC is ONE statement whatever its punctuation. It
# never terminates on a period and must never be split mid-block.
EXEC_SQL_START = "EXEC SQL"
EXEC_SQL_END = "END-EXEC"

SENTENCE_TERMINATOR = "."

# Upper bound on physical lines in one logical statement. A longer run
# almost always means a missing period, and an unbounded scan absorbs -
# and in the callers that delete spans, destroys - the rest of the
# program. Generous: a DECLARE CURSOR legitimately runs long.
JOIN_MAX_LINES = 24

JOINER_MESSAGES = {
    "runaway": (
        "Statement joiner: a statement opening at physical line {line} "
        "ran past {limit} lines; it was cut there. A missing sentence "
        "terminator is the usual cause."
    ),
    "summary": (
        "Statement joiner: {total} logical statement(s) from {lines} "
        "physical line(s); {wrapped} spanned more than one."
    ),
}

__all__ = [
    "CONTINUATION_OPENERS",
    "CONTINUATION_TRAILERS",
    "STATEMENT_VERBS",
    "IDMS_STATEMENT_VERBS",
    "SCOPE_OPENERS",
    "EXEC_SQL_START",
    "EXEC_SQL_END",
    "SENTENCE_TERMINATOR",
    "JOIN_MAX_LINES",
    "JOINER_MESSAGES",
]
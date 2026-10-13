"""Source-based program-kind detection for the review step.

The batch review path (zowe pipeline) runs over a folder of generated .cbl
files and passes a single, global ``--kind`` of UNKNOWN. A program's kind is a
per-program fact, not a per-run one, so every UPDATE program was reviewed as
UNKNOWN and its UPDATE-only checks (record modification, audit column / date
handling, restart structure) were silently skipped.

This detector recovers the kind from evidence that survives conversion:

* An explicit ``USAGE-MODE IS UPDATE|RETRIEVAL`` in the original source wins.
* An IDMS write verb (STORE / MODIFY / ERASE <record>) or a DB2 write statement
  (INSERT / UPDATE / DELETE issued through EXEC SQL) means the program changes
  data -> UPDATE. Write intent takes precedence, because a retrieval-only
  program never writes, whereas an update program routinely reads first.
* Otherwise an IDMS retrieval verb (OBTAIN / FIND) or a DB2 cursor / singleton
  read (DECLARE / FETCH / OPEN / SELECT) means -> RETRIEVAL.
* No evidence at all stays UNKNOWN.

The IDMS verb patterns require "VERB <record>", so paragraph names such as
210-STORE-EFF (STORE not followed by whitespace) never trigger a false match.
No program, record, table, column or host-variable name is hardcoded.

CORRECTION - \\b matched inside a hyphenated host variable
---------------------------------------------------------
The write pattern read ``\\b(?:INSERT|UPDATE|DELETE)\\b``. A hyphen is NOT a
word character, so inside a perfectly ordinary RETRIEVAL cursor

    EXEC SQL
      DECLARE C1 CURSOR FOR
      SELECT TS_UPDATE_479BFAR
        INTO :DCLDZBFARTV.TS-UPDATE-479BFAR

the host variable TS-UPDATE-479BFAR offered \\bUPDATE\\b a clean match and the
program was classified UPDATE. The underscore COLUMN form was safe; the
hyphenated COBOL HOST form was not, and TS_UPDATE / ID_USERID audit columns
are a site standard, so this would misfire on real retrieval programs.

A verb now counts only when it stands as a STATEMENT verb:

* it is not glued to a COBOL data name on either side, and
* it is followed by a DB2 object name.

This is the same lesson recorded elsewhere in the project: a substring must
never stand in for the real question.
"""

from __future__ import annotations

import re

from review.engine.context import (
    KIND_RETRIEVAL,
    KIND_UNKNOWN,
    KIND_UPDATE,
)
from review.standards.cobol_standards import (
    CURSOR_DECLARE_VERB,
    RETRIEVAL_SQL_VERBS,
    WRITE_SQL_VERBS,
)
from patterns.idms_patterns import (
    ERASE_PATTERN,
    FIND_CURRENT_PATTERN,
    FIND_FIRST_PATTERN,
    MODIFY_PATTERN,
    OBTAIN_CALC_PATTERN,
    OBTAIN_CALC_REVERSED_PATTERN,
    OBTAIN_FIRST_NEXT_PATTERN,
    STORE_PATTERN,
    USAGE_MODE_PATTERN,
)

_UPDATE_IDMS_PATTERNS = (STORE_PATTERN, MODIFY_PATTERN, ERASE_PATTERN)
_RETRIEVAL_IDMS_PATTERNS = (
    OBTAIN_CALC_PATTERN,
    OBTAIN_CALC_REVERSED_PATTERN,
    OBTAIN_FIRST_NEXT_PATTERN,
    FIND_FIRST_PATTERN,
    FIND_CURRENT_PATTERN,
)

# How far past EXEC SQL a verb may sit and still belong to that block.
# Fixed-format sequence areas and line breaks sit between the two, so the
# window is generous; it is bounded so a later block cannot be claimed.
_EXEC_SQL_WINDOW = r"EXEC\s+SQL[\s\S]{0,240}?"

# A COBOL data name is built from letters, digits and hyphens; a DB2 name
# from letters, digits and underscores. Forbidding BOTH on either side of
# the verb is what separates the statement UPDATE from the fragment
# -UPDATE- inside TS-UPDATE-479BFAR and TS_UPDATE_479BFAR.
_NOT_NAME_BEFORE = r"(?<![A-Z0-9_-])"
_NOT_NAME_AFTER = r"(?![A-Z0-9_-])"

# A write verb is followed by the object it writes: INSERT INTO <table>,
# UPDATE <table>, DELETE FROM <table>. The optional INTO / FROM keeps the
# expression correct whether WRITE_SQL_VERBS carries bare verbs or the
# two-word forms.
_DB2_OBJECT = r"\s+(?:INTO\s+|FROM\s+)?[A-Z][A-Z0-9_]*\b"

_EXEC_SQL_WRITE_PATTERN = re.compile(
    _EXEC_SQL_WINDOW
    + _NOT_NAME_BEFORE
    + r"(?:" + "|".join(WRITE_SQL_VERBS) + r")"
    + _NOT_NAME_AFTER
    + _DB2_OBJECT,
    flags=re.IGNORECASE,
)

# Read verbs take the same name guards. A read match only decides the
# outcome when there is no write evidence at all, but a flag-name such as
# WS-OPEN-SWITCH must still not be mistaken for OPEN.
_EXEC_SQL_READ_PATTERN = re.compile(
    _EXEC_SQL_WINDOW
    + _NOT_NAME_BEFORE
    + r"(?:" + "|".join((*RETRIEVAL_SQL_VERBS, CURSOR_DECLARE_VERB)) + r")"
    + _NOT_NAME_AFTER,
    flags=re.IGNORECASE,
)


def _has_update_evidence(text: str) -> bool:
    if _EXEC_SQL_WRITE_PATTERN.search(text):
        return True
    return any(pattern.search(text) for pattern in _UPDATE_IDMS_PATTERNS)


def _has_retrieval_evidence(text: str) -> bool:
    if _EXEC_SQL_READ_PATTERN.search(text):
        return True
    return any(pattern.search(text) for pattern in _RETRIEVAL_IDMS_PATTERNS)


def detect_program_kind(converted_cobol: str, source_cobol: str = "") -> str:
    """Return KIND_UPDATE, KIND_RETRIEVAL or KIND_UNKNOWN from program text."""
    source = str(source_cobol or "")

    explicit = USAGE_MODE_PATTERN.search(source)
    if explicit:
        mode = explicit.group(1).upper()
        return KIND_UPDATE if mode == "UPDATE" else KIND_RETRIEVAL

    text = source + "\n" + str(converted_cobol or "")

    if _has_update_evidence(text):
        return KIND_UPDATE
    if _has_retrieval_evidence(text):
        return KIND_RETRIEVAL
    return KIND_UNKNOWN


__all__ = ["detect_program_kind"]
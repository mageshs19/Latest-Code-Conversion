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
"""

from __future__ import annotations

import re

from code_review.engine.context import (
    KIND_RETRIEVAL,
    KIND_UNKNOWN,
    KIND_UPDATE,
)
from code_review.standards.cobol_standards import (
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

# A DB2 verb only counts when it is issued through EXEC SQL, so the word
# UPDATE inside a DISPLAY literal or comment cannot masquerade as a write.
_EXEC_SQL_WRITE_PATTERN = re.compile(
    r"EXEC\s+SQL[\s\S]{0,240}?\b(?:" + "|".join(WRITE_SQL_VERBS) + r")\b",
    flags=re.IGNORECASE,
)
_EXEC_SQL_READ_PATTERN = re.compile(
    r"EXEC\s+SQL[\s\S]{0,240}?\b(?:"
    + "|".join((*RETRIEVAL_SQL_VERBS, CURSOR_DECLARE_VERB))
    + r")\b",
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

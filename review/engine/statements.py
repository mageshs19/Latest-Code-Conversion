# LOCATION: review/engine/statements.py
# ACTION: CREATE NEW FILE
"""Joins COBOL statements that span several physical lines.

WHY THIS EXISTS

sql_blocks.logical_statements joins EXEC SQL ... END-EXEC only. A COBOL
statement split at a word boundary is not joined by anything, so every
check that matches a loop keyword and its condition on ONE physical line
fails correct code. The manual reference program splits exactly this way:

    PERFORM 820-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC OR
                                     SW-STATUS-D = 'Y'

CHK-14.05 was corrected for this individually; CHK-15.06, CHK-19 and
CHK-30 were not. Four checks, one question - this is the single owner.

A statement STARTS at a line whose first word is a COBOL verb, a
paragraph header, or a scope terminator. Any other line continues the
statement before it. A line ending in a period closes the statement.
Deliberately conservative: an unrecognised line continues rather than
starts, because a false JOIN only widens a search window, while a false
SPLIT reintroduces the defect this module removes.
"""

from __future__ import annotations

from review.engine import sql_blocks as sql
from review.standards import cobol_standards as std

MAX_CONTINUATION_LINES = 6
SENTENCE_TERMINATOR = "."


def _starts_statement(text: str) -> bool:
    if not text:
        return False
    word = text.split()[0].rstrip(SENTENCE_TERMINATOR).upper()
    if word in std.NON_PARAGRAPH_WORDS:
        return True
    return text.rstrip().endswith(SENTENCE_TERMINATOR) and " " not in text


def joined_statements(view) -> list[tuple[int, str]]:
    """[(index of first physical line, whole statement text), ...].

    The index is preserved so a check can still report a line number.
    """
    out: list[tuple[int, str]] = []
    start = -1
    buffer: list[str] = []

    for index, line in enumerate(view.code):
        text = sql.norm(line.logical)
        if not text:
            continue

        if not buffer or _starts_statement(text) or (
            len(buffer) > MAX_CONTINUATION_LINES
        ):
            if buffer:
                out.append((start, " ".join(buffer)))
            start, buffer = index, [text]
        else:
            buffer.append(text)

        if text.rstrip().endswith(SENTENCE_TERMINATOR):
            out.append((start, " ".join(buffer)))
            start, buffer = -1, []

    if buffer:
        out.append((start, " ".join(buffer)))

    return out


__all__ = ["joined_statements"]
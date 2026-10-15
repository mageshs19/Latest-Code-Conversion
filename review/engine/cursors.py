# LOCATION: review/engine/cursors.py
# ACTION: REPLACE ENTIRE FILE
"""Shared cursor parsing for checks.

Recognises the two shapes the converter emits:

    EXEC SQL
        DECLARE <cursor> CURSOR WITH HOLD FOR
        SELECT ... FROM <table> ... FOR READ ONLY
    END-EXEC.

    710-OPEN-<cursor>.
    720-FETCH-<cursor>.
    730-CLOSE-<cursor>.

Read-only. Knows nothing about standards or wording.

CORRECTION - THREE FUNCTIONS WERE DEFINED TWICE

open_statements, close_statements and cursor_name each appeared twice:
once in the middle of the module with the full CHK-27 rationale, and
again at the end with a one-line docstring. Python keeps the LAST
definition, so the richly documented copies were DEAD TEXT that still
read as authoritative - editing them changed nothing.

The two sets were behaviourally identical (same comprehension, different
loop variable), so the merge is safe. The surviving definitions carry the
CHK-27 rationale, which is the part that was worth keeping.

Same defect, same resolution, as the duplicate-assignment correction in
rules/db2_infrastructure_rules.py. NO FUNCTION MAY BE DEFINED TWICE IN
THIS MODULE.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from review.engine import sql_blocks as sql

DECLARE = re.compile(
    r"\bDECLARE\s+(?P<cursor>[A-Z][A-Z0-9-]*)\s+CURSOR\b"
)
PARAGRAPH = re.compile(
    r"^(?P<number>\d{3,6})-"
    r"(?P<operation>OPEN|FETCH|CLOSE)-"
    r"(?P<cursor>[A-Z0-9][A-Z0-9-]*)\.$"
)
PERFORM = re.compile(
    r"^PERFORM\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\b(?P<rest>.*)$"
)
CURSOR_VERB = re.compile(
    r"\b(?P<operation>OPEN|FETCH|CLOSE)\s+(?P<cursor>[A-Z][A-Z0-9-]*)\b"
)

# COBOL scope terminators that look like a paragraph header because they
# are a single word followed by a period. These are language facts, not
# site standards, so they live here rather than in standards/. A caller
# may pass a fuller list through stop_words.
SCOPE_TERMINATORS = frozenset({
    "CONTINUE", "END-EXEC", "END-EVALUATE", "END-IF", "END-PERFORM",
    "END-READ", "END-SEARCH", "END-STRING", "END-WRITE", "EXIT",
    "GOBACK", "STOP",
})


@dataclass(frozen=True)
class CursorParagraph:
    """One generated cursor paragraph header."""

    number: int
    operation: str
    cursor: str
    line_number: int
    name: str

    def render(self) -> str:
        return str(self)

    def __str__(self) -> str:
        """One readable evidence line.

        The Recorder turns anything that is not a Line or Finding into
        Finding(text=str(item)), so without this the whole dataclass repr
        would land in the report.
        """
        return f"line {self.line_number:>5} : {self.name}"


def declared_cursors(view) -> dict[str, sql.SqlBlock]:
    """Cursor name -> its DECLARE block."""
    out: dict[str, sql.SqlBlock] = {}
    for block in sql.sql_blocks(view):
        if block.verb != "DECLARE":
            continue
        match = DECLARE.search(block.text)
        if match:
            out.setdefault(match.group("cursor").upper(), block)
    return out


def declare_blocks(view) -> list[sql.SqlBlock]:
    return [b for b in sql.sql_blocks(view) if b.verb == "DECLARE"]


def cursor_paragraphs(view) -> list[CursorParagraph]:
    """Every generated cursor paragraph header, in source order."""
    out: list[CursorParagraph] = []
    for line in view.code:
        logical = sql.norm(line.logical)
        match = PARAGRAPH.match(logical)
        if not match:
            continue
        out.append(CursorParagraph(
            number=int(match.group("number")),
            operation=match.group("operation").upper(),
            cursor=match.group("cursor").upper(),
            line_number=line.number,
            name=logical.rstrip("."),
        ))
    return out


def paragraph_sets(view) -> dict[str, dict[str, CursorParagraph]]:
    """Cursor name -> {OPEN: para, FETCH: para, CLOSE: para}."""
    out: dict[str, dict[str, CursorParagraph]] = {}
    for para in cursor_paragraphs(view):
        out.setdefault(para.cursor, {})[para.operation] = para
    return out


def performed_names(view) -> dict[str, list]:
    """Performed paragraph name -> the lines that perform it."""
    out: dict[str, list] = {}
    for line in view.code:
        match = PERFORM.match(sql.norm(line.logical))
        if match:
            out.setdefault(match.group("name").upper(), []).append(line)
    return out


def cursors_used(view, operation: str) -> set[str]:
    """Cursor names appearing in an EXEC SQL OPEN / FETCH / CLOSE."""
    wanted = str(operation or "").upper()
    out: set[str] = set()
    for block in sql.sql_blocks(view):
        if block.verb != wanted:
            continue
        match = CURSOR_VERB.search(block.text)
        if match:
            out.add(match.group("cursor").upper())
    return out


def open_statements(view) -> list[sql.SqlBlock]:
    """Every EXEC SQL OPEN block, in source order.

    Added for CHK-27 (cursor lifecycle), which pairs each OPEN with its
    CLOSE. Returns the SQL blocks rather than cursor names so the check
    can report the offending line.
    """
    return [block for block in sql.sql_blocks(view) if block.verb == "OPEN"]


def close_statements(view) -> list[sql.SqlBlock]:
    """Every EXEC SQL CLOSE block, in source order.

    Added for CHK-27, which pairs each OPEN with its CLOSE. A declared
    cursor opened and never closed leaks the result set; with WITH HOLD
    it survives COMMIT, so a long batch abends on resource limits.
    """
    return [block for block in sql.sql_blocks(view) if block.verb == "CLOSE"]


def cursor_name(block) -> str:
    """The cursor named by an OPEN / FETCH / CLOSE block.

    Returns "" when the block names no cursor, so a caller can build a
    name set without guarding every element.
    """
    match = CURSOR_VERB.search(getattr(block, "text", "") or "")
    return match.group("cursor").upper() if match else ""


def is_paragraph_header(logical: str, stop_words) -> bool:
    """A single word plus a period that is not a scope terminator.

    END-EXEC. and CONTINUE. look identical to a paragraph header at the
    token level. Treating them as one truncates every paragraph body at
    the first EXEC SQL block.
    """
    text = str(logical or "").strip()
    if not text.endswith(".") or " " in text:
        return False
    name = text[:-1]
    if not name:
        return False
    if name in SCOPE_TERMINATORS:
        return False
    return name not in (stop_words or frozenset())


def paragraph_body(view, para: CursorParagraph, stop_words=None) -> list[str]:
    """Normalised lines of a paragraph, up to the next paragraph header."""
    words = stop_words if stop_words is not None else frozenset()
    code = view.code
    start = next(
        (
            index for index, line in enumerate(code)
            if line.number == para.line_number
        ),
        -1,
    )
    if start < 0:
        return []

    out: list[str] = []
    for line in code[start + 1:]:
        logical = sql.norm(line.logical)
        if PARAGRAPH.match(logical):
            break
        if is_paragraph_header(logical, words):
            break
        out.append(logical)
    return out


__all__ = [
    "CursorParagraph",
    "SCOPE_TERMINATORS",
    "close_statements",
    "cursor_name",
    "cursor_paragraphs",
    "cursors_used",
    "declare_blocks",
    "declared_cursors",
    "is_paragraph_header",
    "open_statements",
    "paragraph_body",
    "paragraph_sets",
    "performed_names",
]
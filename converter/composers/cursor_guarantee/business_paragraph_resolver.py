# LOCATION: converter/composers/cursor_guarantee/business_paragraph_resolver.py
# ACTION: CREATE NEW FILE

"""Resolves the business paragraph a cursor's row logic lives in.

WHY THE COMPOSER OWNS THIS
--------------------------
CursorRepair.bind_fetch_to_business is reachable only from
synthesise_loop, which runs on Path C. A cursor that already had a
driving loop took Path A or B, both of which deliberately never touch the
business paragraph, so the FETCH kept WHEN ZERO / CONTINUE and the
business paragraph became UNREACHABLE. Resolution therefore has to be
available before path selection, which is why it is a separate read-only
collaborator rather than a private method on the synthesiser.

RESOLUTION
----------
The business paragraph is the first NON-GENERATED paragraph that follows
the paragraph performing the cursor OPEN. In the COBOL team's manual
reference that is exactly the paragraph the FETCH performs:

        PERFORM 710-OPEN-DZBEFFC1          <- mainline
        PERFORM 720-FETCH-DZBEFFC1 UNTIL DZBEFFC1-EOC
        PERFORM 730-CLOSE-DZBEFFC1
    ...
 HOOFDVERWERKING.                          <- first non-generated after it

The candidate is then VERIFIED. It must either reference the cursor's own
DCLGEN group or open a nested cursor. An unverified candidate is reported
and refused, never guessed, per CONVERSION_RULES:

    "Do not fabricate DB2 SQL when Sheet Mapping metadata is missing."

READ-ONLY
---------
This class never mutates `lines`. Every mutation belongs to
cursor_guarantee/cursor_repair.py.

SELF-CONTAINED BY DESIGN
------------------------
It depends on CursorLines for logical() and is_comment() only, and falls
back to its own implementation when either is absent. The package has
shipped in two internal layouts; a resolver that reaches deeper would
break on the next one.

No program, paragraph, record, table, cursor or host variable name is
hardcoded here.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------
# Fixed-format geometry, used only by the fallback helpers
# ---------------------------------------------------------------------
BODY_START = 7
BODY_END = 72
COMMENT_INDICATORS = ("*", "/")

# ---------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------
_NAME = r"[A-Z0-9][A-Z0-9-]*"

PARAGRAPH_HEADER_PATTERN = re.compile(
    rf"^(?P<name>{_NAME})\s*\.$", re.IGNORECASE
)
SECTION_HEADER_PATTERN = re.compile(
    rf"^(?P<name>{_NAME})\s+SECTION\s*\.$", re.IGNORECASE
)
DIVISION_PATTERN = re.compile(r"^[A-Z]+\s+DIVISION\b", re.IGNORECASE)

# 710-OPEN-DZBEFFC1 / 720-FETCH-DZBEFFC1 / 730-CLOSE-DZBEFFC1
CURSOR_PARAGRAPH_PATTERN = re.compile(
    rf"^\d{{3,6}}-(?:OPEN|FETCH|CLOSE)-(?P<cursor>{_NAME})$", re.IGNORECASE
)
PERFORM_CURSOR_OPEN_PATTERN = re.compile(
    rf"^PERFORM\s+\d{{3,6}}-OPEN-(?P<cursor>{_NAME})\b", re.IGNORECASE
)

# A DCLGEN host reference inside a FETCH INTO list: :DCLDZBEFFTV.FIELD
HOST_GROUP_REFERENCE_PATTERN = re.compile(
    r":(?P<group>DCL[A-Z0-9]+)\.", re.IGNORECASE
)

END_EXEC_PATTERN = re.compile(r"^END-EXEC\b", re.IGNORECASE)

# Single words ending in a period that are NOT paragraph headers.
NON_PARAGRAPH_WORDS = frozenset({
    "CONTINUE", "EXIT", "GOBACK", "STOP", "END-IF", "END-EVALUATE",
    "END-EXEC", "END-PERFORM", "END-READ", "END-SEARCH", "END-STRING",
    "END-WRITE",
})

# Generated utility paragraphs. None of them is business logic.
GENERATED_PARAGRAPH_TOKENS = (
    "INITIALIZE",
    "GET-TIMESTAMP",
    "DISPLAY-TOTALS",
    "SQLERROR",
    "SQL-ERROR",
    "WRITE-",
)


class BusinessParagraphResolver:
    """Finds and verifies the business paragraph of one cursor."""

    def __init__(self, lines_utils=None, log=None) -> None:
        self.lines_utils = lines_utils
        self.log = log

    # =================================================================
    # Public entry point
    # =================================================================
    def resolve(self, lines: list[str], cursor_set) -> str:
        """The verified business paragraph, or '' when unresolved."""
        if not lines or cursor_set is None:
            return ""

        open_name = str(getattr(cursor_set, "open_name", "") or "")
        fetch_name = str(getattr(cursor_set, "fetch_name", "") or "")
        cursor = str(getattr(cursor_set, "cursor", "") or "")

        if not open_name:
            return ""

        spans = self.paragraph_spans(lines)
        if not spans:
            return ""

        host = self._index_performing(lines, spans, open_name)
        if host < 0:
            return ""

        group = self.dclgen_group(lines, fetch_name)

        for name, start, end in spans[host + 1:]:
            if self.is_generated(name):
                continue

            if self._verifies(lines, start, end, cursor, group):
                return name

            self._log(
                "business_paragraph_unverified",
                cursor=cursor,
                paragraph=name,
            )
            return ""

        return ""

    # =================================================================
    # Paragraph navigation
    # =================================================================
    def paragraph_name(self, line: str) -> str:
        """The paragraph or section name on this line, or ''."""
        logical = self._logical(line)
        if not logical or self._is_comment(logical):
            return ""

        if DIVISION_PATTERN.match(logical):
            return ""

        match = (
            PARAGRAPH_HEADER_PATTERN.match(logical)
            or SECTION_HEADER_PATTERN.match(logical)
        )
        if not match:
            return ""

        name = match.group("name").upper()
        return "" if name in NON_PARAGRAPH_WORDS else name

    def paragraph_spans(self, lines: list[str]) -> list[tuple]:
        """(name, first_index, last_index) for every paragraph, in order."""
        spans: list[tuple] = []
        current = ""
        start = -1

        for index, line in enumerate(lines):
            name = self.paragraph_name(line)
            if not name:
                continue
            if current:
                spans.append((current, start, index - 1))
            current, start = name, index

        if current:
            spans.append((current, start, len(lines) - 1))

        return spans

    @staticmethod
    def is_generated(name: str) -> bool:
        """A generated cursor or utility paragraph is never business logic."""
        clean = str(name or "").upper()
        if not clean:
            return True
        if CURSOR_PARAGRAPH_PATTERN.match(clean):
            return True
        return any(token in clean for token in GENERATED_PARAGRAPH_TOKENS)

    # =================================================================
    # DCLGEN group
    # =================================================================
    def dclgen_group(self, lines: list[str], fetch_paragraph: str) -> str:
        """The group the FETCH reads into, taken from its own INTO list.

        Read from the statement itself rather than from a resolver, so it
        is always the group this very FETCH writes into.
        """
        if not fetch_paragraph:
            return ""

        span = self._span_of(lines, fetch_paragraph)
        if span is None:
            return ""

        start, end = span
        for index in range(start, end + 1):
            logical = self._logical(lines[index])
            if not logical or self._is_comment(logical):
                continue

            match = HOST_GROUP_REFERENCE_PATTERN.search(logical)
            if match:
                return match.group("group").upper()

            if END_EXEC_PATTERN.match(logical):
                break

        return ""

    # =================================================================
    # Helpers
    # =================================================================
    def _span_of(self, lines: list[str], paragraph: str):
        target = str(paragraph or "").upper()
        for name, start, end in self.paragraph_spans(lines):
            if name == target:
                return start, end
        return None

    def _index_performing(
        self,
        lines: list[str],
        spans: list[tuple],
        paragraph: str,
    ) -> int:
        """Position in `spans` of the paragraph that performs `paragraph`."""
        target = f"PERFORM {paragraph}".upper()

        for position, (_name, start, end) in enumerate(spans):
            for index in range(start, end + 1):
                logical = self._logical(lines[index])
                if not logical or self._is_comment(logical):
                    continue
                if logical.upper().startswith(target):
                    return position

        return -1

    def _verifies(
        self,
        lines: list[str],
        start: int,
        end: int,
        cursor: str,
        group: str,
    ) -> bool:
        """True when the candidate really is this cursor's row logic."""
        for index in range(start, end + 1):
            logical = self._logical(lines[index])
            if not logical or self._is_comment(logical):
                continue

            upper = logical.upper()

            # It consumes the row this cursor fetched.
            if group and group in upper:
                return True

            # Or it drives a nested cursor, which makes it the parent's
            # row paragraph.
            match = PERFORM_CURSOR_OPEN_PATTERN.match(upper)
            if match and match.group("cursor").upper() != str(cursor).upper():
                return True

        return False

    # =================================================================
    # Line access - delegated, with a self-contained fallback
    # =================================================================
    def _logical(self, line: str) -> str:
        getter = getattr(self.lines_utils, "logical", None)
        if callable(getter):
            try:
                return str(getter(line) or "").strip()
            except Exception:  # noqa: BLE001 - never abort a scan
                pass
        return self._fallback_logical(line)

    def _is_comment(self, logical: str) -> bool:
        checker = getattr(self.lines_utils, "is_comment", None)
        if callable(checker):
            try:
                return bool(checker(logical))
            except Exception:  # noqa: BLE001
                pass
        text = str(logical or "").lstrip()
        return text[:1] in COMMENT_INDICATORS

    @staticmethod
    def _fallback_logical(line: str) -> str:
        """Columns 8-72 of a fixed-format record, else the stripped line."""
        text = str(line or "").rstrip("\r\n")
        if not text:
            return ""
        if len(text) > BODY_START and text[:6].isdigit():
            if text[6:7] in COMMENT_INDICATORS:
                return text[6:7]
            return text[BODY_START:BODY_END].strip()
        return text.strip()

    def _log(self, key: str, **values) -> None:
        if self.log is None:
            return
        logger = getattr(self.log, "log", None)
        if not callable(logger):
            return
        try:
            logger(key, **values)
        except Exception:  # noqa: BLE001 - a diagnostic must never abort
            pass


__all__ = ["BusinessParagraphResolver"]
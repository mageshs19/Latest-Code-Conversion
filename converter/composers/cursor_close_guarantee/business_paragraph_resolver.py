# LOCATION: converter/composers/cursor_close_guarantee/business_paragraph_resolver.py
# ACTION: CREATE NEW FILE
"""Resolves the business paragraph a cursor's row logic lives in.

The composer needs this on EVERY repair path, not only on synthesis, so
it cannot stay inside LoopSynthesiser.

RESOLUTION

The business paragraph is the first NON-GENERATED paragraph that follows
the paragraph performing the cursor OPEN. In the COBOL team's manual
reference that is exactly the paragraph 720-FETCH performs.

The candidate is then VERIFIED. It must either reference the cursor's own
DCLGEN group or open a nested cursor. An unverified candidate is refused
and reported, never guessed, per CONVERSION_RULES.

No program, paragraph, record, table, cursor or host variable name is
hardcoded. Regex lives in patterns/.
"""

from __future__ import annotations

from converter.composers.cursor_close_guarantee.line_utils import (
    CursorGuaranteeLineUtils,
)
from converter.composers.cursor_close_guarantee.message_log import MessageLog
from converter.composers.cursor_close_guarantee.models import (
    CursorParagraphSet,
)
from patterns.cursor_close_guarantee_patterns import (
    CURSOR_PARAGRAPH_HEADER_PATTERN,
    HOST_GROUP_REFERENCE_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PERFORM_CURSOR_PARAGRAPH_PATTERN,
    SECTION_HEADER_PATTERN,
)
from rules.cursor_close_guarantee_rules import NON_PARAGRAPH_SINGLE_WORDS

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

    def __init__(
        self,
        line_utils: CursorGuaranteeLineUtils | None = None,
        log: MessageLog | None = None,
    ) -> None:
        self.lines_utils = line_utils or CursorGuaranteeLineUtils()
        self.log = log or MessageLog()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def resolve(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
    ) -> str:
        spans = self.paragraph_spans(lines)
        if not spans:
            return ""

        host = self._index_performing(lines, spans, cursor_set.open_name)
        if host < 0:
            return ""

        group = self.dclgen_group(lines, cursor_set)

        for name, start, end in spans[host + 1:]:
            if self.is_generated(name):
                continue
            if self._verifies(lines, start, end, cursor_set.cursor, group):
                return name
            self.log.log(
                "business_paragraph_unverified",
                cursor=cursor_set.cursor,
                paragraph=name,
            )
            return ""

        return ""

    # ------------------------------------------------------------------
    # Paragraph navigation
    # ------------------------------------------------------------------

    def paragraph_name(self, line: str) -> str:
        logical = self.lines_utils.logical(line)
        if not logical or self.lines_utils.is_comment(logical):
            return ""

        match = (
            PARAGRAPH_HEADER_PATTERN.match(logical)
            or SECTION_HEADER_PATTERN.match(logical)
        )
        if not match:
            return ""

        name = match.group("name").upper()
        return "" if name in NON_PARAGRAPH_SINGLE_WORDS else name

    def paragraph_spans(self, lines: list[str]) -> list[tuple]:
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
        """A generated utility or cursor paragraph is never business logic."""
        clean = str(name or "").upper()
        if CURSOR_PARAGRAPH_HEADER_PATTERN.match(f"{clean}."):
            return True
        return any(token in clean for token in GENERATED_PARAGRAPH_TOKENS)

    # ------------------------------------------------------------------
    # DCLGEN group
    # ------------------------------------------------------------------

    def dclgen_group(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
    ) -> str:
        """The group the FETCH reads into, taken from its own INTO list."""
        target = str(cursor_set.fetch_name or "").upper()
        if not target:
            return ""

        inside = False
        for line in lines:
            logical = self.lines_utils.logical(line)
            if not logical:
                continue

            if self.paragraph_name(line) == target:
                inside = True
                continue
            if not inside:
                continue

            match = HOST_GROUP_REFERENCE_PATTERN.search(logical)
            if match:
                return match.group("group").upper()

            if logical.upper().startswith("END-EXEC"):
                break

        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _index_performing(
        self,
        lines: list[str],
        spans: list[tuple],
        paragraph: str,
    ) -> int:
        target = f"PERFORM {paragraph}".upper()

        for position, (_name, start, end) in enumerate(spans):
            for index in range(start, end + 1):
                logical = self.lines_utils.logical(lines[index])
                if logical and logical.upper().startswith(target):
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
        for index in range(start, end + 1):
            logical = self.lines_utils.logical(lines[index])
            if not logical or self.lines_utils.is_comment(logical):
                continue

            upper = logical.upper()
            if group and group in upper:
                return True

            match = PERFORM_CURSOR_PARAGRAPH_PATTERN.match(logical)
            if match and match.group("cursor").upper() != str(cursor).upper():
                return True

        return False


__all__ = ["BusinessParagraphResolver"]
# LOCATION: converter/composers/cursor_close_guarantee/fetch_business_binder.py
# ACTION: CREATE NEW FILE
"""Binds a generated FETCH paragraph to its business paragraph.

WHY THIS EXISTS
---------------
LoopSynthesiser._bind_fetch_to_business is documented as "used only when
no driving loop exists at all" and is reachable ONLY from synthesise().
A cursor that already has a driving loop takes the span / close-guarantor
path, which "never restructures the loop, never moves the business
paragraph" - and therefore never binds WHEN ZERO either.

The FETCH keeps CONTINUE, the business paragraph is never performed, and
the program fetches every row and does nothing with it. No diagnostic
appears because business_paragraph_unknown is also logged only inside the
synthesiser.

Binding is PATH-INDEPENDENT and belongs outside the synthesiser.

DELIBERATELY SELF-CONTAINED
---------------------------
No import of CursorLines, CursorGuaranteeLineUtils, ParagraphIndex,
CursorRepair or any rules module, because the package has shipped in two
different internal layouts. This module takes a list of physical lines
and returns one, so it cannot break when the internals change.

REFUSES RATHER THAN GUESSES
---------------------------
A candidate business paragraph must VERIFY: it either references the
cursor's own DCLGEN group, or it opens a nested cursor. An unverified
candidate is reported and the FETCH is left unchanged.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set, Tuple

# ---------------------------------------------------------------------
# Fixed-format geometry
# ---------------------------------------------------------------------
LINE_WIDTH = 80
BODY_START = 7
BODY_END = 72
COMMENT_INDICATORS = ("*", "/")

PERFORM_BUSINESS_TEMPLATE = "PERFORM {paragraph}"

# ---------------------------------------------------------------------
# Regex
# ---------------------------------------------------------------------
_NAME = r"[A-Z0-9][A-Z0-9-]*"

WHEN_ZERO_PATTERN = re.compile(
    r"^WHEN\s+(?:ZERO|ZEROS|ZEROES|0)\s*$", re.IGNORECASE
)
ANY_WHEN_PATTERN = re.compile(r"^WHEN\b", re.IGNORECASE)
END_EVALUATE_PATTERN = re.compile(r"^END-EVALUATE\b", re.IGNORECASE)
CONTINUE_PATTERN = re.compile(r"^CONTINUE\s*\.?$", re.IGNORECASE)

PARAGRAPH_HEADER_PATTERN = re.compile(
    rf"^(?P<name>{_NAME})\s*\.$", re.IGNORECASE
)
SECTION_HEADER_PATTERN = re.compile(
    rf"^(?P<name>{_NAME})\s+SECTION\s*\.$", re.IGNORECASE
)
DIVISION_PATTERN = re.compile(r"^[A-Z]+\s+DIVISION\b", re.IGNORECASE)

CURSOR_PARAGRAPH_PATTERN = re.compile(
    rf"^\d{{3,6}}-(?:OPEN|FETCH|CLOSE)-(?P<cursor>{_NAME})$", re.IGNORECASE
)
PERFORM_CURSOR_OPEN_PATTERN = re.compile(
    rf"^PERFORM\s+\d{{3,6}}-OPEN-(?P<cursor>{_NAME})\b", re.IGNORECASE
)
HOST_GROUP_REFERENCE_PATTERN = re.compile(
    r":(?P<group>DCL[A-Z0-9]+)\.", re.IGNORECASE
)

NON_PARAGRAPH_WORDS = frozenset({
    "CONTINUE", "EXIT", "GOBACK", "STOP", "END-IF", "END-EVALUATE",
    "END-EXEC", "END-PERFORM", "END-READ", "END-SEARCH", "END-STRING",
    "END-WRITE",
})

GENERATED_PARAGRAPH_TOKENS = (
    "INITIALIZE",
    "GET-TIMESTAMP",
    "DISPLAY-TOTALS",
    "SQLERROR",
    "SQL-ERROR",
    "WRITE-",
)

MESSAGES = {
    "bound": (
        "Cursor close guarantee: FETCH paragraph {fetch} now performs "
        "business paragraph {paragraph}."
    ),
    "unknown": (
        "Cursor close guarantee: could not identify the business "
        "paragraph for cursor {cursor}; WHEN ZERO left unchanged."
    ),
    "unverified": (
        "Cursor close guarantee: candidate business paragraph {paragraph} "
        "for cursor {cursor} references neither its DCLGEN group nor a "
        "nested cursor; binding refused."
    ),
    "not_bindable": (
        "Cursor close guarantee: the WHEN ZERO branch of {fetch} holds no "
        "CONTINUE to replace; left unchanged."
    ),
}


class FetchBusinessBinder:
    """Replaces CONTINUE under WHEN ZERO with PERFORM <business>."""

    def __init__(self, log=None) -> None:
        self.log = log
        self.messages: List[str] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def bind(
        self,
        lines: List[str],
        cursor: str,
        fetch_paragraph: str,
        open_paragraph: str,
    ) -> Tuple[List[str], str]:
        """Bind one cursor. Returns (lines, business_paragraph_or_empty)."""
        if not fetch_paragraph or not open_paragraph:
            return lines, ""

        business = self.business_paragraph(
            lines, cursor, fetch_paragraph, open_paragraph
        )
        if not business:
            self._note("unknown", cursor=cursor)
            return lines, ""

        return (
            self._bind_when_zero(lines, fetch_paragraph, business),
            business,
        )

    # ------------------------------------------------------------------
    # Line geometry
    # ------------------------------------------------------------------

    @staticmethod
    def _body(line: str) -> str:
        text = str(line or "").rstrip("\r\n")
        if not text:
            return ""
        if len(text) > BODY_START and text[:6].isdigit():
            return text[BODY_START:BODY_END].strip()
        return text.strip()

    @staticmethod
    def _indicator(line: str) -> str:
        text = str(line or "")
        if len(text) > 6 and text[:6].isdigit():
            return text[6:7]
        stripped = text.lstrip()
        return stripped[:1] if stripped[:1] in COMMENT_INDICATORS else " "

    def _is_code(self, line: str) -> bool:
        if self._indicator(line) in COMMENT_INDICATORS:
            return False
        return bool(self._body(line))

    def _replace_body(self, line: str, body: str) -> str:
        """Rewrite columns 8-72 only. Sequence areas are never displaced."""
        text = str(line or "").rstrip("\r\n")

        if len(text) > BODY_START and text[:6].isdigit():
            window = text[BODY_START:BODY_END]
            indent = len(window) - len(window.lstrip())
            width = BODY_END - BODY_START
            new_body = (" " * indent + body)[:width].ljust(width)
            return (
                f"{text[:6]}{text[6:7]}{new_body}"
                f"{text[BODY_END:LINE_WIDTH]}"
            )

        indent = len(text) - len(text.lstrip())
        return " " * indent + body

    # ------------------------------------------------------------------
    # Paragraph navigation
    # ------------------------------------------------------------------

    def paragraph_name(self, line: str) -> str:
        if not self._is_code(line):
            return ""

        body = self._body(line)
        if DIVISION_PATTERN.match(body):
            return ""

        match = (
            PARAGRAPH_HEADER_PATTERN.match(body)
            or SECTION_HEADER_PATTERN.match(body)
        )
        if not match:
            return ""

        name = match.group("name").upper()
        return "" if name in NON_PARAGRAPH_WORDS else name

    def paragraph_spans(self, lines: List[str]) -> List[tuple]:
        spans: List[tuple] = []
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
        clean = str(name or "").upper()
        if CURSOR_PARAGRAPH_PATTERN.match(clean):
            return True
        return any(token in clean for token in GENERATED_PARAGRAPH_TOKENS)

    def span_of(
        self, lines: List[str], paragraph: str
    ) -> Optional[Tuple[int, int]]:
        target = str(paragraph or "").upper()
        for name, start, end in self.paragraph_spans(lines):
            if name == target:
                return start, end
        return None

    # ------------------------------------------------------------------
    # Business paragraph resolution
    # ------------------------------------------------------------------

    def business_paragraph(
        self,
        lines: List[str],
        cursor: str,
        fetch_paragraph: str,
        open_paragraph: str,
    ) -> str:
        """First non-generated paragraph after the one that OPENs.

        In the COBOL team's manual reference that is exactly the paragraph
        720-FETCH performs. The candidate must then verify.
        """
        spans = self.paragraph_spans(lines)
        if not spans:
            return ""

        host = self._index_performing(lines, spans, open_paragraph)
        if host < 0:
            return ""

        group = self.dclgen_group(lines, fetch_paragraph)

        for name, start, end in spans[host + 1:]:
            if self.is_generated(name):
                continue
            if self._verifies(lines, start, end, cursor, group):
                return name
            self._note("unverified", cursor=cursor, paragraph=name)
            return ""

        return ""

    def dclgen_group(self, lines: List[str], fetch_paragraph: str) -> str:
        """The group the FETCH reads into, taken from its own INTO list."""
        span = self.span_of(lines, fetch_paragraph)
        if span is None:
            return ""

        start, end = span
        for index in range(start, end + 1):
            if not self._is_code(lines[index]):
                continue
            body = self._body(lines[index])

            match = HOST_GROUP_REFERENCE_PATTERN.search(body)
            if match:
                return match.group("group").upper()

            if body.upper().startswith("END-EXEC"):
                break

        return ""

    def _index_performing(
        self, lines: List[str], spans: List[tuple], paragraph: str
    ) -> int:
        target = f"PERFORM {paragraph}".upper()

        for position, (_name, start, end) in enumerate(spans):
            for index in range(start, end + 1):
                if not self._is_code(lines[index]):
                    continue
                if self._body(lines[index]).upper().startswith(target):
                    return position

        return -1

    def _verifies(
        self,
        lines: List[str],
        start: int,
        end: int,
        cursor: str,
        group: str,
    ) -> bool:
        for index in range(start, end + 1):
            if not self._is_code(lines[index]):
                continue

            body = self._body(lines[index]).upper()
            if group and group in body:
                return True

            match = PERFORM_CURSOR_OPEN_PATTERN.match(body)
            if match and match.group("cursor").upper() != str(cursor).upper():
                return True

        return False

    # ------------------------------------------------------------------
    # The bind
    # ------------------------------------------------------------------

    def _bind_when_zero(
        self,
        lines: List[str],
        fetch_paragraph: str,
        business: str,
    ) -> List[str]:
        """Replace the CONTINUE in the WHEN ZERO branch. Idempotent.

        Scanning is bounded to the WHEN ZERO body: it stops at the next
        WHEN or at END-EVALUATE, so a CONTINUE belonging to another branch
        can never be claimed.
        """
        span = self.span_of(lines, fetch_paragraph)
        if span is None:
            return lines

        start, end = span
        statement = PERFORM_BUSINESS_TEMPLATE.format(paragraph=business)
        target = self._compress(statement)

        output = list(lines)
        in_when_zero = False

        for index in range(start, end + 1):
            if not self._is_code(output[index]):
                continue

            body = self._body(output[index])

            if WHEN_ZERO_PATTERN.match(body):
                in_when_zero = True
                continue

            if not in_when_zero:
                continue

            if self._compress(body) == target:
                return lines

            if ANY_WHEN_PATTERN.match(body) or END_EVALUATE_PATTERN.match(
                body
            ):
                break

            if CONTINUE_PATTERN.match(body):
                output[index] = self._replace_body(output[index], statement)
                self._note(
                    "bound", fetch=fetch_paragraph, paragraph=business
                )
                return output

        self._note("not_bindable", fetch=fetch_paragraph)
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compress(text: str) -> str:
        return " ".join(str(text or "").split()).upper().rstrip(".")

    def _note(self, key: str, **values) -> None:
        template = MESSAGES.get(key, "")
        if not template:
            return

        message = template.format(**values)
        self.messages.append(message)

        if self.log is None:
            return
        try:
            self.log.messages.append(message)
        except AttributeError:
            pass


__all__ = ["FetchBusinessBinder"]
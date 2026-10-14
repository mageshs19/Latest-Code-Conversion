# LOCATION: converter/composers/cursor_close_guarantee/fetch_business_binder.py
# ACTION: REPLACE ENTIRE FILE
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
and returns one, so it cannot break when the internals change, and it can
be imported from EITHER layout.

REFUSES RATHER THAN GUESSES
---------------------------
A candidate business paragraph must VERIFY: it either references the
cursor's own DCLGEN group, or it opens a nested cursor. An unverified
candidate is reported and the FETCH is left unchanged.

CORRECTION 1 - double-drive recursion
--------------------------------------
Two legal shapes exist, and a program must carry EXACTLY ONE:

  MAINLINE-DRIVEN   PERFORM <business> THRU <business>-EXIT
                            UNTIL <cursor>-EOC.
                    <business> performs <fetch> at its tail
                    <fetch> WHEN ZERO -> CONTINUE

  FETCH-DRIVEN      PERFORM <fetch> UNTIL <cursor>-EOC.
                    <fetch> WHEN ZERO -> PERFORM <business>
                    <business> does NOT fetch

cursor_flow's SPAN strategy is deliberately conservative: "Restructuring
a span loop would rewrite working business flow, which the business-flow
rule forbids." It therefore leaves a mainline-driven program alone. This
binder runs LATER and PATH-INDEPENDENTLY, sees a bare CONTINUE under
WHEN ZERO, and adds the second edge - producing both at once.

COBOL PERFORM holds ONE return address per paragraph. The nested call
overwrites the outer one and the pair loops forever. It compiles clean,
hangs at run time, and every static check passes - CHK-14.05 reported
PASS on exactly such a program - which is why the guard lives here,
before the bind, and SAYS SO when it fires.

CORRECTION 2 - one detector, not two
-------------------------------------
Two methods used to answer one question. _already_span_driven was
defined, documented and never called; _already_driven WAS called but
tested `"UNTIL" in body` on ONE physical line, so it could not see

    PERFORM <business> THRU <business>-EXIT
        UNTIL <cursor>-EOC.

and never fired. Both are replaced by a single detector,
already_externally_driven, which:

  * resolves an UNTIL that continues on the next physical line,
  * accepts the THRU and the THRU-less idiom - a bare
    PERFORM <business> UNTIL <cond> drives just as hard,
  * ignores a driver found INSIDE a generated cursor paragraph, because
    that is this binder's own output and not an external loop, which
    makes the guard idempotent across re-runs,
  * KEEPS BOTH HALVES of the old test: an external driver alone is not
    enough. <business> must also re-fetch at its tail. Refusing to bind
    when nothing fetches would trade a recursion for a stall.

CORRECTION 3 - silent returns
------------------------------
_bind_when_zero returned unchanged lines without a word when the FETCH
paragraph was absent and when the bind was already in place. A silent
pass cannot be reviewed. Both now report.

PUBLIC SURFACE
--------------
    FetchBusinessBinder.bind(...)                    full bind
    FetchBusinessBinder.already_externally_driven(.) the guard alone
    already_externally_driven(...)                   module-level guard

The module-level function exists for a caller that binds through its own
line utilities and message log and only needs the ANSWER. One owner for
the question, any number of callers.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------
# Fixed-format geometry
# ---------------------------------------------------------------------
LINE_WIDTH = 80
BODY_START = 7
BODY_END = 72
COMMENT_INDICATORS = ("*", "/")

PERFORM_BUSINESS_TEMPLATE = "PERFORM {paragraph}"
EOC_CONDITION_TEMPLATE = "{cursor}-EOC"

# How many physical lines to look ahead when a PERFORM and its UNTIL
# clause are split across a continuation line.
UNTIL_LOOKAHEAD_LIMIT = 4

# Conditions that mean "the legacy end test is still in place", kept
# local (not imported) per this module's self-contained design.
_LEGACY_EOC_FORMS = (
    "SQLCODE=100",
    "SQLCODE = 100",
    "SQLCODE=+100",
    "SQLCODE = +100",
    "DB-END-OF-SET",
    "DB-REC-NOT-FOUND",
)

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

# A driving PERFORM in EITHER idiom, UNTIL optionally on the same line:
#   PERFORM <para>                                 (no drive)
#   PERFORM <para> UNTIL <condition>               (inline drive)
#   PERFORM <para> THRU <exit>                     (span, UNTIL follows)
#   PERFORM <para> THRU <exit> UNTIL <condition>   (span drive)
PERFORM_DRIVER_PATTERN = re.compile(
    rf"^PERFORM\s+(?P<paragraph>{_NAME})"
    rf"(?:\s+(?:THRU|THROUGH)\s+(?P<through>{_NAME}))?"
    rf"(?:\s+UNTIL\s+(?P<condition>.+?))?\s*\.?$",
    re.IGNORECASE,
)

# A standalone UNTIL line, for the split-continuation case.
UNTIL_LINE_PATTERN = re.compile(
    r"^UNTIL\s+(?P<condition>.+?)\s*\.?$", re.IGNORECASE
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
    "already_bound": (
        "Cursor close guarantee: {fetch} already performs {paragraph}; "
        "no change needed."
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
    "fetch_not_found": (
        "Cursor close guarantee: FETCH paragraph {fetch} was not found in "
        "the program; WHEN ZERO left unchanged."
    ),
    "already_driven_by_span": (
        "Cursor close guarantee: business paragraph {paragraph} is "
        "already driven by an external SPAN loop on cursor {cursor} "
        "(UNTIL {cursor}-EOC) and performs {fetch} at its own tail; "
        "binding refused to prevent FETCH <-> business recursion."
    ),
}


class FetchBusinessBinder:
    """Replaces CONTINUE under WHEN ZERO with PERFORM <business>."""

    def __init__(self, log=None) -> None:
        self.log = log
        self.messages: List[str] = []

    # ------------------------------------------------------------------
    # Public entry points
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

        # Refuse rather than create a mutual PERFORM. See CORRECTION 1.
        if self.already_externally_driven(
            lines, cursor, business, fetch_paragraph
        ):
            self._note(
                "already_driven_by_span",
                paragraph=business,
                cursor=cursor,
                fetch=fetch_paragraph,
            )
            return lines, business

        return (
            self._bind_when_zero(lines, fetch_paragraph, business),
            business,
        )

    def already_externally_driven(
        self,
        lines: List[str],
        cursor: str,
        business: str,
        fetch_paragraph: str = "",
    ) -> bool:
        """True when binding WHEN ZERO would create a mutual PERFORM.

        Both halves must hold:

          1. an EXTERNAL loop drives `business` to this cursor's
             end-of-cursor condition, and
          2. `business` performs `fetch_paragraph` at its own tail.

        Half 1 alone is not enough: if nothing re-fetches, refusing the
        bind leaves a loop that never advances. When fetch_paragraph is
        omitted, half 2 is not testable and half 1 decides.

        Recognised driver forms:
            PERFORM <business> THRU <exit> UNTIL <cursor>-EOC.
            PERFORM <business> UNTIL <cursor>-EOC.
            PERFORM <business> THRU <exit>
                UNTIL <cursor>-EOC.                 (split across lines)
        """
        target = str(business or "").strip().upper()
        if not target:
            return False

        eoc_token = self._squash(
            EOC_CONDITION_TEMPLATE.format(cursor=str(cursor or "").upper())
        )
        if not eoc_token:
            return False

        generated = [
            (start, end)
            for name, start, end in self.paragraph_spans(lines)
            if self.is_generated(name)
        ]

        for index, line in enumerate(lines):
            if not self._is_code(line):
                continue
            if any(start <= index <= end for start, end in generated):
                continue

            body = self._body(line).upper()
            match = PERFORM_DRIVER_PATTERN.match(body)
            if not match:
                continue
            if match.group("paragraph").upper() != target:
                continue

            condition = match.group("condition") or ""
            if not condition:
                condition = self._until_lookahead(lines, index + 1)

            probe = self._squash(condition)
            if not probe:
                continue

            driven = eoc_token in probe or any(
                self._squash(legacy) in probe
                for legacy in _LEGACY_EOC_FORMS
            )
            if not driven:
                continue

            if not fetch_paragraph:
                return True
            return self._business_fetches(lines, business, fetch_paragraph)

        return False

    # ------------------------------------------------------------------
    # External-driver helpers
    # ------------------------------------------------------------------

    def _business_fetches(
        self, lines: List[str], business: str, fetch_paragraph: str
    ) -> bool:
        """True when <business> performs <fetch> inside its own span."""
        span = self.span_of(lines, business)
        if span is None:
            return False

        start, end = span
        target = f"PERFORM {str(fetch_paragraph or '').upper()}"

        for index in range(start, end + 1):
            if not self._is_code(lines[index]):
                continue
            if self._body(lines[index]).upper().startswith(target):
                return True

        return False

    def _until_lookahead(self, lines: List[str], start_index: int) -> str:
        """The condition of an UNTIL clause on a continuation line.

        Stops at the first code line. An UNTIL that is not the very next
        statement does not belong to this PERFORM.
        """
        start = max(int(start_index), 0)
        end = min(len(lines), start + UNTIL_LOOKAHEAD_LIMIT)

        for index in range(start, end):
            if not self._is_code(lines[index]):
                continue
            match = UNTIL_LINE_PATTERN.match(self._body(lines[index]).upper())
            return match.group("condition") if match else ""

        return ""

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
            self._note("fetch_not_found", fetch=fetch_paragraph)
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
                self._note(
                    "already_bound",
                    fetch=fetch_paragraph,
                    paragraph=business,
                )
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

    @staticmethod
    def _squash(text: str) -> str:
        """Upper case with every space removed - for condition matching."""
        return "".join(str(text or "").split()).upper().rstrip(".")

    def _note(self, key: str, **values) -> None:
        template = MESSAGES.get(key, "")
        if not template:
            return

        try:
            message = template.format(**values)
        except KeyError:
            # A missing placeholder must not abort a conversion pass.
            message = template

        self.messages.append(message)

        if self.log is None:
            return
        try:
            self.log.messages.append(message)
        except AttributeError:
            pass


# ---------------------------------------------------------------------
# Module-level guard, for a caller that owns its own line utilities
# ---------------------------------------------------------------------
def already_externally_driven(
    lines: List[str],
    cursor: str,
    business: str,
    fetch_paragraph: str = "",
) -> bool:
    """Stateless form of FetchBusinessBinder.already_externally_driven.

    A binding site in a sibling package needs the ANSWER, not this class.
    One import, one call, no construction, no shared state - and only ONE
    implementation of the question in the repository.
    """
    return FetchBusinessBinder().already_externally_driven(
        lines, cursor, business, fetch_paragraph
    )


__all__ = ["FetchBusinessBinder", "already_externally_driven"]
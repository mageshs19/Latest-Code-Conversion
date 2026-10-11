"""Where things are in a converted COBOL program.

Pure location logic: paragraph spans, insertion points, and the two
ways of reading a line. No COBOL is written here and no pass order is
decided here.

Extracted from RestartInjectionComposer so the composer reads as the
sequence of passes it is, and so a boundary rule can be tested without
constructing a restart family.

CORRECTION A - END-EXEC. was read as a paragraph header
---------------------------------------------------------
``END-EXEC.`` wears the header SHAPE - one word, one period - and was
not in NON_PARAGRAPH_DOTTED_LINES, which only knew CONTINUE / EXIT /
END-IF. The consequence is not cosmetic: every pass in the composer is
SPAN based, so a false boundary truncates the enclosing paragraph.

NON_PARAGRAPH_WORDS is therefore a SUPERSET of the shared vocabulary
plus every COBOL scope terminator. It is exported so tests assert
against production vocabulary instead of a private copy.

FOLLOW-UP: converter/composers/restart/legacy_restart_cleanup.py removes
paragraphs by span too and carries the same blind spot.

CORRECTION B - one reader could not serve both callers
--------------------------------------------------------
``_logical()`` returns "" for a comment, which is required: a commented
line must never be mistaken for a paragraph header. But evidence
gathering needs the opposite. The checkpoint record that proves a
program is a restart program is routinely commented out by the
unmapped-record pass before restart injection runs, and a reader that
drops comments discards the last surviving proof.

``_logical_any()`` keeps comments. Boundary detection uses the first;
evidence gathering uses the second. Neither caller may use the other's
reader.

CORRECTION C - the mainline was located by OPEN INPUT
-------------------------------------------------------
OPEN INPUT is where the generated flow BEGINS; it is not what makes a
paragraph the mainline. A program that opens its file in an
initialisation paragraph had the restart flow - which ends in STOP RUN
- spliced into the INITIALISER, while the real mainline kept its own.
The program then carried TWO STOP RUNs and the restart control ran
inside initialisation.

``_termination_index()`` answers the real question: which line ends the
program. ``_open_input_index_within()`` remains, now serving only the
narrower question of where inside a known span the flow should start.

CORRECTION D - "outside the replaced region" was not specific enough
----------------------------------------------------------------------
A priming read and a loop-tail read are the SAME statement text serving
different purposes. ``_statement_index_outside()`` first took a single
(start, end) pair, so it found the tail that ProcessParagraphInjector
appends to the business paragraph, the caller suppressed the priming
read, and the pass stopped being idempotent: run 1 wrote it, run 2
deleted it, and the loop would process a record it had never read.

It now takes a SEQUENCE of excluded ranges. The caller excludes both
the region being replaced and the process paragraph, so what remains is
an initialisation the program genuinely performs.

ANY CHANGE TO A SIGNATURE HERE IS A CHANGE TO A CONTRACT. The composer
inherits these methods; a shape change in this file that is not matched
in the caller fails at RUNTIME, not at import, and every unit test of
this class on its own still passes.
tests/restart/test_geometry_signatures.py exists to make that loud.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from patterns.restart_patterns import (
    OPEN_INPUT_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    STOP_RUN_PATTERN,
)
from rules.restart_cleanup_rules import NON_PARAGRAPH_DOTTED_LINES

END_PROGRAM = "END PROGRAM"
MAINLINE_LABEL = "PROCEDURE DIVISION"

# Statement prefixes worth reporting when a span is handed to a repair
# pass. Scope openers and closers only - enough to audit the arithmetic
# the composer performs, without dumping the paragraph.
SCOPE_REPORT_PREFIXES = ("IF ", "EVALUATE ", "END-IF", "END-EVALUATE")

# The verb that opens a performed-paragraph reference. A LANGUAGE token,
# never site vocabulary.
PERFORM_VERB = "PERFORM "

# COBOL scope terminators and no-ops. Every one of them is one word
# followed by a period, which is also the paragraph-header shape. These
# are LANGUAGE tokens, never site vocabulary.
SCOPE_TERMINATOR_WORDS = (
    "CONTINUE",
    "END-ADD",
    "END-CALL",
    "END-COMPUTE",
    "END-DELETE",
    "END-DIVIDE",
    "END-EVALUATE",
    "END-EXEC",
    "END-IF",
    "END-MULTIPLY",
    "END-PERFORM",
    "END-READ",
    "END-RETURN",
    "END-REWRITE",
    "END-SEARCH",
    "END-START",
    "END-STRING",
    "END-SUBTRACT",
    "END-UNSTRING",
    "END-WRITE",
    "EXIT",
    "GOBACK",
)

NON_PARAGRAPH_WORDS = tuple(
    sorted(
        {
            *(
                str(word).strip().upper().rstrip(".")
                for word in NON_PARAGRAPH_DOTTED_LINES
            ),
            *SCOPE_TERMINATOR_WORDS,
        }
        - {""}
    )
)


@dataclass(frozen=True)
class Span:
    """One paragraph: header line, first body line, first line after."""

    name: str
    header: int
    start: int
    end: int


class RestartParagraphGeometry:
    """Locates paragraphs and boundaries. Expects ``self.line_utils``."""

    # -----------------------------------------------------------------
    # Line handling - the SHARED retrieval utility, never a local parser
    # -----------------------------------------------------------------
    def _logical(self, line: str) -> str:
        """Columns 8-72, upper-cased. Comments return "".

        Used for every BOUNDARY decision. A comment that looked like a
        header would split a paragraph in half.
        """
        text = str(self.line_utils.logical(line) or "").strip()
        if not text or self.line_utils.is_comment(text):
            return ""
        return " ".join(text.upper().split())

    def _logical_any(self, line: str) -> str:
        """Like _logical, but KEEPS comment lines.

        Used only for EVIDENCE. See CORRECTION B in the module
        docstring: a commented checkpoint record is still evidence.
        """
        text = str(self.line_utils.logical(line) or "").strip()
        if not text:
            return ""
        return " ".join(text.upper().split())

    def _lines(self, text: str) -> list[str]:
        if self._has_text_helpers():
            return list(self.line_utils.lines(text))
        return str(text or "").splitlines()

    def _join(self, lines: list[str]) -> str:
        if self._has_text_helpers():
            return str(self.line_utils.join(list(lines)))
        return "\n".join(str(line) for line in lines)

    def _has_text_helpers(self) -> bool:
        """Split and join must come from the SAME source or the round
        trip loses idempotence."""
        return callable(getattr(self.line_utils, "lines", None)) and callable(
            getattr(self.line_utils, "join", None)
        )

    # -----------------------------------------------------------------
    # Paragraph geometry
    # -----------------------------------------------------------------
    def _spans(self, lines: list[str]) -> list[Span]:
        headers = self._headers(lines)
        limit = self._insert_index(lines)
        spans: list[Span] = []
        for position, (index, name) in enumerate(headers):
            following = (
                headers[position + 1][0]
                if position + 1 < len(headers)
                else limit
            )
            spans.append(
                Span(
                    name=name,
                    header=index,
                    start=index + 1,
                    end=max(min(following, limit), index + 1),
                )
            )
        return spans

    def _headers(self, lines: list[str]) -> list[tuple[int, str]]:
        found: list[tuple[int, str]] = []
        started = False
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if not logical:
                continue
            if PROCEDURE_DIVISION_PATTERN.match(logical):
                started = True
                continue
            if not started:
                continue
            match = PARAGRAPH_HEADER_PATTERN.match(logical)
            if not match:
                continue
            name = match.group("name").upper()
            if self._is_not_a_paragraph(name):
                continue
            found.append((index, name))
        return found

    @staticmethod
    def _is_not_a_paragraph(name: str) -> bool:
        """END-EXEC. / END-IF. / EXIT. wear the header SHAPE but head
        nothing."""
        return (
            str(name or "").strip().upper().rstrip(".") in NON_PARAGRAPH_WORDS
        )

    def _span_named(self, lines: list[str], name: str) -> Span | None:
        target = str(name or "").strip().upper()
        if not target:
            return None
        for span in self._spans(lines):
            if span.name.upper() == target:
                return span
        return None

    def _procedure_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if logical and PROCEDURE_DIVISION_PATTERN.match(logical):
                return index
        return -1

    def _open_input_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if logical and OPEN_INPUT_PATTERN.match(logical):
                return index
        return -1

    def _open_input_index_within(
        self,
        lines: list[str],
        start: int,
        end: int,
    ) -> int:
        """The OPEN INPUT line inside [start, end), or -1.

        Scoped, unlike _open_input_index, because a program may OPEN in
        one paragraph and terminate in another; a caller repairing ONE
        paragraph must not be handed an anchor from a different one.
        """
        for index in range(max(0, start), min(end, len(lines))):
            logical = self._logical(lines[index])
            if logical and OPEN_INPUT_PATTERN.match(logical):
                return index
        return -1

    # -----------------------------------------------------------------
    # Termination and statement location  -- CORRECTION C and D
    # -----------------------------------------------------------------
    def _termination_index(self, lines: list[str]) -> int:
        """The line that terminates the program, or -1. CORRECTION C."""
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if logical and STOP_RUN_PATTERN.match(logical):
                return index
        return -1

    def _perform_index_within(
        self,
        lines: list[str],
        start: int,
        end: int,
        paragraph: str,
    ) -> int:
        """The first PERFORM of `paragraph` inside [start, end), or -1."""
        target = str(paragraph or "").strip().upper()
        if not target:
            return -1
        for index in range(max(0, start), min(end, len(lines))):
            body = self._logical(lines[index])
            if body.startswith(PERFORM_VERB) and target in body:
                return index
        return -1

    def _statement_index_outside(
        self,
        lines: list[str],
        excluded: Sequence[tuple[int, int]],
        statement: str,
    ) -> int:
        """First occurrence of `statement` outside every excluded range.

        CORRECTION D. `excluded` is a SEQUENCE of (start, end) pairs,
        not a single pair: the caller excludes both the region being
        replaced and the process paragraph, because the loop tail and
        the priming read are the same statement text.
        """
        target = " ".join(str(statement or "").strip().upper().split())
        if not target:
            return -1
        for index, line in enumerate(lines):
            if any(start <= index < end for start, end in excluded):
                continue
            if self._logical(line) == target:
                return index
        return -1

    def _insert_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if self._logical(line).startswith(END_PROGRAM):
                return index
        return len(lines)


__all__ = [
    "END_PROGRAM",
    "MAINLINE_LABEL",
    "NON_PARAGRAPH_WORDS",
    "PERFORM_VERB",
    "SCOPE_REPORT_PREFIXES",
    "SCOPE_TERMINATOR_WORDS",
    "RestartParagraphGeometry",
    "Span",
]
# LOCATION: converter/composers/procedure_indent/indent_models.py
# ACTION: CREATE NEW FILE
"""Frames, the frame stack and line classification. The passive parts.

Nothing here decides an indent. _Frame knows how far its own body sits
from its header; FrameStack opens and closes blocks; LineClassifier
answers yes/no questions about one line.

CORRECTION - a word-boundary continuation was classified as a statement.

_is_untouchable tested only the '-' indicator. A fixed-format statement
may continue onto the next line with NO indicator at all, provided the
break falls between two complete words, so

    DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF
                             OF DCLDZBEFFTV

had its second line re-indented to Area B. is_continuation() recognises
a continuation by what the line STARTS with, or by what the line above
ENDS with - never by its indicator.
"""

from __future__ import annotations

from dataclasses import dataclass

from patterns.procedure_indent_patterns import (
    PARAGRAPH_HEADER_PATTERN,
    SECTION_HEADER_PATTERN,
)
from rules.procedure_indent_rules import (
    BLOCK_KIND_EVALUATE,
    BLOCK_KIND_SQL,
    CONTINUATION_OPENERS,
    CONTINUATION_TRAILERS,
    NEST_STEP,
    NON_PARAGRAPH_SINGLE_WORDS,
    RESPECT_STATEMENT_CONTINUATIONS,
    SQL_BODY_OFFSET,
    STATEMENT_VERBS,
    WHEN_BODY_OFFSET,
    WHEN_OFFSET,
)

SELF_CLOSING_SUFFIXES = ("END-IF", "END-PERFORM")
SCOPED_CLOSING_SUFFIXES = (
    "END-READ", "END-SEARCH", "END-STRING", "END-UNSTRING",
)


@dataclass
class Frame:
    """One open block on the indentation stack."""

    kind: str
    own_indent: int

    @property
    def body_indent(self) -> int:
        if self.kind == BLOCK_KIND_EVALUATE:
            return self.own_indent + WHEN_BODY_OFFSET
        if self.kind == BLOCK_KIND_SQL:
            return self.own_indent + SQL_BODY_OFFSET
        return self.own_indent + NEST_STEP

    @property
    def when_indent(self) -> int:
        return self.own_indent + WHEN_OFFSET


class FrameStack:
    """Open blocks, innermost last. Tolerates a mismatched terminator."""

    def __init__(self) -> None:
        self._frames: list[Frame] = []

    def __len__(self) -> int:
        return len(self._frames)

    def clear(self) -> None:
        self._frames.clear()

    def push(self, kind: str, own_indent: int) -> None:
        self._frames.append(Frame(kind, own_indent))

    @property
    def top(self) -> Frame | None:
        return self._frames[-1] if self._frames else None

    def pop(self, kind: str) -> Frame | None:
        """Close the nearest frame of `kind`.

        A malformed program can terminate a block that was never
        opened. Falling back to the innermost frame keeps the stack
        usable rather than losing sync for the rest of the paragraph.
        """
        for index in range(len(self._frames) - 1, -1, -1):
            if self._frames[index].kind == kind:
                frame = self._frames[index]
                del self._frames[index:]
                return frame

        return self._frames.pop() if self._frames else None

    def peek(self, kind: str) -> Frame | None:
        for index in range(len(self._frames) - 1, -1, -1):
            if self._frames[index].kind == kind:
                return self._frames[index]
        return None


class LineClassifier:
    """Yes/no questions about one line. Owns no indent arithmetic."""

    def __init__(self, fixed_format) -> None:
        self.fixed_format = fixed_format

    def is_untouchable(self, line: str) -> bool:
        """Comment, page-eject, debug, '-' continuation or blank."""
        if not str(line or "").strip():
            return True
        if self.fixed_format.is_comment_or_control_line(line):
            return True
        if self.fixed_format.is_continuation_line(line):
            return True
        return self.fixed_format.is_sequence_artifact(line)

    @staticmethod
    def is_continuation(upper: str, previous_upper: str) -> bool:
        """True when this line continues the statement above it.

        Two independent signals, either sufficient:

          OPENER   starts with a connector - OF, TO, a comma, a quote -
                   which cannot begin a statement;
          TRAILER  the line above ends on a connector, so this line is
                   its operand.

        A COBOL verb is tested first, so 'MOVE A TO B' followed by
        'MOVE C TO D' is never mistaken for a continuation.
        """
        if not RESPECT_STATEMENT_CONTINUATIONS or not previous_upper:
            return False

        text = upper.strip()
        if not text:
            return False

        if text.rstrip(".") in NON_PARAGRAPH_SINGLE_WORDS:
            return False

        if text.split()[0].rstrip(".") in STATEMENT_VERBS:
            return False

        if text.startswith(CONTINUATION_OPENERS):
            return True

        previous = previous_upper.rstrip().rstrip(".")
        if not previous:
            return False

        return previous.split()[-1] in CONTINUATION_TRAILERS

    @staticmethod
    def is_area_a_header(upper: str) -> bool:
        if SECTION_HEADER_PATTERN.match(upper):
            return True

        match = PARAGRAPH_HEADER_PATTERN.match(upper)
        if not match:
            return False

        return match.group("name").upper() not in NON_PARAGRAPH_SINGLE_WORDS

    @staticmethod
    def is_self_closing(upper: str) -> bool:
        """A one-line block carrying its own terminator.

        Example: IF X = 1 MOVE A TO B END-IF
        """
        return upper.rstrip(".").endswith(SELF_CLOSING_SUFFIXES)

    @staticmethod
    def opens_scope(upper: str) -> bool:
        """A READ / SEARCH / STRING that is not already terminated."""
        if upper.rstrip(".").endswith(SCOPED_CLOSING_SUFFIXES):
            return False
        return not upper.endswith(".")


__all__ = ["Frame", "FrameStack", "LineClassifier"]
# LOCATION: converter/composers/restart/restart_line_utils.py
# ACTION: REPLACE ENTIRE FILE
"""The line utility the restart package passes to its collaborators.

WHY THIS EXISTS

Every restart module calls exactly two methods:

    logical(raw_line) -> str      the body, columns 8-72, stripped
    is_comment(text)  -> bool     is this logical text a comment?

No production class exposes both. FixedFormatLineService,
CursorFlowLineFormatter and CobolCleanupLineUtils all supply logical()
and each spells the comment test differently. Only the test stand-in had
is_comment, so wiring any of them directly would have failed on the
first comment line of a real program.

converter/composers/cursor_close_guarantee/line_utils.py solved the same
problem the same way: wrap the shared formatter, add what the package
needs, define a logical line in ONE place.

THE COMMENT DECISION IS SPLIT IN TWO

FixedFormatLineService.logical() returns columns 8-72. For a line whose
INDICATOR column carries '*', that body comes back WITHOUT the asterisk,
so testing the logical text alone can never recognise it. The indicator
is read from the RAW line and a comment collapses to "", which every
restart module already skips. is_comment() then answers honestly for
free-form text carrying its own marker.

CORRECTION - a stray sequence area was returned as a statement

A line carrying only its sequence number came back as a body, and

    001690.

matches the paragraph-header shape exactly: digits are legal in a COBOL
name. The restart composer would have invented a paragraph and cut every
span at it. converter/composers/statement_layout rules already record
this shape - six digits, an optional indicator, an optional period - as
"not COBOL". The width is SIX because that is the sequence area; a
shorter or longer run of digits may be a genuine numeric paragraph name
and is left alone.

Owns no regex, no business rule, no program / paragraph / record /
table / DCLGEN / cursor / host variable name.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)

COMMENT_MARKERS = ("*", "/")
INDICATOR_MARKERS = ("*", "/", "-", "D", "d")
SEQUENCE_WIDTH = 6
REQUIRED_METHODS = ("logical", "is_comment_or_control_line")


class RestartLineUtils:
    """Adapts the shared fixed-format service to the restart contract."""

    def __init__(self, fixed_format=None) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self._verify(self.fixed_format)

    #
    # The two methods every restart module calls
    #
    def logical(self, line: str) -> str:
        """Body of a code line; "" for a comment, control or stray line."""
        body = self._body(line)
        return "" if self._is_sequence_only(body) else body

    @staticmethod
    def is_comment(text: str) -> bool:
        """True when ALREADY-LOGICAL text carries its own marker."""
        return str(text or "").lstrip().startswith(COMMENT_MARKERS)

    #
    # Split and join must come from one place or the round trip drifts
    #
    @staticmethod
    def lines(text: str) -> list[str]:
        return str(text or "").splitlines()

    @staticmethod
    def join(lines) -> str:
        return "\n".join(str(line) for line in lines or [])

    #
    # Reading
    #
    def _body(self, line: str) -> str:
        try:
            if self.fixed_format.is_comment_or_control_line(line):
                return ""
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:  # noqa: BLE001 - one odd line must not abort a pass
            text = str(line or "").strip()
            return "" if text.startswith(COMMENT_MARKERS) else text

    @staticmethod
    def _is_sequence_only(body: str) -> bool:
        """A body that is only a sequence area is not COBOL.

        Exactly SIX digits, with an optional indicator character and an
        optional period. A numeric paragraph name of any other width is
        left alone.
        """
        candidate = str(body or "").strip()
        if candidate.endswith("."):
            candidate = candidate[:-1]
        if candidate[-1:] in INDICATOR_MARKERS:
            candidate = candidate[:-1]
        candidate = candidate.strip()
        return len(candidate) == SEQUENCE_WIDTH and candidate.isdigit()

    #
    # Construction-time contract check
    #
    @staticmethod
    def _verify(fixed_format) -> None:
        missing = [
            name
            for name in REQUIRED_METHODS
            if not callable(getattr(fixed_format, name, None))
        ]
        if missing:
            raise TypeError(
                "RestartLineUtils needs a fixed-format service exposing "
                f"{missing}; got {type(fixed_format).__name__}."
            )


__all__ = [
    "COMMENT_MARKERS",
    "INDICATOR_MARKERS",
    "REQUIRED_METHODS",
    "SEQUENCE_WIDTH",
    "RestartLineUtils",
]
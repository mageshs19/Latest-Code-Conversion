# LOCATION: converter/generators/cursor_paragraph/cursor_line_geometry.py
# ACTION: CREATE NEW FILE
"""Fixed-format width arithmetic for one generated body line.

Owns no COBOL text. Answers exactly two questions:

    does this body line fit the window?
    what is the widest continuation indent that fits?

Split out because every diagnostic builder needs both and neither is a
decision about COBOL content.
"""

from __future__ import annotations

from rules.cursor_paragraph_rules import (
    FETCH_KEY_BODY_END_COLUMN,
    IND_WHEN_BODY,
    IND_WHEN_BODY_CONT,
)

# A rendered body carries the indicator, so a body of length n ends at
# physical column 7 + n.
BODY_COLUMN_OFFSET = 7


def fits(line: str) -> bool:
    """True when the body line ends on or before the window edge."""
    return BODY_COLUMN_OFFSET + len(str(line or "")) <= FETCH_KEY_BODY_END_COLUMN


def continuation(text: str) -> str:
    """A continuation fragment at the widest indent that still fits.

    Prefers IND_WHEN_BODY_CONT, which aligns under the DISPLAY operands
    the way the manual reference lays them out, and falls back to
    IND_WHEN_BODY when the fragment is too wide for it.

    Returns "" when neither works, which makes the caller skip the whole
    diagnostic rather than emit an over-long line. A truncated data-name
    does not compile; a missing diagnostic is harmless.
    """
    body = str(text or "").strip()
    if not body:
        return ""

    for indent in (IND_WHEN_BODY_CONT, IND_WHEN_BODY):
        candidate = f"{indent}{body}"
        if fits(candidate):
            return candidate

    return ""


__all__ = ["BODY_COLUMN_OFFSET", "fits", "continuation"]
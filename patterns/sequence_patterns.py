# LOCATION: patterns/sequence_patterns.py
# ACTION: REPLACE ENTIRE FILE

"""COBOL fixed-format sequence handling.

CORRECTION 1 - the indicator column was required to be blank
------------------------------------------------------------
The original left-sequence pattern demanded whitespace after the six
digits:

    r"^\\s*(?P<seq>\\d{6})(?P<body>\\s+.*)$"

Column 7 is the INDICATOR AREA. It legitimately holds '*', '/', '-' or
'D'. On any such line the sequence number was never stripped, so a body
read as "001690/" was classified as executable COBOL and the terminator
pass punctuated it into "001690/." - not valid COBOL. The same defect
hid trailing IF ... WRITE ... END-IF blocks from the output-write pass.

Stripping is now COLUMN-BASED, with a regex fallback only for free-form
text that carries no fixed-format frame.

CORRECTION 2 - a duplicated sequence area survived
---------------------------------------------------
A line that had already been sequenced, then sequenced a SECOND time by
a later pass, reaches this module as:

    000380 000380* 2004/12 REPRENDRE N  DE TITRE EN OUTPUT (12 POS  00380000
    ^^^^^^ ^                                                       ^^^^^^^^
    cols1-6 col7                                             cols 73-80

Columns 1-6 are digits and column 7 is a blank indicator, so the line
passed is_fixed_format_line() and columns 8-72 were returned verbatim -
inner sequence and all. strip_sequence_numbers() now removes a nested
sequence area as well, capped and guarded so a legitimate body that
happens to begin with digits is never damaged.

CORRECTION 3 - the right sequence was removed without being verified
---------------------------------------------------------------------
strip_right_sequence() truncated every fixed-format line at column 72.
A generated line whose body overran column 72 therefore lost real text
with no diagnostic. Columns 73-80 are now removed only when they are
actually an eight-digit sequence.

CORRECTION 4 - CRLF
--------------------
rstrip("\\n") left a trailing '\\r' at position 80, displacing the right
sequence slice by one. Both line endings are removed.

CORRECTION 5 - a six-digit PARAGRAPH NUMBER was read as a sequence area
------------------------------------------------------------------------
The abend paragraph is named 810000-CALL-USERABEN. Presented to
is_fixed_format_line() it satisfied BOTH tests:

    text[0:6].isdigit()            -> "810000"  -> True
    text[6] in VALID_INDICATORS    -> "-"       -> True   (continuation)

The header was therefore classified as a fully framed record. From that
point logical_body() returned "CALL-USERABEN.", replace_body() rebuilt
the line as left="810000" + indicator="-" + body, and the final
resequencer overwrote columns 1-6 with its running number, producing:

    005680-CALL-USERABEN.                                      05680000

A paragraph name beginning with a hyphen does not compile. It is the
ONLY paragraph in the scheme whose number is six digits wide, which is
why nothing else broke: 700-, 720- and 1100- all fail isdigit().

THE DISCRIMINATOR

A continuation indicator is followed by Area A/B whitespace or a quote.
A paragraph-name hyphen is followed IMMEDIATELY by an alphanumeric
character, and the line carries no right sequence because it has not
been framed yet. Requiring the right sequence only in that narrow case
keeps genuine continuation lines - including truncated hand-maintained
ones - working exactly as before.

tests/restart/conftest.py already encodes this rule for its own line
utility; this module is the production owner that had not caught up.

CONTRACT (unchanged for callers)
--------------------------------
strip_sequence_numbers(line) removes columns 1-6 and 73-80, KEEPING
column 7 onwards. A comment line therefore still begins with its '*' or
'/' indicator, which is what is_comment_or_blank() relies on.

logical_body(line) returns columns 8-72 only, indicator excluded.

This file contains regex patterns and pure text helpers only.
No business rules, no layout constants, no program names.
"""

from __future__ import annotations

import re

# =====================================================================
# Fixed-format geometry
# =====================================================================
LEFT_SEQUENCE_START = 0
LEFT_SEQUENCE_END = 6
INDICATOR_INDEX = 6
BODY_START = 7
BODY_END = 72
RIGHT_SEQUENCE_START = 72
RIGHT_SEQUENCE_END = 80

LINE_WIDTH = RIGHT_SEQUENCE_END
BODY_WIDTH = BODY_END - BODY_START
INDICATED_BODY_WIDTH = BODY_END - INDICATOR_INDEX

MIN_ADDRESSABLE_LENGTH = BODY_START
LEFT_SEQUENCE_WIDTH = LEFT_SEQUENCE_END - LEFT_SEQUENCE_START
RIGHT_SEQUENCE_WIDTH = RIGHT_SEQUENCE_END - RIGHT_SEQUENCE_START

LINE_ENDINGS = "\r\n"

# Every indicator the COBOL standard permits in column 7.
VALID_INDICATORS = (" ", "*", "/", "D", "d", "-")
COMMENT_INDICATORS = ("*", "/")
DEBUG_INDICATORS = ("D", "d")
CONTINUATION_INDICATOR = "-"
BLANK_INDICATOR = " "

# A duplicated sequence area is a pass bug, never source. One extra pass
# is all that is ever observed; a cap stops a malformed body from being
# eaten digit group by digit group.
STRIP_NESTED_SEQUENCE = True
MAX_NESTED_SEQUENCE_PASSES = 2

# CORRECTION 5. When column 7 is a hyphen AND column 8 is alphanumeric,
# the six digits are the head of a paragraph NAME unless the line also
# carries its right sequence. Switchable so the old, permissive
# behaviour can be restored for a single run if a site needs it.
CONTINUATION_REQUIRES_RIGHT_SEQUENCE = True

# =====================================================================
# Patterns
# =====================================================================
_INDICATOR_CLASS = r"[ */\-Dd]"

# CORRECTION 5. Nested-sequence detection must NOT accept the hyphen:
# "810000-CALL-USERABEN." is a name, not a leaked sequence area followed
# by a continuation indicator.
_NESTED_INDICATOR_CLASS = r"[ */Dd]"

# Left sequence followed by the indicator area. The body group accepts
# ANY valid indicator, not whitespace only. Kept for direct importers;
# strip_left_sequence() applies the CORRECTION 5 guard on top of it.
LEFT_SEQUENCE_PATTERN = re.compile(
    rf"^\s*(?P<seq>\d{{{LEFT_SEQUENCE_WIDTH}}})(?P<body>{_INDICATOR_CLASS}.*)?$",
)

# Trailing eight-digit right sequence on a free-form line.
RIGHT_SEQUENCE_PATTERN = re.compile(
    rf"^(?P<body>.*?)\s+(?P<right>\d{{{RIGHT_SEQUENCE_WIDTH}}})\s*$",
)

# A sequence area that has leaked INTO a body: six digits immediately
# followed by a valid indicator character. The hyphen is excluded - see
# CORRECTION 5.
NESTED_SEQUENCE_PATTERN = re.compile(
    rf"^(?P<seq>\d{{{LEFT_SEQUENCE_WIDTH}}})"
    rf"(?P<rest>{_NESTED_INDICATOR_CLASS}.*)?$",
)

# A body that is nothing but a leaked sequence number. The digit run is
# 6-8 wide: a short record keeps part of its right sequence, which is how
# "<paragraph>.  0074700" reached the paragraph scanner.
SEQUENCE_ARTIFACT_PATTERN = re.compile(
    rf"^\s*\d{{{LEFT_SEQUENCE_WIDTH},{RIGHT_SEQUENCE_WIDTH}}}"
    rf"\s*{_NESTED_INDICATOR_CLASS}?\s*\.?\s*$",
)

_ALL_DIGITS_PATTERN = re.compile(r"^\d+$")


# =====================================================================
# Classification
# =====================================================================
def _clean(line: str) -> str:
    """The physical line with its line ending removed, nothing else.

    Trailing blanks are NOT stripped: they are what position the right
    sequence at column 73.
    """
    return str(line or "").rstrip(LINE_ENDINGS)


def is_paragraph_number_prefix(line: str) -> bool:
    """True when a six-digit run is the HEAD OF A NAME, not a sequence area.

    CORRECTION 5. Recognises exactly one shape:

        six digits, a hyphen in column 7, an alphanumeric in column 8,
        and NO right sequence

    which is an unframed generated paragraph header such as
    "810000-CALL-USERABEN.". A genuine continuation line inside a
    sequenced member carries its right sequence and is unaffected; a
    continuation whose column 8 is a space or a quote is unaffected
    whether or not it is framed.
    """
    text = _clean(line)

    if len(text) <= BODY_START:
        return False

    if not text[LEFT_SEQUENCE_START:LEFT_SEQUENCE_END].isdigit():
        return False

    if text[INDICATOR_INDEX] != CONTINUATION_INDICATOR:
        return False

    if not text[BODY_START:BODY_START + 1].isalnum():
        return False

    return not has_right_sequence(text)


def is_fixed_format_line(line: str) -> bool:
    """True when columns 1-6 are numeric and column 7 is a valid indicator.

    The right sequence is deliberately optional: hand-maintained members
    often leave it blank or truncate the line, and demanding it was what
    caused sequence numbers to be parsed as COBOL text.

    CORRECTION 5 - a six-digit paragraph number is refused here. See the
    module docstring and is_paragraph_number_prefix().
    """
    text = _clean(line)

    if len(text) < MIN_ADDRESSABLE_LENGTH:
        return False

    if not text[LEFT_SEQUENCE_START:LEFT_SEQUENCE_END].isdigit():
        return False

    if text[INDICATOR_INDEX] not in VALID_INDICATORS:
        return False

    if CONTINUATION_REQUIRES_RIGHT_SEQUENCE and is_paragraph_number_prefix(text):
        return False

    return True


def has_right_sequence(line: str) -> bool:
    """True when columns 73-80 hold an eight-digit sequence."""
    text = _clean(line)

    if len(text) < RIGHT_SEQUENCE_END:
        return False

    return bool(
        _ALL_DIGITS_PATTERN.match(
            text[RIGHT_SEQUENCE_START:RIGHT_SEQUENCE_END]
        )
    )


def indicator_of(line: str) -> str:
    """Column 7 of a fixed-format line.

    Falls back to the first non-blank character of a free-form line when
    that character is a comment indicator, so a caller can classify an
    unsequenced member without a separate code path.
    """
    text = _clean(line)

    if is_fixed_format_line(text):
        return text[INDICATOR_INDEX]

    stripped = text.lstrip()
    if stripped and stripped[0] in COMMENT_INDICATORS:
        return stripped[0]

    return ""


def is_comment_or_control(line: str) -> bool:
    """True for comment, page-eject and debug lines.

    Works on a RAW line, before any stripping, so a caller can classify
    correctly without relying on the stripped text starting with '*'.
    A continuation line ('-') is NOT a comment and returns False.
    """
    text = _clean(line)

    if not text.strip():
        return False

    return indicator_of(text) in COMMENT_INDICATORS + DEBUG_INDICATORS


def is_blank(line: str) -> bool:
    """True when the line carries no body at all."""
    return not logical_body(line)


def has_nested_sequence_area(body: str) -> bool:
    """True when a BODY still begins with a leaked sequence area.

    Accepts an optional leading indicator character, because
    strip_sequence_numbers() returns column 7 onwards. The hyphen is not
    accepted as the separator - CORRECTION 5.
    """
    text = str(body or "")

    if text[:1] in VALID_INDICATORS:
        text = text[1:]

    return bool(NESTED_SEQUENCE_PATTERN.match(text.lstrip()))


def is_sequence_artifact(line: str) -> bool:
    """True when the line carries nothing but a leaked sequence number."""
    text = _clean(line)

    if not text.strip():
        return False

    body = logical_body(text)
    if body and SEQUENCE_ARTIFACT_PATTERN.match(body):
        return True

    # A fully fixed-format artifact strips down to its bare indicator, so
    # the body test above cannot see it. Measure the raw record instead.
    if is_fixed_format_line(text):
        remainder = text[BODY_START:RIGHT_SEQUENCE_START].strip()
        if not remainder and not has_right_sequence(text):
            return True

    stripped = text.strip()
    return bool(SEQUENCE_ARTIFACT_PATTERN.match(stripped))


# =====================================================================
# Stripping
# =====================================================================
def strip_left_sequence(line: str) -> str:
    """Remove columns 1-6, keeping the indicator and the body.

    CORRECTION 5 - the regex fallback is guarded as well. Without it the
    column-based path refused the paragraph header and the fallback
    stripped it anyway, which is the same defect one line lower.
    """
    text = _clean(line)

    if CONTINUATION_REQUIRES_RIGHT_SEQUENCE and is_paragraph_number_prefix(text):
        return text

    if is_fixed_format_line(text):
        return text[LEFT_SEQUENCE_END:]

    match = LEFT_SEQUENCE_PATTERN.match(text)
    if match:
        body = match.group("body") or ""
        if (
            CONTINUATION_REQUIRES_RIGHT_SEQUENCE
            and body[:1] == CONTINUATION_INDICATOR
            and body[1:2].isalnum()
            and not has_right_sequence(text)
        ):
            return text
        return body

    return text


def strip_right_sequence(line: str) -> str:
    """Remove columns 73-80, but only when they really are a sequence.

    Truncating unconditionally destroyed body text on any generated line
    that overran column 72.
    """
    text = _clean(line)

    if is_fixed_format_line(text):
        if has_right_sequence(text):
            return text[:RIGHT_SEQUENCE_START]
        return text

    match = RIGHT_SEQUENCE_PATTERN.match(text)
    if match:
        return match.group("body")

    return text


def strip_nested_sequence(body: str) -> str:
    """Remove a sequence area that has leaked into a body.

    Guarded and capped. The leading indicator is preserved so the
    strip_sequence_numbers() contract is not broken.
    """
    if not STRIP_NESTED_SEQUENCE:
        return str(body or "")

    text = str(body or "")
    indicator = ""

    if text[:1] in VALID_INDICATORS:
        indicator, text = text[0], text[1:]

    for _ in range(MAX_NESTED_SEQUENCE_PASSES):
        candidate = text.lstrip()
        match = NESTED_SEQUENCE_PATTERN.match(candidate)
        if not match:
            break
        text = match.group("rest") or ""

    return f"{indicator}{text}"


def strip_sequence_numbers(line: str) -> str:
    """Remove columns 1-6 and 73-80, KEEPING column 7 onwards.

    A comment line therefore still begins with its '*' or '/' indicator,
    preserving the contract every existing caller depends on. A nested
    sequence area left by an earlier pass is removed as well.
    """
    text = _clean(line)

    if CONTINUATION_REQUIRES_RIGHT_SEQUENCE and is_paragraph_number_prefix(text):
        return text

    if is_fixed_format_line(text):
        padded = text.ljust(RIGHT_SEQUENCE_END)
        body = padded[INDICATOR_INDEX:RIGHT_SEQUENCE_START].rstrip()
        return strip_nested_sequence(body)

    body = strip_right_sequence(strip_left_sequence(text)).rstrip()
    return strip_nested_sequence(body)


def logical_body(line: str) -> str:
    """Columns 8-72 only, stripped. Indicator excluded."""
    text = _clean(line)

    if CONTINUATION_REQUIRES_RIGHT_SEQUENCE and is_paragraph_number_prefix(text):
        return text.strip()

    if is_fixed_format_line(text):
        padded = text.ljust(RIGHT_SEQUENCE_END)
        body = padded[BODY_START:BODY_END].rstrip()
        return strip_nested_sequence(body).strip()

    return strip_sequence_numbers(text).strip()


# =====================================================================
# Rebuilding
# =====================================================================
def replace_body(line: str, new_body: str) -> str:
    """Rewrite columns 8-72 and keep both sequence areas in place.

    Returns the line unchanged when the replacement will not fit, so a
    rewrite can never displace the right sequence. Callers that must know
    should compare the result with the input.

    CORRECTION 5 - an unframed paragraph header is treated as free-form,
    so its six-digit number is never promoted into a sequence area.
    """
    text = _clean(line)
    body = str(new_body or "").rstrip()

    if not is_fixed_format_line(text):
        leading = len(text) - len(text.lstrip())
        return f"{' ' * leading}{body}"

    if len(body) > BODY_WIDTH:
        return text

    left = text[LEFT_SEQUENCE_START:LEFT_SEQUENCE_END]
    indicator = text[INDICATOR_INDEX]
    right = (
        text[RIGHT_SEQUENCE_START:RIGHT_SEQUENCE_END]
        if has_right_sequence(text)
        else ""
    )

    return f"{left}{indicator}{body.ljust(BODY_WIDTH)}{right}"


__all__ = [
    # geometry
    "LEFT_SEQUENCE_START",
    "LEFT_SEQUENCE_END",
    "INDICATOR_INDEX",
    "BODY_START",
    "BODY_END",
    "RIGHT_SEQUENCE_START",
    "RIGHT_SEQUENCE_END",
    "LINE_WIDTH",
    "BODY_WIDTH",
    "INDICATED_BODY_WIDTH",
    # indicators
    "VALID_INDICATORS",
    "COMMENT_INDICATORS",
    "DEBUG_INDICATORS",
    "CONTINUATION_INDICATOR",
    "BLANK_INDICATOR",
    # switches
    "CONTINUATION_REQUIRES_RIGHT_SEQUENCE",
    "STRIP_NESTED_SEQUENCE",
    "MAX_NESTED_SEQUENCE_PASSES",
    # patterns
    "LEFT_SEQUENCE_PATTERN",
    "RIGHT_SEQUENCE_PATTERN",
    "NESTED_SEQUENCE_PATTERN",
    "SEQUENCE_ARTIFACT_PATTERN",
    # classification
    "is_fixed_format_line",
    "is_paragraph_number_prefix",
    "has_right_sequence",
    "indicator_of",
    "is_comment_or_control",
    "is_blank",
    "has_nested_sequence_area",
    "is_sequence_artifact",
    # stripping
    "strip_left_sequence",
    "strip_right_sequence",
    "strip_nested_sequence",
    "strip_sequence_numbers",
    "logical_body",
    # rebuilding
    "replace_body",
]
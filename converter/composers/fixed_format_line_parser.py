# LOCATION: converter/composers/fixed_format_line_parser.py
# ACTION: REPLACE ENTIRE FILE

"""Fixed-format COBOL line parser.

Responsibilities:
  - Parse already sequenced 80-column COBOL records.
  - Parse unsequenced COBOL lines.
  - Strip old left and right sequence numbers.
  - Preserve COBOL body indentation.
  - Detect indicator column values.

CORRECTION 1 - the length test was fatal
-----------------------------------------
_is_fixed_format_line required len(text) >= TOTAL_WIDTH and digits at
columns 73-80. A record short by even ONE character was therefore
classified as UNSEQUENCED, and its entire content - its own sequence
area included - was written into columns 8-72 of a new record:

    000380 000380* 2004/12 REPRENDRE N DE TITRE EN OUTPUT (12 POS

A record goes short for ordinary reasons: a blank right sequence, a
truncated line, or a multi-byte character severed upstream.

"Is this record sequenced" and "does it carry a right sequence" are now
two separate questions. Coupling them is what tied the two failures
together.

CORRECTION 2 - rstrip() destroyed the body padding
---------------------------------------------------
parse_line() and replace_body_preserving_sequence() opened with

    text = str(line or "").rstrip()

Trailing blanks are not decoration: they are what hold the right sequence
at column 73. A record whose columns 73-80 are blank was stripped back to
column 72, failed the width test, and fell through to the loose path -
where its sequence area became body text. Only the LINE ENDING is removed
now.

CORRECTION 3 - geometry was imported from a composer
-----------------------------------------------------
RIGHT_SEQUENCE_START and RIGHT_SEQUENCE_END were imported from
converter.composers.retrieval_commit_cleanup_composer. Column geometry
belongs in rules/, and a parser importing a composer is a layering
inversion that will deadlock as a circular import the moment that
composer imports anything from this package.
"""

from __future__ import annotations

from converter.composers.fixed_format_sequence_stripper import (
    FixedFormatSequenceStripper,
)
from patterns.fixed_format_patterns import (
    DEBUG_LINE_PATTERN,
    TRUE_LEFT_SEQUENCE_PATTERN,
)
from rules.fixed_format_rules import (
    BODY_END,
    BODY_START,
    BODY_WIDTH,
    COMMENT_INDICATOR,
    DEBUG_INDICATOR,
    INDICATOR_INDEX,
    LEFT_SEQUENCE_END,
    LEFT_SEQUENCE_START,
    LEFT_SEQUENCE_WIDTH,
    LINE_ENDINGS,
    MIN_ADDRESSABLE_LENGTH,
    PAGE_INDICATOR,
    RIGHT_SEQUENCE_END,
    RIGHT_SEQUENCE_START,
    RIGHT_SEQUENCE_WIDTH,
    SPACE_INDICATOR,
    TOTAL_WIDTH,
    VALID_INDICATORS,
)


class FixedFormatLineParser(FixedFormatSequenceStripper):
    """Parses fixed-format and loose COBOL lines safely."""

    # =================================================================
    # Public entry points
    # =================================================================
    def parse_line(self, line: str) -> dict[str, str | bool]:
        """Split one raw record into its four fixed-format areas.

        Only the line ending is removed. Trailing blanks are preserved,
        because they position the right sequence at column 73.
        """
        text = str(line or "").rstrip(LINE_ENDINGS)

        fixed = self.parse_fixed_80_line(text)
        if fixed is not None:
            return fixed

        body = self.remove_loose_sequence_numbers(text)
        indicator = self.indicator_for_body(body)
        body = self.strip_inline_indicator(body=body, indicator=indicator)

        return {
            "left_sequence": "",
            "indicator": indicator,
            "body": body,
            "right_sequence": "",
            "is_fixed_format": False,
        }

    def parse_fixed_80_line(self, line: str) -> dict[str, str | bool] | None:
        """Parse a sequenced record, whatever its physical length.

        A record without a right sequence keeps every character from
        column 8 onwards as body. Slicing columns 73-80 off a record that
        does not have them destroys real COBOL text.
        """
        text = str(line or "").rstrip(LINE_ENDINGS)

        if not self._is_fixed_format_line(text):
            return None

        indicator = text[INDICATOR_INDEX:INDICATOR_INDEX + 1]
        if indicator not in VALID_INDICATORS:
            indicator = SPACE_INDICATOR

        if self._has_right_sequence(text):
            body = text[BODY_START:BODY_END].rstrip()
            right = text[RIGHT_SEQUENCE_START:RIGHT_SEQUENCE_END]
        else:
            body = text[BODY_START:].rstrip()
            right = ""

        return {
            "left_sequence": text[LEFT_SEQUENCE_START:LEFT_SEQUENCE_END],
            "indicator": indicator,
            "body": body,
            "right_sequence": right,
            "is_fixed_format": True,
        }

    def body_for_boolean_merge(self, line: str) -> str:
        return str(self.parse_line(line).get("body", ""))

    # =================================================================
    # Indicator handling
    # =================================================================
    def indicator_for_body(self, body: str) -> str:
        text = str(body or "")
        if not text:
            return SPACE_INDICATOR

        stripped = text.lstrip()
        if stripped.startswith(COMMENT_INDICATOR):
            return COMMENT_INDICATOR
        if stripped.startswith(PAGE_INDICATOR):
            return PAGE_INDICATOR
        if DEBUG_LINE_PATTERN.match(text):
            return DEBUG_INDICATOR
        return SPACE_INDICATOR

    def strip_inline_indicator(self, body: str, indicator: str) -> str:
        text = str(body or "")

        if indicator in {COMMENT_INDICATOR, PAGE_INDICATOR}:
            stripped = text.lstrip()
            if stripped.startswith(indicator):
                return stripped[1:].lstrip()

        if indicator == DEBUG_INDICATOR and DEBUG_LINE_PATTERN.match(text):
            stripped = text.lstrip()
            if stripped[:1].upper() == DEBUG_INDICATOR:
                return stripped[1:]

        return text.rstrip()

    def is_debug_line(self, stripped: str) -> bool:
        return bool(DEBUG_LINE_PATTERN.match(str(stripped or "")))

    # =================================================================
    # Rebuilding
    # =================================================================
    def replace_body_preserving_sequence(
        self,
        original_line: str,
        new_body: str,
    ) -> str:
        """Rewrite columns 8-72 and keep both sequence areas in place.

        A record that carried NO right sequence does not gain a fabricated
        one. zfill(8) on an empty string produced '00000000', inventing a
        sequence number the source never had.
        """
        text = str(original_line or "").rstrip(LINE_ENDINGS)
        parsed = self.parse_line(text)
        body = str(new_body or "").rstrip()

        if bool(parsed.get("is_fixed_format")):
            left = str(parsed.get("left_sequence") or "")
            left = left.zfill(LEFT_SEQUENCE_WIDTH)[-LEFT_SEQUENCE_WIDTH:]

            indicator = str(parsed.get("indicator") or SPACE_INDICATOR)[:1]
            if indicator not in VALID_INDICATORS:
                indicator = SPACE_INDICATOR

            raw_right = str(parsed.get("right_sequence") or "")
            right = (
                raw_right.zfill(RIGHT_SEQUENCE_WIDTH)[-RIGHT_SEQUENCE_WIDTH:]
                if raw_right
                else ""
            )

            area = body[:BODY_WIDTH].ljust(BODY_WIDTH)
            return f"{left}{indicator}{area}{right}"

        match = TRUE_LEFT_SEQUENCE_PATTERN.match(text)
        if match:
            left = str(match.group("left") or "")
            left = left.zfill(LEFT_SEQUENCE_WIDTH)[-LEFT_SEQUENCE_WIDTH:]
            return f"{left} {body}"

        return body

    # =================================================================
    # Classification
    # =================================================================
    def _is_fixed_format_line(self, line: str) -> bool:
        """True when columns 1-6 are numeric and column 7 is an indicator.

        The right sequence is deliberately NOT required. Demanding it is
        what caused a short record's left sequence to be parsed as COBOL
        text and duplicated into the output.
        """
        text = str(line or "").rstrip(LINE_ENDINGS)

        if len(text) < MIN_ADDRESSABLE_LENGTH:
            return False

        if not text[LEFT_SEQUENCE_START:LEFT_SEQUENCE_END].isdigit():
            return False

        return text[INDICATOR_INDEX] in VALID_INDICATORS

    def _has_right_sequence(self, line: str) -> bool:
        """True only when columns 73-80 really hold eight digits."""
        text = str(line or "").rstrip(LINE_ENDINGS)

        if len(text) < RIGHT_SEQUENCE_END:
            return False

        return text[RIGHT_SEQUENCE_START:RIGHT_SEQUENCE_END].isdigit()

    def is_strict_fixed_line(self, line: str) -> bool:
        """A complete 80-column record: sequenced AND right-sequenced.

        Use this only where a FULL record is genuinely required, never to
        decide whether a line is sequenced at all.
        """
        text = str(line or "").rstrip(LINE_ENDINGS)
        return (
            len(text) == TOTAL_WIDTH
            and self._is_fixed_format_line(text)
            and self._has_right_sequence(text)
        )


__all__ = ["FixedFormatLineParser"]
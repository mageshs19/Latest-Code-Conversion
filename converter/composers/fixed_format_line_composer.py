# LOCATION: converter/composers/fixed_format_line_composer.py
# ACTION: REPLACE ENTIRE FILE

"""Per-line composition: parse, area-body, wrap, sequence, compose.

Depends on the host class for ``self.line_parser``, ``self.body_formatter``
and ``self.wrapper``. Layout constants and patterns are external.

CORRECTION - width was measured in BYTES
-----------------------------------------
_compose_line previously ended with:

    line_bytes = final_line.encode('utf-8')
    if len(line_bytes) > TOTAL_WIDTH:
        line_bytes = line_bytes[:TOTAL_WIDTH]
        final_line = line_bytes.decode('utf-8', errors='ignore')
    final_bytes = final_line.encode('utf-8')
    if len(final_bytes) < TOTAL_WIDTH:
        final_line = final_line + (' ' * (TOTAL_WIDTH - len(final_bytes)))

A record carrying one non-ASCII character is 80 CHARACTERS but 81 BYTES
in UTF-8, so this:

    1. truncated to 80 bytes, severing the trailing byte,
    2. decoded with errors='ignore', SILENTLY DROPPING the severed
       character - the record is now 79 CHARACTERS,
    3. padded to 80 BYTES, which the 2-byte character already satisfied,
       so no padding was added.

FixedFormatLineParser then rejected the 79-character record as
unsequenced and its own sequence area was written into the body of a new
record:

    000380 000380* 2004/12 REPRENDRE N DE TITRE EN OUTPUT (12 POS

A COBOL source record is 80 CHARACTER POSITIONS. Encoding is the writer's
concern, not this composer's.
"""

from __future__ import annotations

from patterns.fixed_format_patterns import (
    DIVISION_PATTERN,
    SEQUENCE_ONLY_PATTERN,
)
from rules.fixed_format_rules import (
    BODY_WIDTH,
    COMMENT_INDICATOR,
    DEBUG_INDICATOR,
    DEBUG_INDICATOR_LOWER,
    FIXED_FORMAT_MESSAGES,
    LEFT_SEQUENCE_WIDTH,
    PAGE_INDICATOR,
    PROCEDURE_DIVISION_NAME,
    RIGHT_SEQUENCE_WIDTH,
    SPACE_INDICATOR,
    TOTAL_WIDTH,
    VALID_INDICATORS,
)

DEFAULT_PROCEDURE_INDENT = " "


class FixedFormatLineComposer:
    """Per-line composition: parse, area-body, wrap, sequence, compose."""

    # =================================================================
    # One raw source line
    # =================================================================
    def _compose_body_lines(
        self,
        *,
        raw_text: str,
        state,
        current_division: str,
        inside_exec_sql: bool,
        previous_procedure_indent: str,
        preserve_blank_lines: bool,
        output_lines: list[str],
    ) -> tuple[str, bool, str]:
        """Process one raw line, appending composed records.

        Returns the updated (current_division, inside_exec_sql,
        previous_procedure_indent) tuple.
        """
        if SEQUENCE_ONLY_PATTERN.match(raw_text.strip()):
            return current_division, inside_exec_sql, previous_procedure_indent

        parsed = self.line_parser.parse_line(raw_text)
        indicator = str(parsed["indicator"])
        body = str(parsed["body"])
        logical = body.strip()

        if not logical and indicator == SPACE_INDICATOR:
            self._append_blank(state, preserve_blank_lines, output_lines)
            return current_division, inside_exec_sql, previous_procedure_indent

        division_match = DIVISION_PATTERN.match(logical)
        if division_match:
            current_division = division_match.group(1).upper()
            previous_procedure_indent = DEFAULT_PROCEDURE_INDENT

        if self.body_formatter.is_exec_sql_start(logical):
            inside_exec_sql = True

        area_body = self.body_formatter.area_body(
            body=body,
            logical=logical,
            current_division=current_division,
            inside_exec_sql=inside_exec_sql,
            indicator=indicator,
            previous_procedure_indent=previous_procedure_indent,
        )

        physical_bodies = self.wrapper.wrap_body(
            body=area_body,
            indicator=indicator,
            inside_exec_sql=inside_exec_sql,
            current_division=current_division,
            previous_procedure_indent=previous_procedure_indent,
        )
        physical_bodies = self.wrapper.repair_boolean_operator_only_lines(
            physical_bodies
        )

        for index, physical_body in enumerate(physical_bodies):
            physical_indicator = (
                self._continuation_indicator(indicator)
                if index > 0
                else indicator
            )
            output_lines.append(
                self._compose_line(
                    left_seq=state.current_left(),
                    indicator=physical_indicator,
                    area_body=physical_body,
                    right_seq=state.current_right(),
                )
            )
            state.advance()

        if (
            current_division == PROCEDURE_DIVISION_NAME
            and indicator == SPACE_INDICATOR
            and physical_bodies
            and not self.body_formatter.is_area_a_statement(logical)
        ):
            previous_procedure_indent = self.body_formatter.leading_spaces(
                physical_bodies[0],
                default=DEFAULT_PROCEDURE_INDENT,
            )

        if self.body_formatter.is_exec_sql_end(logical):
            inside_exec_sql = False

        return current_division, inside_exec_sql, previous_procedure_indent

    def _append_blank(
        self,
        state,
        preserve_blank_lines: bool,
        output_lines: list[str],
    ) -> None:
        if not preserve_blank_lines:
            return

        output_lines.append(
            self._compose_line(
                left_seq=state.current_left(),
                indicator=SPACE_INDICATOR,
                area_body="",
                right_seq=state.current_right(),
            )
        )
        state.advance()

    def _continuation_indicator(self, indicator: str) -> str:
        if indicator in {COMMENT_INDICATOR, PAGE_INDICATOR}:
            return indicator
        if indicator in {DEBUG_INDICATOR, DEBUG_INDICATOR_LOWER}:
            return DEBUG_INDICATOR
        return SPACE_INDICATOR

    # =================================================================
    # One 80-column record
    # =================================================================
    def _compose_line(
        self,
        left_seq: str,
        indicator: str,
        area_body: str,
        right_seq: str,
    ) -> str:
        """Assemble one 80-COLUMN record. Width is counted in CHARACTERS."""
        safe_left = str(left_seq or "").zfill(LEFT_SEQUENCE_WIDTH)
        safe_left = safe_left[-LEFT_SEQUENCE_WIDTH:]

        safe_right = str(right_seq or "").zfill(RIGHT_SEQUENCE_WIDTH)
        safe_right = safe_right[-RIGHT_SEQUENCE_WIDTH:]

        safe_indicator = str(indicator or SPACE_INDICATOR)[:1]
        if safe_indicator not in VALID_INDICATORS:
            safe_indicator = SPACE_INDICATOR
        if safe_indicator == DEBUG_INDICATOR_LOWER:
            safe_indicator = DEBUG_INDICATOR

        safe_body = str(area_body or "").rstrip()

        if len(safe_body) > BODY_WIDTH:
            self._report_truncation(safe_body)
            safe_body = safe_body[:BODY_WIDTH]

        body_area = safe_body.ljust(BODY_WIDTH)
        line = f"{safe_left}{safe_indicator}{body_area}{safe_right}"

        # All four fields are already fixed width, so this can only fire
        # if a constant has drifted - a defect worth reporting rather than
        # silently papering over.
        if len(line) != TOTAL_WIDTH:
            self._report_geometry_drift(len(line))
            line = line[:TOTAL_WIDTH].ljust(TOTAL_WIDTH)

        return line

    # =================================================================
    # Diagnostics
    # =================================================================
    def _report_truncation(self, body: str) -> None:
        """Record a body that did not fit columns 8-72."""
        messages = getattr(self, "messages", None)
        if messages is None:
            return

        template = FIXED_FORMAT_MESSAGES.get("body_truncated", "")
        if not template:
            return

        messages.append(
            template.format(
                width=len(body),
                limit=BODY_WIDTH,
                body=body.strip()[:40],
            )
        )

    def _report_geometry_drift(self, width: int) -> None:
        """Record a record that did not assemble to exactly 80 columns."""
        messages = getattr(self, "messages", None)
        if messages is None:
            return

        template = FIXED_FORMAT_MESSAGES.get("geometry_drift", "")
        if template:
            messages.append(template.format(width=width, limit=TOTAL_WIDTH))
            return

        messages.append(
            f"Fixed format: record assembled to {width} columns, "
            f"expected {TOTAL_WIDTH}."
        )


__all__ = ["FixedFormatLineComposer"]
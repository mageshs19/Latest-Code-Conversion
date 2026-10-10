"""
Final sequence resequencer service.

Generic behavior:
- Resequences already fixed-format 80-column COBOL lines.
- Preserves column 7 indicator.
- Preserves columns 8-72 COBOL body.
- Rewrites only columns 1-6 and 73-80.
- Does not hardcode program names, tables, columns, cursors, DCLGEN names,
  host variables, or business fields.

Purpose:
- Remove sequence gaps introduced by safe generated-line cleanup.
"""

from __future__ import annotations

from rules.fixed_format_rules import (
    DEFAULT_LEFT_START,
    DEFAULT_LEFT_STEP,
    DEFAULT_RIGHT_START,
    DEFAULT_RIGHT_STEP,
    TOTAL_WIDTH,
)


class FinalSequenceResequencerService:
    """
    Resequences final manual-style COBOL output.

    Physical layout:
    - Columns 1-6   : left sequence number
    - Column 7      : indicator area
    - Columns 8-72  : COBOL body
    - Columns 73-80 : right sequence number

    This service assumes the final output is already fixed-format.
    It does not reformat or wrap COBOL statements.
    """

    LEFT_START = 0
    LEFT_END = 6
    RIGHT_START = 72
    RIGHT_END = 80

    def resequence(
        self,
        text: str,
        left_start: int = DEFAULT_LEFT_START,
        left_step: int = DEFAULT_LEFT_STEP,
        right_start: int = DEFAULT_RIGHT_START,
        right_step: int = DEFAULT_RIGHT_STEP,
    ) -> str:
        source = str(text or "")

        if not source:
            return ""

        output: list[str] = []
        left_value = int(left_start)
        right_value = int(right_start)

        for line in source.splitlines():
            # Check if already formatted
            if self._is_fixed_format_line(line):
                output.append(
                    self._replace_sequence(
                        line=line,
                        left_value=left_value,
                        right_value=right_value,
                    )
                )
                left_value += int(left_step)
                right_value += int(right_step)
            # Check if it's a blank line
            elif not line.strip():
                # Format blank line as 80-char line with sequence numbers
                output.append(
                    self._format_blank_line(
                        left_value=left_value,
                        right_value=right_value,
                    )
                )
                left_value += int(left_step)
                right_value += int(right_step)
            # Check if it's a COBOL line that needs formatting
            elif self._is_cobol_line(line):
                output.append(
                    self._format_and_sequence(
                        line=line,
                        left_value=left_value,
                        right_value=right_value,
                    )
                )
                left_value += int(left_step)
                right_value += int(right_step)
            # Unknown line - pass through as-is
            else:
                output.append(line)
                left_value += int(left_step)
                right_value += int(right_step)

        return "\n".join(output).rstrip() + "\n"

    def _is_fixed_format_line(
        self,
        line: str,
    ) -> bool:
        text = str(line or "")

        if len(text) != TOTAL_WIDTH:
            return False

        if not text[self.LEFT_START:self.LEFT_END].isdigit():
            return False

        if not text[self.RIGHT_START:self.RIGHT_END].isdigit():
            return False

        return True

    def _is_cobol_line(
        self,
        line: str,
    ) -> bool:
        """Check if line is a COBOL statement or comment that needs formatting."""
        text = str(line or "")
        
        # Skip empty lines or lines with only whitespace
        if not text.strip():
            return False
        
        # Lines that are not already 80 chars need formatting
        if len(text) < TOTAL_WIDTH:
            return True
        
        return False

    def _format_blank_line(
        self,
        left_value: int,
        right_value: int,
    ) -> str:
        """Format a blank line as 80 chars with sequence numbers."""
        left = f"{left_value:06d}"
        right = f"{right_value:08d}"
        
        # Blank line: sequence + space indicator + 65 spaces + right sequence
        code_area_width = self.RIGHT_START - self.LEFT_END  # 72 - 6 = 66
        code_area = " " * code_area_width
        
        return left + code_area + right

    def _format_and_sequence(
        self,
        line: str,
        left_value: int,
        right_value: int,
    ) -> str:
        """Format unformatted COBOL line to 80 chars with sequence numbers."""
        text = str(line or "")
        
        # Determine if this is a comment line
        is_comment = False
        indicator = " "
        code_content = text.rstrip()
        
        # Check if line starts with * (comment)
        if code_content.startswith('*'):
            is_comment = True
            indicator = "*"
            # Remove the * from the content since it will go in column 7
            code_content = code_content[1:]
        elif code_content.startswith('/'):
            indicator = "/"
            code_content = code_content[1:]
        
        # Pad or truncate to fit in columns 8-72 (65 characters for code area)
        code_area_width = self.RIGHT_START - self.LEFT_END  # 72 - 6 = 66 (includes indicator column)
        
        # Format: left_seq (6 chars) + indicator (1 char) + code (65 chars) + right_seq (8 chars)
        left = f"{left_value:06d}"
        right = f"{right_value:08d}"
        
        # Ensure code fits in the code area (with indicator)
        if len(code_content) < code_area_width - 1:  # -1 for indicator column
            # Pad with spaces
            code_area = indicator + code_content.ljust(code_area_width - 1)
        else:
            # Truncate if too long (shouldn't happen with normal COBOL)
            code_area = indicator + code_content[:(code_area_width - 1)]
        
        return left + code_area + right

    def _replace_sequence(
        self,
        line: str,
        left_value: int,
        right_value: int,
    ) -> str:
        text = str(line or "")

        left = f"{left_value:06d}"
        right = f"{right_value:08d}"

        return (
            left
            + text[self.LEFT_END:self.RIGHT_START]
            + right
        )
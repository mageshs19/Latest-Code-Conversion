# LOCATION: converter/transformers/unnecessary_comments_cleanup.py
# ACTION: REPLACE ENTIRE FILE

"""Remove unnecessary comment blocks from generated COBOL programs.

Removes:
- Comment blocks describing manual mapping work (no DB2 columns)
- Comment blocks describing non-executed commented-out code
- Multi-line French comment blocks explaining skipped IDMS logic

Preserves:
- Comments explaining active business logic
- Comments marking DB2-KEEP sections
- Single meaningful comments

CORRECTION 1 - the keep marker was never recognised in fixed format

DB2_KEEP_PATTERN was

    r"^\\s*\\*\\s*DB2-KEEP"

which demands optional whitespace then '*'. A fixed-format marker is

    002420*DB2-KEEP: VMBWCEF has no DB2 layout after conversion.

and begins with six DIGITS, so it never matched. _is_comment_line()
already understood fixed format, so the line WAS collected into a
block - and then removed, because _should_remove_comment_block() tests

    if "no db2" in block_text

and the marker's own wording is "has NO DB2 layout". The guard's
decision record deleted itself, taking the commented statement with it:

    MOVE SPACES TO VMBWCEF          <- vanished without trace

StructuralSafetyComposer promises "COMMENT-ONLY, never deletes". This
pass was breaking that promise one stage later.

CORRECTION 2 - the keep check was per LINE, not per BLOCK

Even recognised, a marker only protected its own line and stopped block
collection. A block whose SECOND line carries the marker could still
lose its first. A keep marker makes the whole run a DECISION RECORD:
some other pass wrote "I could not convert this, here it is for
review". None of it is noise, and the refusal is now reported so the
decision is visible rather than silent.

THE INVARIANT

    A pass that removes comments must never remove a comment another
    pass wrote as a decision record.
"""

from __future__ import annotations

import re
from typing import Optional


class UnnecessaryCommentsCleanup:
    """Remove comment blocks that don't contribute to code understanding."""

    # Patterns for removable comment blocks
    NO_DB2_PATTERN = re.compile(
        r"^\s*\*\s*(?:[-\w]+\s*)?(?:no DB2|no columnas?|not found|manual)",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    FRENCH_RESTART_PATTERN = re.compile(
        r"^\s*\*\s*(?:RESTART|SI EXISTE|SINON|RECHERCHE)",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    COMMENTED_CODE_BLOCK_PATTERN = re.compile(
        r"^\s*\*\s*(?:IF|MOVE|PERFORM|ADD|DO|END-IF|ELSE|UNTIL)",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # Matches a keep marker in BOTH line formats - see CORRECTION 1:
    #
    #   *DB2-KEEP ...            free form
    #      *DB2-KEEP ...         free form, indented
    #   002420*DB2-KEEP ...      fixed format, indicator in column 7
    #   002420 *DB2-KEEP ...     fixed format, blank indicator
    DB2_KEEP_PATTERN = re.compile(
        r"^\s*(?:\d{6})?\s*\*\s*DB2-KEEP",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    KEPT_BLOCK_MESSAGE = (
        "Kept comment block at lines {start}-{end}; it carries a "
        "DB2-KEEP marker and is a decision record, not noise."
    )

    def __init__(self) -> None:
        self.messages: list[str] = []

    def apply(self, cobol_text: str) -> tuple[str, list[str]]:
        """Remove unnecessary comment blocks from COBOL text."""
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        text = self._remove_unnecessary_comment_blocks(text)

        return text, self.messages

    def _remove_unnecessary_comment_blocks(self, text: str) -> str:
        """Remove comment blocks that don't add value."""
        lines = text.split("\n")
        result = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is a comment line
            if self._is_comment_line(line):
                # Identify start of comment block
                block_start = i
                block_lines = [line]

                # Collect consecutive comment lines. The block is NOT
                # cut at a keep marker any more: a marker protects the
                # whole run, so the run has to be seen whole first.
                j = i + 1
                while j < len(lines) and self._is_comment_line(lines[j]):
                    block_lines.append(lines[j])
                    j += 1

                # CORRECTION 2 - a keep marker anywhere in the block
                # makes the entire block a decision record.
                if self._block_has_keep_marker(block_lines):
                    result.extend(block_lines)
                    if len(block_lines) > 1:
                        self.messages.append(
                            self.KEPT_BLOCK_MESSAGE.format(
                                start=block_start + 1, end=j
                            )
                        )
                    i = j
                    continue

                # Check if this block should be removed
                if self._should_remove_comment_block(block_lines, lines, j):
                    # Skip this entire comment block
                    i = j
                    self.messages.append(
                        f"Removed comment block at lines {block_start + 1}-{j}"
                    )
                    continue
                else:
                    # Keep the comment block
                    result.extend(block_lines)
                    i = j
            else:
                result.append(line)
                i += 1

        return "\n".join(result)

    def _block_has_keep_marker(self, block_lines: list[str]) -> bool:
        """True when any line in the block is a keep marker."""
        return any(
            self.DB2_KEEP_PATTERN.search(line) for line in block_lines
        )

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a pure comment line.

        Handles two formats:
        1. With line numbers: columns 1-6 are line numbers, column 7 is indicator
           (standard COBOL fixed format)
        2. Without line numbers: column 1 is indicator (after cleanup/transformation)
        """
        if not line or len(line) < 1:
            return False

        # Format 1: with line numbers (position 7 = column 6, 0-indexed)
        if len(line) >= 7 and line[6] == "*":
            return True

        # Format 2: without line numbers (position 1 = column 0)
        if line[0] == "*":
            return True

        # Format 3: with leading spaces then asterisk
        stripped = line.lstrip()
        if stripped.startswith("*"):
            return True

        return False

    def _should_remove_comment_block(
        self, block_lines: list[str], all_lines: list[str], block_end: int
    ) -> bool:
        """Determine if a comment block should be removed.

        Never reached for a block carrying a keep marker - that test
        runs first, in the caller. The "no db2" test below is broad
        enough to match a keep marker's own wording, which is how the
        decision record deleted itself.
        """
        block_text = "\n".join(block_lines).lower()

        # Remove if it describes manual mapping work
        if "no db2" in block_text or "map manually" in block_text:
            return True

        # Remove if it's all French restart logic comments
        if (
            "restart" in block_text
            and "recherche" in block_text
            and "si existe" in block_text
        ):
            return True

        # Remove if it describes only commented-out code (more than 3 lines)
        if len(block_lines) > 2 and self._is_all_commented_code_description(
            block_lines, all_lines, block_end
        ):
            return True

        # Remove if it's just structure explanation with no business value
        if len(block_lines) > 3 and self._is_pure_structure_comment(block_text):
            return True

        # Remove if it contains only commented code lines (starting with * MOVE, * IF, etc.)
        if self._is_block_of_commented_code(block_lines):
            return True

        return False

    def _is_block_of_commented_code(self, block_lines: list[str]) -> bool:
        """Check if block consists entirely of commented-out code statements."""
        if len(block_lines) < 2:
            return False

        code_comment_count = 0
        for line in block_lines:
            line_lower = line.lower()
            # Check for commented COBOL statements
            if any(
                kw in line_lower
                for kw in [
                    "* move ",
                    "* if ",
                    "* perform ",
                    "* add ",
                    "* until ",
                    "* else",
                    "* end-if",
                    "*  move ",
                    "*  if ",
                    "*  perform ",
                ]
            ):
                code_comment_count += 1

        return code_comment_count > (len(block_lines) * 0.6)

    def _is_all_commented_code_description(
        self, block_lines: list[str], all_lines: list[str], block_end: int
    ) -> bool:
        """Check if block only describes commented-out code that follows."""
        # Look at what comes after the comment block
        if block_end >= len(all_lines):
            return False

        # Check if next non-empty line is an empty line followed by commented code
        next_idx = block_end
        while next_idx < len(all_lines) and not all_lines[next_idx].strip():
            next_idx += 1

        if next_idx >= len(all_lines):
            return False

        # Count if the following lines are mostly comments
        next_line = all_lines[next_idx]
        if self._is_comment_line(next_line):
            return True

        return False

    def _is_pure_structure_comment(self, text: str) -> bool:
        """Check if comment is just describing structure."""
        keywords = ["move", "if", "perform", "add", "do", "end-if", "else", "until"]
        count = sum(1 for kw in keywords if kw in text)
        return count >= 3


__all__ = ["UnnecessaryCommentsCleanup"]
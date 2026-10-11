# LOCATION: converter/composers/unnecessary_comments_cleanup_composer.py
# ACTION: REPLACE ENTIRE FILE

"""Composer that applies unnecessary comments cleanup to generated COBOL.

Two passes, in order:

  1. MARKER  drop generated *DB2: marker comments. Owned here because
             neither pattern had a consumer - TRACE had none at all, and
             NOISE was handled only by ResidualIdmsCommentCleanup, which
             is not registered in the pipeline.

  2. BLOCK   delegate to UnnecessaryCommentsCleanup for the comment
             BLOCK heuristics (manual-mapping notes, commented-out
             logic, prose explaining skipped IDMS work).

DB2-KEEP is never touched by either pass. It flags a business line a
human must review.
"""

from __future__ import annotations

from converter.transformers.unnecessary_comments_cleanup import (
    UnnecessaryCommentsCleanup,
)
from patterns.cobol_cleanup_patterns import (
    RESIDUAL_IDMS_COMMENT_PATTERN,
    TRACE_MARKER_COMMENT_PATTERN,
)
from patterns.sequence_patterns import strip_sequence_numbers
from rules.unnecessary_comments_rules import (
    MARKER_CLEANUP_MESSAGE,
    REMOVE_NOISE_MARKERS,
    REMOVE_TRACE_MARKERS,
)

from patterns.cobol_cleanup_patterns import (
    RESIDUAL_IDMS_COMMENT_PATTERN,
    TRACE_MARKER_COMMENT_PATTERN,
)

class UnnecessaryCommentsCleanupComposer:
    """Removes unnecessary comment blocks from COBOL programs.

    Removes:
    - Generated *DB2: NOISE and TRACE marker comments
    - Blocks describing manual mapping work (no DB2 columns)
    - Blocks describing non-executed commented-out code
    - Prose blocks explaining skipped IDMS logic

    Preserves:
    - Comments explaining active business logic
    - DB2-KEEP marker comments
    - Meaningful single-line comments
    """

    def __init__(self) -> None:
        self.cleanup = UnnecessaryCommentsCleanup()
        self.messages: list[str] = []

    #
    # Public entry point
    #
    def compose(self, text: str) -> str:
        self.messages = []

        source = str(text or "")
        if not source:
            return source

        source = self._remove_marker_comments(source)
        source = self._remove_comment_blocks(source)
        return source

    #
    # Pass 1 - generated markers
    #
    def _remove_marker_comments(self, text: str) -> str:
        """Drop generated *DB2: marker comments.

        Two kinds, two policies:

          NOISE  a removal the operator does not need told about in the
                 delivered source ("COMMIT removed", "Removed residual
                 IDMS ..."). The conversion log already records it.

          TRACE  a conversion breadcrumb ("Converted OBTAIN FIRST ...",
                 "Materialised X from ..."). Useful during review, noise
                 in a delivered program.

        DB2_KEEP_PATTERN is read from the transformer rather than
        re-declared, so the two passes can never disagree about what a
        keep marker looks like.
        """
        lines = str(text or "").split("\n")
        output: list[str] = []
        removed = 0

        for line in lines:
            if UnnecessaryCommentsCleanup.DB2_KEEP_PATTERN.search(line):
                output.append(line)
                continue

            logical = self._logical(line)

            if REMOVE_NOISE_MARKERS and RESIDUAL_IDMS_COMMENT_PATTERN.match(logical):
                removed += 1
                continue

            if REMOVE_TRACE_MARKERS and TRACE_MARKER_COMMENT_PATTERN.match(logical):
                removed += 1
                continue

            output.append(line)

        if removed:
            self.messages.append(MARKER_CLEANUP_MESSAGE.format(count=removed))

        return "\n".join(output)

    #
    # Pass 2 - comment blocks, delegated
    #
    def _remove_comment_blocks(self, text: str) -> str:
        """Hand off to UnnecessaryCommentsCleanup.

        The transformer returns (text, messages). The isinstance guard
        tolerates a plain-string return so a signature change cannot
        make this stage silently stop cleaning.
        """
        result = self.cleanup.apply(text)

        if isinstance(result, tuple):
            cleaned, messages = result
            self.messages.extend(messages or [])
            return cleaned

        return str(result or text)

    #
    # Helpers
    #
    @staticmethod
    def _logical(line: str) -> str:
        """Body only, sequence areas removed."""
        return strip_sequence_numbers(str(line or "")).strip()


__all__ = ["UnnecessaryCommentsCleanupComposer"]
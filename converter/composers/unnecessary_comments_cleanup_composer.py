# LOCATION: converter/composers/unnecessary_comments_cleanup_composer.py

"""Composer that applies unnecessary comments cleanup to generated COBOL."""

from __future__ import annotations

from converter.transformers.unnecessary_comments_cleanup import (
    UnnecessaryCommentsCleanup,
)


class UnnecessaryCommentsCleanupComposer:
    """Removes unnecessary comment blocks from COBOL programs.
    
    Removes:
    - Blocks describing manual mapping work (no DB2 columns)
    - Blocks describing non-executed commented-out code
    - French comment blocks explaining skipped IDMS logic
    
    Preserves:
    - Comments explaining active business logic
    - DB2-KEEP marker comments
    - Meaningful single-line comments
    """

    def __init__(self) -> None:
        self.cleanup = UnnecessaryCommentsCleanup()
        self.messages: list[str] = []

    def compose(self, cobol_text: str) -> str:
        """Apply unnecessary comments cleanup."""
        text, cleanup_messages = self.cleanup.apply(cobol_text)
        self.messages = cleanup_messages
        return text

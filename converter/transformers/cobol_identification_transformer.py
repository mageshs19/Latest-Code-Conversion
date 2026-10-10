# LOCATION: converter/transformers/cobol_identification_transformer.py
"""Replace AUTHOR and DATE-WRITTEN in IDENTIFICATION DIVISION.

This transformer updates the AUTHOR and DATE-WRITTEN lines in the
COBOL program header to match the configured values from
rules/program_metadata_config.txt.
"""

from __future__ import annotations

import re

from converter.transformers.cobol_transformer_line_utils import (
    CobolTransformerLineUtils,
)
from rules.manual_reference_rules import (
    AUTHOR_TEMPLATE,
    DATE_WRITTEN_TEMPLATE,
    DEFAULT_AUTHOR,
    DEFAULT_DATE_WRITTEN,
)
from rules.program_metadata_loader import get_author, get_date_written


class CobolIdentificationTransformer:
    """Replaces AUTHOR and DATE-WRITTEN in IDENTIFICATION DIVISION."""

    def __init__(
        self,
        line_utils: CobolTransformerLineUtils | None = None,
    ) -> None:
        self.line_utils = line_utils or CobolTransformerLineUtils()
        self.messages: list[str] = []

    def reset(self) -> None:
        """Clear per-program state."""
        self.messages = []

    def author_replacement(
        self,
        *,
        original_line: str,
        logical_line: str,
    ) -> str | None:
        """Replace AUTHOR line with configured author name.
        
        Args:
            original_line: Original line with fixed-format spacing
            logical_line: Trimmed logical line content
            
        Returns:
            Replacement line or None if no replacement needed
        """
        author = get_author()
        if not author:
            return None

        # Match AUTHOR. line
        if not re.search(r"AUTHOR\.", logical_line, re.IGNORECASE):
            return None

        replacement_body = AUTHOR_TEMPLATE.format(author=author)
        
        return self.line_utils.replace_logical_body(
            original_line=original_line,
            replacement_body=replacement_body,
        )

    def date_written_replacement(
        self,
        *,
        original_line: str,
        logical_line: str,
    ) -> str | None:
        """Replace DATE-WRITTEN line with configured date.
        
        Args:
            original_line: Original line with fixed-format spacing
            logical_line: Trimmed logical line content
            
        Returns:
            Replacement line or None if no replacement needed
        """
        date_written = get_date_written()
        if not date_written:
            return None

        # Match DATE-WRITTEN. line
        if not re.search(r"DATE-WRITTEN\.", logical_line, re.IGNORECASE):
            return None

        replacement_body = DATE_WRITTEN_TEMPLATE.format(date_written=date_written)
        
        return self.line_utils.replace_logical_body(
            original_line=original_line,
            replacement_body=replacement_body,
        )


__all__ = ["CobolIdentificationTransformer"]

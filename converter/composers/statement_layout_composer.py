# LOCATION: converter/composers/statement_layout_composer.py
# ACTION: CREATE NEW FILE
"""Inserts a blank line before a paragraph header.

    WRITE UITRECORD.
    VERWERK-VMBEVEF.          <- runs straight into the next paragraph

becomes

    WRITE UITRECORD.

    VERWERK-VMBEVEF.

Text only. No statement is added, removed or reordered; the pass writes
blank lines and nothing else.

The inserted line borrows the sequence area of the header it precedes.
FinalSequenceResequencerService rewrites columns 1-6 and 73-80
afterwards, so the borrowed numbers are placeholders.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from rules.statement_layout_rules import (
    BLANK_LINE_BEFORE_PARAGRAPH,
    ENFORCE_STATEMENT_LAYOUT,
    NON_PARAGRAPH_WORDS,
    SENTENCE_TERMINATOR,
    SEPARATOR_INDICATORS,
    SKIPPABLE_INDICATORS,
    SQL_BLOCK_END,
    SQL_BLOCK_START,
    STATEMENT_LAYOUT_MESSAGES,
)

BLANK_BODY = ""
BLANK_INDICATOR = " "
INDICATOR_COLUMN = 6


class StatementLayoutComposer:
    """Separates paragraphs with a blank line."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

    #
    # Public entry point
    #
    def compose(self, text: str) -> str:
        self.messages = []

        source = str(text or "")
        if not source or not ENFORCE_STATEMENT_LAYOUT:
            return source

        if not BLANK_LINE_BEFORE_PARAGRAPH:
            return source

        lines = (
            source
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        output: list[str] = []
        inserted = 0
        in_sql = False

        for line in lines:
            in_sql = self._track_sql(line, in_sql)

            if in_sql or not self._is_paragraph_header(line):
                output.append(line)
                continue

            previous = self._last_populated(output)

            if previous is not None and not self._is_separator(previous):
                blank = self._clone(line, BLANK_BODY)
                if blank is not None:
                    output.append(blank)
                    inserted += 1

            output.append(line)

        self.messages.append(
            STATEMENT_LAYOUT_MESSAGES["blank_inserted"].format(count=inserted)
            if inserted
            else STATEMENT_LAYOUT_MESSAGES["none_needed"]
        )

        return "\n".join(output).rstrip() + "\n"

    #
    # Classification
    #
    def _is_paragraph_header(self, line: str) -> bool:
        """A single name ending in a period, starting in Area A.

        Area A is the discriminator. `WRITE UITRECORD.` contains a
        space and is a statement; `VERWERK-VMBEVEF.` is one word at
        body position 0 and is a header. The NON_PARAGRAPH_WORDS set
        catches the scope terminators that share the shape - CONTINUE.,
        END-EXEC., EXIT.
        """
        if self._is_skippable(line):
            return False

        body = self._body(line)
        if not body:
            return False

        # Area A: a header starts at body position 0.
        if body[:1].isspace():
            return False

        name = body.strip()
        if not name.endswith(SENTENCE_TERMINATOR):
            return False
        if " " in name:
            return False

        name = name[: -len(SENTENCE_TERMINATOR)].upper()
        if not name or name in NON_PARAGRAPH_WORDS:
            return False

        return name[0].isalnum()

    def _is_separator(self, line: str) -> bool:
        """Blank, comment or page eject - already separates."""
        text = str(line or "")

        if not text.strip():
            return True
        if not self._body(text).strip():
            return True

        indicator = text[INDICATOR_COLUMN] if len(text) > INDICATOR_COLUMN else " "
        return indicator in SEPARATOR_INDICATORS

    def _is_skippable(self, line: str) -> bool:
        text = str(line or "")

        if not text.strip():
            return True
        if not self.fixed_format.is_fixed_line(text):
            return True

        indicator = text[INDICATOR_COLUMN] if len(text) > INDICATOR_COLUMN else " "
        return indicator in SKIPPABLE_INDICATORS

    @staticmethod
    def _track_sql(line: str, in_sql: bool) -> bool:
        upper = str(line or "").upper()

        if SQL_BLOCK_START in upper:
            return True
        if in_sql and SQL_BLOCK_END in upper:
            return False

        return in_sql

    #
    # Fixed-format helpers
    #
    def _body(self, line: str) -> str:
        try:
            _left, _indicator, body, _right = self.fixed_format.split(line)
        except Exception:  # noqa: BLE001
            return ""
        return str(body or "").rstrip()

    def _clone(self, template: str, body: str) -> str | None:
        try:
            left, _indicator, _old, right = self.fixed_format.split(template)
        except Exception:  # noqa: BLE001
            return None
        return self.fixed_format.build_or_none(
            left, BLANK_INDICATOR, body, right
        )

    @staticmethod
    def _last_populated(output: list[str]) -> str | None:
        for line in reversed(output):
            if str(line or "").strip():
                return line
        return None


__all__ = ["StatementLayoutComposer"]
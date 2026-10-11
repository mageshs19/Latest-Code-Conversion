# LOCATION: converter/composers/restart/legacy_restart_cleanup.py
# ACTION: CREATE NEW FILE
"""Removes legacy restart residue so the family can be regenerated.

THREE JOBS

    detect()              is there a restart mechanism already?
    remove_paragraphs()   drop the restart-family paragraphs
    remove_declarations() drop unreferenced legacy working storage

WHY REMOVAL COMES FIRST

Regeneration appends. Without removal a second conversion run leaves two
700-RESTART-CONTROL paragraphs, and COBOL resolves a PERFORM to the
first one - so the newly generated logic would be declared and never
reached. Removing before writing makes the whole pipeline idempotent.

WHY A DECLARATION SURVIVES A REFERENCE

The generated program kept SW-RECAB, CTR-REC and STOP01 from the IDMS
original. They are legacy, but a declaration the PROCEDURE DIVISION
still reads is load-bearing whatever its origin: deleting it turns a
tidy-up into a compile error. Each one is removed only when nothing
references it, and the decision is reported either way.

WHY A LONG PARAGRAPH IS LEFT ALONE

The paragraph boundary is the next header. If an upstream pass has
damaged the headers, that test loses sync and the span runs to end of
source. A span longer than the limit is refused rather than deleted.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Regex lives in patterns/restart_patterns.py,
constants in rules/restart_cleanup_rules.py.
"""

from __future__ import annotations

from converter.generators.restart.restart_config import RestartConfig
from patterns.restart_patterns import (
    LEVEL_77_HEADER_PATTERN,
    LEVEL_77_WITH_VALUE_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    VALUE_LINE_PATTERN,
)
from rules.restart_cleanup_rules import (
    CLEANUP_MESSAGES,
    DIVISION_SUFFIX,
    LEGACY_ABEND_MARKER_PREFIX,
    LEGACY_DECLARATION_NAMES,
    LEGACY_RESTART_DETECTION_TOKENS,
    NON_PARAGRAPH_DOTTED_LINES,
    PARAGRAPH_SPAN_LIMIT,
    SECTION_SUFFIX,
    VALUE_CONTINUATION_SCAN_LIMIT,
)
from rules.restart_standard_rules import RESTART_PARAGRAPH_ROLES


class LegacyRestartCleanup:
    """Detects and removes the previous restart mechanism."""

    def __init__(self, config: RestartConfig, line_utils) -> None:
        self.config = config
        self.line_utils = line_utils
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def clean(self, lines: list[str]) -> list[str]:
        """Remove the restart family and unreferenced legacy storage."""
        self.messages = []
        body = self.remove_paragraphs(list(lines or []), reset=False)
        return self.remove_declarations(body, reset=False)

    def detect(self, lines: list[str]) -> bool:
        """True when any legacy restart token is present."""
        text = " ".join(self._logical(line) for line in lines or [])
        found = [
            token
            for token in LEGACY_RESTART_DETECTION_TOKENS
            if token in text
        ]
        for token in found:
            self._log("legacy_detected", token=token)
        if not found:
            self._log("legacy_absent")
        return bool(found)

    # -----------------------------------------------------------------
    # Paragraphs
    # -----------------------------------------------------------------

    def remove_paragraphs(
        self,
        lines: list[str],
        reset: bool = True,
    ) -> list[str]:
        if reset:
            self.messages = []

        body = list(lines or [])
        for role in RESTART_PARAGRAPH_ROLES:
            body = self._remove_one(body, self.config.paragraph(role))
        return body

    def _remove_one(self, lines: list[str], paragraph: str) -> list[str]:
        start = self._header_index(lines, paragraph)
        if start < 0:
            self._log("paragraph_absent", paragraph=paragraph)
            return lines

        end = self._span_end(lines, start)
        if end - start > PARAGRAPH_SPAN_LIMIT:
            self._log(
                "paragraph_too_long",
                paragraph=paragraph,
                limit=PARAGRAPH_SPAN_LIMIT,
            )
            return lines

        self._log(
            "paragraph_removed", paragraph=paragraph, count=end - start
        )
        return lines[:start] + lines[end:]

    def _header_index(self, lines: list[str], paragraph: str) -> int:
        wanted = paragraph.upper()
        for index, line in enumerate(lines):
            if self._header_name(self._logical(line)) == wanted:
                return index
        return -1

    def _span_end(self, lines: list[str], start: int) -> int:
        for index in range(start + 1, len(lines)):
            logical = self._logical(lines[index])
            if not logical:
                continue
            if self._header_name(logical):
                return index
            if logical.endswith((SECTION_SUFFIX, DIVISION_SUFFIX)):
                return index
        return len(lines)

    # -----------------------------------------------------------------
    # Declarations
    # -----------------------------------------------------------------

    def remove_declarations(
        self,
        lines: list[str],
        reset: bool = True,
    ) -> list[str]:
        if reset:
            self.messages = []

        body = list(lines or [])
        split = self._procedure_index(body)
        if split >= len(body):
            self._log("no_procedure_division")
            return body

        referenced = " ".join(self._logical(l) for l in body[split:])
        out: list[str] = []
        index = 0

        while index < len(body):
            if index >= split:
                out.extend(body[index:])
                break

            span = self._legacy_span(body, index, referenced)
            if span is None:
                out.append(body[index])
                index += 1
                continue
            index = span

        return out

    def _legacy_span(
        self,
        lines: list[str],
        start: int,
        referenced: str,
    ) -> int | None:
        logical = self._logical(lines[start])

        inline = LEVEL_77_WITH_VALUE_PATTERN.match(logical)
        if inline:
            return self._decide(
                inline.group("name"), inline.group("value"), referenced,
                start + 1,
            )

        header = LEVEL_77_HEADER_PATTERN.match(logical)
        if not header:
            return None

        limit = min(len(lines), start + 1 + VALUE_CONTINUATION_SCAN_LIMIT)
        for cursor in range(start + 1, limit):
            following = self._logical(lines[cursor])
            if not following:
                continue
            value = VALUE_LINE_PATTERN.match(following)
            if not value:
                return None
            return self._decide(
                header.group("name"), value.group("value"), referenced,
                cursor + 1,
            )
        return None

    def _decide(
        self,
        name: str,
        value: str,
        referenced: str,
        span_end: int,
    ) -> int | None:
        upper = name.upper()
        is_marker = str(value or "").startswith(LEGACY_ABEND_MARKER_PREFIX)
        is_legacy = upper in LEGACY_DECLARATION_NAMES

        if not is_marker and not is_legacy:
            return None

        if upper in referenced:
            self._log("declaration_referenced", name=name)
            return None

        self._log(
            "marker_removed" if is_marker else "declaration_removed",
            name=name,
        )
        return span_end

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _procedure_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if PROCEDURE_DIVISION_PATTERN.match(self._logical(line)):
                return index
        return len(lines)

    def _logical(self, line: str) -> str:
        text = str(self.line_utils.logical(line) or "")
        if self.line_utils.is_comment(text):
            return ""
        return " ".join(text.upper().split())

    def _header_name(self, logical: str) -> str:
        """Paragraph name when the line is a header, else an empty string.

        CONTINUE. and the scope terminators match the header SHAPE. They
        are not headers, and treating them as one ends every span after
        a single line.
        """
        if logical in NON_PARAGRAPH_DOTTED_LINES:
            return ""
        match = PARAGRAPH_HEADER_PATTERN.match(logical)
        return match.group("name").upper() if match else ""

    def _log(self, key: str, **values) -> None:
        template = CLEANUP_MESSAGES.get(key, "")
        if template:
            self.messages.append(template.format(**values))


__all__ = ["LegacyRestartCleanup"]
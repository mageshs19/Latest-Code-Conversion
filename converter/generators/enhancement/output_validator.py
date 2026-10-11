from __future__ import annotations

from typing import Dict, List

from converter.generators.initialization.cursor_scope_scanner import (
    CursorScopeScanner,
)
from converter.generators.initialization.diagnostics import (
    InitializationDiagnostics,
)
from converter.generators.initialization.initialize_placer import (
    InitializePlacer,
)
from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import (
    ParagraphIndex,
)
from patterns.initialization_scope_patterns import (
    CURSOR_PARAGRAPH_HEADER_PATTERN,
    INITIALIZE_PATTERN,
    PERFORM_PARAGRAPH_PATTERN,
)
from rules.initialization_placement_rules import (
    DCLGEN_GROUP_PREFIX,
    STARTUP_PARAGRAPH_NAME,
    TIMESTAMP_PARAGRAPH_NAME,
)

NO_GROUP_INITIALIZED = (
    "No DCLGEN group is initialized anywhere in the program"
)
MISSING_SCOPED_INITIALIZE = (
    "Cursor {cursor} opens without INITIALIZE {group} in the same scope"
)
UNRESOLVED_CURSOR = (
    "Cursor {cursor} has no resolvable DCLGEN group"
)
INITIALIZE_IN_CURSOR_PARAGRAPH = (
    "INITIALIZE found inside generated cursor paragraph {paragraph}"
)
LEGACY_PARAGRAPH_PRESENT = (
    "{paragraph} is still present; initialization is cursor scoped"
)
MISSING_TIMESTAMP = "Missing {paragraph} paragraph"
DUPLICATE_TIMESTAMP = "{paragraph} is performed {count} times"


class OutputValidator:

    def __init__(self) -> None:
        self.geometry = LineGeometry()
        self.paragraphs = ParagraphIndex(self.geometry)
        self.scanner = CursorScopeScanner(self.geometry, self.paragraphs)
        self.placer = InitializePlacer(
            InitializationDiagnostics(), self.geometry
        )

    def validate(self, program_text: str) -> Dict[str, object]:
        result: Dict[str, object] = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
        }
        lines = self.geometry.split(str(program_text or ""))
        if not lines:
            return result

        self._check_groups(lines, result)
        self._check_scope(lines, result)
        self._check_cursor_paragraphs(lines, result)
        self._check_legacy(lines, result)
        self._check_timestamp(lines, result)
        return result

    def _check_groups(self, lines: List[str], result: Dict) -> None:
        if self._initialized_groups(lines):
            return
        result["issues"].append(NO_GROUP_INITIALIZED)
        result["is_valid"] = False

    def _check_scope(self, lines: List[str], result: Dict) -> None:
        for site in self.scanner.open_sites(lines):
            if not site.is_resolved:
                result["warnings"].append(
                    UNRESOLVED_CURSOR.format(cursor=site.cursor)
                )
                continue
            if self.placer.already_placed(lines, site):
                continue
            result["issues"].append(
                MISSING_SCOPED_INITIALIZE.format(
                    cursor=site.cursor,
                    group=site.group,
                )
            )
            result["is_valid"] = False

    def _check_cursor_paragraphs(
        self,
        lines: List[str],
        result: Dict,
    ) -> None:
        for index, line in enumerate(lines):
            if not self.paragraphs.is_paragraph_header(line):
                continue
            body = self.geometry.body(line)
            if not CURSOR_PARAGRAPH_HEADER_PATTERN.match(body):
                continue
            start, end = self.paragraphs.span_of(lines, index)
            if self._has_group_initialize(lines, start, end):
                result["warnings"].append(
                    INITIALIZE_IN_CURSOR_PARAGRAPH.format(
                        paragraph=body.rstrip(".")
                    )
                )

    def _check_legacy(self, lines: List[str], result: Dict) -> None:
        if self.paragraphs.header_index(lines, STARTUP_PARAGRAPH_NAME) < 0:
            return
        result["warnings"].append(
            LEGACY_PARAGRAPH_PRESENT.format(
                paragraph=STARTUP_PARAGRAPH_NAME
            )
        )

    def _check_timestamp(self, lines: List[str], result: Dict) -> None:
        if self.paragraphs.header_index(lines, TIMESTAMP_PARAGRAPH_NAME) < 0:
            result["warnings"].append(
                MISSING_TIMESTAMP.format(paragraph=TIMESTAMP_PARAGRAPH_NAME)
            )
            return
        count = self._perform_count(lines, TIMESTAMP_PARAGRAPH_NAME)
        if count > 1:
            result["warnings"].append(
                DUPLICATE_TIMESTAMP.format(
                    paragraph=TIMESTAMP_PARAGRAPH_NAME,
                    count=count,
                )
            )

    def _initialized_groups(self, lines: List[str]) -> List[str]:
        out: List[str] = []
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            match = INITIALIZE_PATTERN.match(self.geometry.body(line))
            if not match:
                continue
            group = match.group("group").upper()
            if group.startswith(DCLGEN_GROUP_PREFIX):
                out.append(group)
        return out

    def _has_group_initialize(
        self,
        lines: List[str],
        start: int,
        end: int,
    ) -> bool:
        for index in range(start + 1, end + 1):
            if self.geometry.is_comment_or_blank(lines[index]):
                continue
            match = INITIALIZE_PATTERN.match(self.geometry.body(lines[index]))
            if match and match.group("group").upper().startswith(
                DCLGEN_GROUP_PREFIX
            ):
                return True
        return False

    def _perform_count(self, lines: List[str], name: str) -> int:
        target = str(name or "").upper()
        count = 0
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            match = PERFORM_PARAGRAPH_PATTERN.match(self.geometry.body(line))
            if match and match.group("paragraph").upper() == target:
                count += 1
        return count


def validate_output(program_text: str) -> Dict[str, object]:
    return OutputValidator().validate(program_text)


__all__ = ["OutputValidator", "validate_output"]
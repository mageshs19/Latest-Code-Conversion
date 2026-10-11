from __future__ import annotations

from typing import List, Set, Tuple

from converter.generators.initialization.diagnostics import (
    InitializationDiagnostics,
)
from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import (
    ParagraphIndex,
)
from patterns.initialization_scope_patterns import (
    INITIALIZE_PATTERN,
    PERFORM_PARAGRAPH_PATTERN,
)
from rules.initialization_placement_rules import (
    SALVAGE_LEGACY_STARTUP_STATEMENTS,
    STARTUP_PARAGRAPH_NAME,
    STATEMENT_TERMINATOR,
)


class LegacyParagraphRemover:

    def __init__(
        self,
        diagnostics: InitializationDiagnostics,
        geometry: LineGeometry | None = None,
        paragraphs: ParagraphIndex | None = None,
    ) -> None:
        self.diagnostics = diagnostics
        self.geometry = geometry or LineGeometry()
        self.paragraphs = paragraphs or ParagraphIndex(self.geometry)

    def remove(self, lines: List[str]) -> List[str]:
        span = self.paragraphs.span_named(lines, STARTUP_PARAGRAPH_NAME)
        performs = self._perform_indexes(lines)
        if span[0] < 0 and not performs:
            return list(lines)

        salvage = self._salvage(lines, span)
        known = self._mainline_keys(lines)
        output: List[str] = []
        emitted = False

        for index, line in enumerate(lines):
            if self._inside(span, index):
                continue
            if index in performs:
                if not emitted:
                    output.extend(
                        self._render(line, salvage, known)
                    )
                    emitted = True
                else:
                    self.diagnostics.log(
                        "removed_startup_perform",
                        paragraph=STARTUP_PARAGRAPH_NAME,
                    )
                continue
            output.append(line)

        if span[0] >= 0:
            self.diagnostics.log(
                "removed_startup_paragraph",
                paragraph=STARTUP_PARAGRAPH_NAME,
            )
        if performs:
            self.diagnostics.log(
                "removed_startup_perform",
                paragraph=STARTUP_PARAGRAPH_NAME,
            )
        return output

    def _perform_indexes(self, lines: List[str]) -> Set[int]:
        target = STARTUP_PARAGRAPH_NAME.upper()
        found: Set[int] = set()
        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            match = PERFORM_PARAGRAPH_PATTERN.match(self.geometry.body(line))
            if match and match.group("paragraph").upper() == target:
                found.add(index)
        return found

    def _salvage(
        self,
        lines: List[str],
        span: Tuple[int, int],
    ) -> List[str]:
        if not SALVAGE_LEGACY_STARTUP_STATEMENTS or span[0] < 0:
            return []
        out: List[str] = []
        for index in range(span[0] + 1, span[1] + 1):
            line = lines[index]
            if self.geometry.is_comment_or_blank(line):
                continue
            body = self.geometry.body(line)
            if INITIALIZE_PATTERN.match(body):
                continue
            out.append(body.rstrip().rstrip(STATEMENT_TERMINATOR).strip())
        return out

    def _mainline_keys(self, lines: List[str]) -> Set[str]:
        start, end = self.paragraphs.mainline_span(lines)
        if start < 0:
            return set()
        keys: Set[str] = set()
        for index in range(start + 1, end + 1):
            if self.geometry.is_comment_or_blank(lines[index]):
                continue
            keys.add(self._key(self.geometry.body(lines[index])))
        return keys

    def _render(
        self,
        template: str,
        salvage: List[str],
        known: Set[str],
    ) -> List[str]:
        indent = self.geometry.indent_of(template)
        out: List[str] = []
        seen: Set[str] = set()
        for body in salvage:
            key = self._key(body)
            if not key or key in known or key in seen:
                self.diagnostics.log("dropped_duplicate", statement=body)
                continue
            seen.add(key)
            out.append(self.geometry.statement(body, indent))
            self.diagnostics.log(
                "salvaged_statement",
                statement=body,
                paragraph=STARTUP_PARAGRAPH_NAME,
            )
        return out

    @staticmethod
    def _inside(span: Tuple[int, int], index: int) -> bool:
        return span[0] >= 0 and span[0] <= index <= span[1]

    @staticmethod
    def _key(body: str) -> str:
        text = str(body or "").upper().rstrip().rstrip(STATEMENT_TERMINATOR)
        return " ".join(text.split())


__all__ = ["LegacyParagraphRemover"]
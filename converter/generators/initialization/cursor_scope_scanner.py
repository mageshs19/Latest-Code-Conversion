from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import (
    MAINLINE_NAME,
    ParagraphIndex,
)
from patterns.initialization_scope_patterns import (
    DCLGEN_INCLUDE_PATTERN,
    DCLGEN_REFERENCE_PATTERN,
    FETCH_PARAGRAPH_HEADER_PATTERN,
    HOST_GROUP_PATTERN,
    PERFORM_OPEN_CURSOR_PATTERN,
)
from rules.initialization_placement_rules import (
    DCLGEN_GROUP_PREFIX,
    SCOPE_ROW,
    SCOPE_RUN,
)


@dataclass(frozen=True)
class CursorOpenSite:
    index: int
    cursor: str
    group: str
    indent: str
    owner: str
    scope: str

    @property
    def is_resolved(self) -> bool:
        return bool(self.cursor) and bool(self.group)


class CursorScopeScanner:

    def __init__(
        self,
        geometry: LineGeometry | None = None,
        paragraphs: ParagraphIndex | None = None,
    ) -> None:
        self.geometry = geometry or LineGeometry()
        self.paragraphs = paragraphs or ParagraphIndex(self.geometry)

    def dclgen_groups(self, lines: List[str]) -> Set[str]:
        found: Set[str] = set()
        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                continue
            body = self.geometry.body(line)
            for pattern in (
                DCLGEN_INCLUDE_PATTERN,
                DCLGEN_REFERENCE_PATTERN,
            ):
                for match in pattern.finditer(body):
                    found.add(match.group("group").upper())
        return {
            group for group in found
            if group.startswith(DCLGEN_GROUP_PREFIX)
        }

    def fetch_group_map(self, lines: List[str]) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for index, line in enumerate(lines):
            if not self.paragraphs.is_paragraph_header(line):
                continue
            header = FETCH_PARAGRAPH_HEADER_PATTERN.match(
                self.geometry.body(line)
            )
            if not header:
                continue
            cursor = header.group("cursor").upper()
            if cursor in mapping:
                continue
            group = self._group_in_span(lines, index)
            if group:
                mapping[cursor] = group
        return mapping

    def open_sites(self, lines: List[str]) -> List[CursorOpenSite]:
        groups = self.fetch_group_map(lines)
        sites: List[CursorOpenSite] = []
        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            match = PERFORM_OPEN_CURSOR_PATTERN.match(
                self.geometry.body(line)
            )
            if not match:
                continue
            cursor = match.group("cursor").upper()
            owner = self.paragraphs.owner_of(lines, index)
            sites.append(
                CursorOpenSite(
                    index=index,
                    cursor=cursor,
                    group=groups.get(cursor, ""),
                    indent=self.geometry.indent_of(line),
                    owner=owner,
                    scope=(
                        SCOPE_RUN
                        if owner == MAINLINE_NAME
                        else SCOPE_ROW
                    ),
                )
            )
        return sites

    def resolved_sites(self, lines: List[str]) -> List[CursorOpenSite]:
        return [site for site in self.open_sites(lines) if site.is_resolved]

    def unresolved_cursors(self, lines: List[str]) -> List[str]:
        return [
            site.cursor
            for site in self.open_sites(lines)
            if not site.is_resolved
        ]

    def scoped_groups(self, lines: List[str], scope: str) -> Set[str]:
        return {
            site.group
            for site in self.resolved_sites(lines)
            if site.scope == str(scope or "").upper()
        }

    def _group_in_span(self, lines: List[str], start: int) -> str:
        span_start, span_end = self.paragraphs.span_of(lines, start)
        if span_start < 0:
            return ""
        for index in range(span_start + 1, span_end + 1):
            if self.geometry.is_comment_or_blank(lines[index]):
                continue
            match = HOST_GROUP_PATTERN.search(self.geometry.body(lines[index]))
            if match:
                return match.group("group").upper()
        return ""


__all__ = ["CursorOpenSite", "CursorScopeScanner"]
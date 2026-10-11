from __future__ import annotations

from typing import List

from converter.generators.initialization.cursor_scope_scanner import (
    CursorOpenSite,
)
from converter.generators.initialization.diagnostics import (
    InitializationDiagnostics,
)
from converter.generators.initialization.line_geometry import LineGeometry
from patterns.initialization_scope_patterns import INITIALIZE_PATTERN
from rules.initialization_placement_rules import (
    EMIT_INITIALIZE_PERIOD,
    INITIALIZE_TEMPLATE,
    SCOPE_RUN,
    STATEMENT_TERMINATOR,
)


class InitializePlacer:

    def __init__(
        self,
        diagnostics: InitializationDiagnostics,
        geometry: LineGeometry | None = None,
    ) -> None:
        self.diagnostics = diagnostics
        self.geometry = geometry or LineGeometry()

    def place(
        self,
        lines: List[str],
        sites: List[CursorOpenSite],
    ) -> List[str]:
        output = list(lines)
        for site in sorted(sites, key=lambda item: item.index, reverse=True):
            if not site.is_resolved:
                continue
            if self.already_placed(output, site):
                self.diagnostics.log(
                    "already_placed",
                    group=site.group,
                    paragraph=self.geometry.body(output[site.index]),
                )
                continue
            output.insert(site.index, self._statement(site))
            self._report(site, output)
        return output

    def already_placed(
        self,
        lines: List[str],
        site: CursorOpenSite,
    ) -> bool:
        position = self._previous_executable(lines, site.index)
        if position < 0:
            return False
        match = INITIALIZE_PATTERN.match(self.geometry.body(lines[position]))
        if not match:
            return False
        return match.group("group").upper() == site.group

    def verify(
        self,
        lines: List[str],
        sites: List[CursorOpenSite],
    ) -> List[str]:
        return [
            site.group
            for site in sites
            if site.is_resolved and not self.already_placed(lines, site)
        ]

    def _statement(self, site: CursorOpenSite) -> str:
        body = INITIALIZE_TEMPLATE.format(group=site.group)
        if EMIT_INITIALIZE_PERIOD:
            body = f"{body}{STATEMENT_TERMINATOR}"
        return self.geometry.statement(body, site.indent)

    def _report(self, site: CursorOpenSite, lines: List[str]) -> None:
        paragraph = self.geometry.body(lines[site.index + 1])
        if site.scope == SCOPE_RUN:
            self.diagnostics.log(
                "placed_run_scope",
                group=site.group,
                paragraph=paragraph,
            )
            return
        self.diagnostics.log(
            "placed_row_scope",
            group=site.group,
            scope=site.owner,
            paragraph=paragraph,
        )

    def _previous_executable(self, lines: List[str], index: int) -> int:
        for position in range(index - 1, -1, -1):
            if not self.geometry.is_comment_or_blank(lines[position]):
                return position
        return -1


__all__ = ["InitializePlacer"]
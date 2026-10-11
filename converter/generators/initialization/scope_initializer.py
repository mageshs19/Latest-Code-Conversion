from __future__ import annotations

from typing import List, Set

from converter.generators.initialization.cursor_scope_scanner import (
    CursorScopeScanner,
)
from converter.generators.initialization.diagnostics import (
    InitializationDiagnostics,
)
from converter.generators.initialization.initialize_placer import (
    InitializePlacer,
)
from converter.generators.initialization.initialize_remover import (
    InitializeRemover,
)
from converter.generators.initialization.legacy_paragraph_remover import (
    LegacyParagraphRemover,
)
from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import (
    ParagraphIndex,
)
from rules.initialization_placement_rules import (
    ENFORCE_CURSOR_SCOPED_INITIALIZATION,
    REMOVE_LEGACY_STARTUP_PARAGRAPH,
    SCOPE_ROW,
    SCOPE_RUN,
)


class CursorScopedInitializer:

    def __init__(self, program_text: str) -> None:
        self.program_text = program_text
        self.dclgen_groups: Set[str] = set()
        self.diagnostics = InitializationDiagnostics()
        self.geometry = LineGeometry()
        self.paragraphs = ParagraphIndex(self.geometry)
        self.scanner = CursorScopeScanner(self.geometry, self.paragraphs)
        self.remover = InitializeRemover(self.geometry)
        self.legacy = LegacyParagraphRemover(
            self.diagnostics, self.geometry, self.paragraphs
        )
        self.placer = InitializePlacer(self.diagnostics, self.geometry)

    @property
    def messages(self) -> List[str]:
        return self.diagnostics.all()

    def process(self) -> str:
        text = str(self.program_text or "")
        if not text.strip() or not ENFORCE_CURSOR_SCOPED_INITIALIZATION:
            return text

        self.diagnostics.reset()
        lines = self.geometry.split(text)

        self.dclgen_groups = self.scanner.dclgen_groups(lines)
        if not self.dclgen_groups:
            self.diagnostics.log("no_groups")
            return text

        if self.paragraphs.procedure_division_index(lines) < 0:
            self.diagnostics.log("no_procedure_division")
            return text

        sites = self.scanner.open_sites(lines)
        if not sites:
            self.diagnostics.log("no_cursor_open")
            return text

        for cursor in self.scanner.unresolved_cursors(lines):
            self.diagnostics.log("group_unresolved", cursor=cursor)

        working = list(lines)
        if REMOVE_LEGACY_STARTUP_PARAGRAPH:
            working = self.legacy.remove(working)

        working, removed = self.remover.remove(working, self.dclgen_groups)
        if removed:
            self.diagnostics.log("removed_statements", count=removed)

        placed = self.scanner.resolved_sites(working)
        if not placed:
            self.diagnostics.log(
                "rolled_back",
                reason="no cursor OPEN resolved a DCLGEN group",
            )
            return text

        working = self.placer.place(working, placed)

        verified = self.scanner.resolved_sites(working)
        missing = self.placer.verify(working, verified)
        if missing:
            self.diagnostics.log(
                "rolled_back",
                reason=f"INITIALIZE missing for {', '.join(sorted(missing))}",
            )
            return text

        self.diagnostics.log(
            "summary",
            run=len(self.scanner.scoped_groups(working, SCOPE_RUN)),
            row=len(self.scanner.scoped_groups(working, SCOPE_ROW)),
        )
        return self.geometry.join(working)


def initialize_by_cursor_scope(program_text: str) -> str:
    return CursorScopedInitializer(program_text).process()


__all__ = ["CursorScopedInitializer", "initialize_by_cursor_scope"]
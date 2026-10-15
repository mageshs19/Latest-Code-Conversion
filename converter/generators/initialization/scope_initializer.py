# LOCATION: converter/generators/initialization/scope_initializer.py
# ACTION: REPLACE ENTIRE FILE
"""Places INITIALIZE <DCLGEN group> at the right scope.

TWO ANCHORS, ONE PLACER

    cursor site       the group a PERFORM <nnn>-OPEN-<cursor> will fill
    population site   the paragraph that fills the group by MOVE

CORRECTION 1 - the pass knew only the first anchor

    sites = self.scanner.open_sites(lines)
    if not sites:
        self.diagnostics.log("no_cursor_open")
        return text

VMDZ1567 is an update program driven by a flat file through singleton
SQL. It has ZERO cursors and 18 references to DCLDZBFARTV, populated
field by field at the top of VERWERKING. With no cursor OPEN the whole
pass stood down, the group was never cleared, and every field the
paragraph does not write carried the previous row's value into the next
UPDATE.

Site composition now asks both scanners. A group a cursor already owns
keeps the cursor anchor - that is the manual reference shape and the
existing tests assert it - so the two can never both clear one group.

CORRECTION 2 - the summary denied the work the log had just announced

    run=len(self.scanner.scoped_groups(working, SCOPE_RUN)),
    row=len(self.scanner.scoped_groups(working, SCOPE_ROW)),

CursorScopeScanner.scoped_groups counts CURSOR sites only, so a program
placed through a population site reported:

    Initialization: placed INITIALIZE DCLDZBFARTV in VERWERKING ...
    Initialization: scoped 0 run-level and 0 row-level DCLGEN group(s).

A report that contradicts itself is worse than no report. _scoped_groups
counts across both anchors.

CORRECTION 3 - the population scanner was rebuilt on every call

_initialization_sites runs three times per program (plan, place,
verify). Constructing a scanner inside it created three objects where
one is needed, and - worse - three chances for them to be built with
different collaborators. It is built once, in __init__, from the SAME
geometry and paragraph index every other collaborator uses, so there is
exactly one interpretation of a logical line in this package.

No program, paragraph, record, table, DCLGEN group or host variable name
is hardcoded. Regex lives in patterns/, constants in rules/.
"""

from __future__ import annotations

from typing import List, Sequence, Set

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
from converter.generators.initialization.population_site_scanner import (
    PopulationSiteScanner,
)
from rules.initialization_placement_rules import (
    ENFORCE_CURSOR_SCOPED_INITIALIZATION,
    REMOVE_LEGACY_STARTUP_PARAGRAPH,
    SCOPE_ROW,
    SCOPE_RUN,
)


class CursorScopedInitializer:
    """Clears every DCLGEN group once per unit of work, or refuses.

    The name is historical: placement is no longer cursor-only. It is
    kept because enhancement_pipeline.py, the package __init__ and
    initialization_centralizer.py all import it, and a rename that
    touches four call sites for no behavioural gain is churn. The
    docstring, not the class name, is the contract.
    """

    def __init__(self, program_text: str) -> None:
        self.program_text = program_text
        self.dclgen_groups: Set[str] = set()
        self.diagnostics = InitializationDiagnostics()
        self.geometry = LineGeometry()
        self.paragraphs = ParagraphIndex(self.geometry)
        self.scanner = CursorScopeScanner(self.geometry, self.paragraphs)
        self.population = PopulationSiteScanner(
            self.geometry,
            self.paragraphs,
        )
        self.remover = InitializeRemover(self.geometry)
        self.legacy = LegacyParagraphRemover(
            self.diagnostics, self.geometry, self.paragraphs
        )
        self.placer = InitializePlacer(self.diagnostics, self.geometry)

    @property
    def messages(self) -> List[str]:
        return self.diagnostics.all()

    # ------------------------------------------------------------------ #
    # Public entry point
    # ------------------------------------------------------------------ #
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

        sites = self._initialization_sites(lines)
        if not sites:
            # Both anchors came back empty. Name which one was absent,
            # so a skipped program is never mistaken for one that
            # needed nothing.
            if not self.scanner.open_sites(lines):
                self.diagnostics.log("no_cursor_open")
            self.diagnostics.log(
                "rolled_back",
                reason="no cursor OPEN and no DCLGEN population site",
            )
            return text

        for cursor in self.scanner.unresolved_cursors(lines):
            self.diagnostics.log("group_unresolved", cursor=cursor)

        working = list(lines)
        if REMOVE_LEGACY_STARTUP_PARAGRAPH:
            working = self.legacy.remove(working)

        working, removed = self.remover.remove(working, self.dclgen_groups)
        if removed:
            self.diagnostics.log("removed_statements", count=removed)

        # Re-measured after removal: a statement the remover took out
        # must not still count as a resolved site.
        placed = self._initialization_sites(working)
        if not placed:
            self.diagnostics.log(
                "rolled_back",
                reason="no site resolved a DCLGEN group",
            )
            return text

        working = self.placer.place(working, placed)

        # Verify by TEXT, not by re-scanning for sites. After placement
        # the INITIALIZE is itself the paragraph's first executable
        # line, so a re-scan resolves nothing and both the check and the
        # summary silently reported zero.
        missing = self._unplaced_groups(working, placed)
        if missing:
            self.diagnostics.log(
                "rolled_back",
                reason=f"INITIALIZE missing for {', '.join(missing)}",
            )
            return text

        self.diagnostics.log(
            "summary",
            run=len(self._groups_at(placed, SCOPE_RUN)),
            row=len(self._groups_at(placed, SCOPE_ROW)),
        )
        return self.geometry.join(working)

    # ------------------------------------------------------------------ #
    # Site composition
    # ------------------------------------------------------------------ #
    def _initialization_sites(self, lines: Sequence[str]) -> List[object]:
        """Cursor sites first, then population sites for the rest.

        Order is load-bearing. A group owned by a cursor OPEN keeps the
        cursor anchor, because that is the manual reference shape the
        existing contract tests assert. Population sites cover only the
        groups the cursor pass cannot see, so one group can never
        receive two INITIALIZE statements.
        """
        source = list(lines)

        cursor_sites = self.scanner.resolved_sites(source)
        owned = {site.group for site in cursor_sites if site.group}

        population_sites = self.population.sites(
            source,
            exclude_groups=owned,
        )

        return list(cursor_sites) + list(population_sites)

    @staticmethod
    def _groups_at(sites, scope) -> Set[str]:
        target = str(scope or "").upper()
        return {
            site.group
            for site in sites
            if site.is_resolved and str(site.scope or "").upper() == target
        }

    def _unplaced_groups(self, lines, sites) -> List[str]:
        """Groups that were planned but do not appear in the output."""
        text = self.geometry.logical_text(lines)
        return sorted({
            site.group
            for site in sites
            if site.is_resolved and f"INITIALIZE {site.group}" not in text
        })

def initialize_by_cursor_scope(program_text: str) -> str:
    return CursorScopedInitializer(program_text).process()


__all__ = ["CursorScopedInitializer", "initialize_by_cursor_scope"]
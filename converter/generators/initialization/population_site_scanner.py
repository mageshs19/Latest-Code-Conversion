# LOCATION: converter/generators/initialization/population_site_scanner.py
# ACTION: CREATE NEW FILE
"""Finds the paragraph that POPULATES a DCLGEN group.

WHY THIS FILE EXISTS

CursorScopeScanner resolves placement sites from ONE anchor: a
PERFORM <nnn>-OPEN-<cursor>. That is correct for a cursor program and
blind to every other shape.

VMDZ1567 is an update program driven by a flat file through singleton
SQL. It has ZERO cursors, 18 references to DCLDZBFARTV, and populates
that group field by field at the top of VERWERKING:

    VERWERKING.
        MOVE '1815' TO CT-TGDSERV-479BFAR OF DCLDZBFARTV
        MOVE NR-CIO-FORM-AS-R TO NR-CIOFMAS-479BFAR OF DCLDZBFARTV
        ...

With no cursor OPEN, scope_initializer logged no_cursor_open and
returned the text unchanged, so the group was never cleared and every
field the paragraph does not write carried the previous row's value
into the next UPDATE.

WHAT THIS SCANNER ADDS

A second site type: the FIRST line of a paragraph that writes into a
DCLGEN group. INITIALIZE belongs immediately above that line, inside
the paragraph, so the group is cleared once per row.

WHY A SEPARATE DATACLASS

CursorOpenSite.is_resolved reads

    bool(self.cursor) and bool(self.group)

A population site has no cursor, so reusing that type would make every
site unresolved and InitializePlacer would skip it. InitializationSite
resolves on the GROUP alone, which is the only fact placement needs.
The placer is duck-typed and takes it unchanged.

SCOPE

Population sites are always ROW scope. The paragraph is the per-record
unit of work; clearing once per run would reintroduce the defect for
every record after the first.

No program, paragraph, record, table, DCLGEN group or host variable
name is hardcoded. Regex is imported from patterns/, constants from
rules/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import ParagraphIndex
from patterns.initialization_scope_patterns import HOST_GROUP_PATTERN
from rules.initialization_placement_rules import (
    DCLGEN_GROUP_PREFIX,
    SCOPE_ROW,
)
from patterns.initialization_scope_patterns import COBOL_HOST_GROUP_PATTERN

NO_CURSOR = ""


@dataclass
class InitializationSite:
    """A place where a DCLGEN group must be cleared.

    Structurally compatible with CursorOpenSite so InitializePlacer
    accepts it unchanged. `cursor` is carried only for that
    compatibility and is always empty for a population site.
    """

    index: int
    group: str
    indent: str
    owner: str
    scope: str = SCOPE_ROW
    cursor: str = NO_CURSOR

    @property
    def is_resolved(self) -> bool:
        """Resolution is the GROUP. A population site has no cursor."""
        return bool(self.group)


class PopulationSiteScanner:
    """Locates the first DCLGEN write in every paragraph."""

    def __init__(
        self,
        geometry: Optional[LineGeometry] = None,
        paragraphs: Optional[ParagraphIndex] = None,
    ) -> None:
        self.geometry = geometry or LineGeometry()
        self.paragraphs = paragraphs or ParagraphIndex(self.geometry)

    # ------------------------------------------------------------------ #
    # Public surface
    # ------------------------------------------------------------------ #
    def sites(
        self,
        lines: List[str],
        exclude_groups: Optional[Iterable[str]] = None,
    ) -> List[InitializationSite]:
        """One site per (paragraph, group), at the first write.

        `exclude_groups` carries the groups a cursor site already owns,
        so a group reached by both anchors is never initialised twice.
        """
        excluded = {
            str(name or "").strip().upper()
            for name in (exclude_groups or ())
            if str(name or "").strip()
        }

        seen: Dict[Tuple[str, str], bool] = {}
        output: List[InitializationSite] = []

        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue

            group = self._group_written_on(line)
            if not group or group in excluded:
                continue

            owner = self.paragraphs.owner_of(lines, index)
            if not owner:
                # A write outside any paragraph has no per-row unit of
                # work to attach to. Refuse rather than guess a scope.
                continue

            key = (owner.upper(), group)
            if key in seen:
                continue
            seen[key] = True

            output.append(
                InitializationSite(
                    index=index,
                    group=group,
                    indent=self.geometry.indent_of(line),
                    owner=owner,
                    scope=SCOPE_ROW,
                )
            )

        return output

    def groups(self, lines: List[str]) -> Set[str]:
        return {site.group for site in self.sites(lines)}

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _group_written_on(self, line: str) -> str:
        """The DCLGEN group this line writes into, or ''."""
        match = HOST_GROUP_PATTERN.search(self.geometry.body(line))
        if not match:
            return ""
        group = str(match.group("group") or "").upper()
        if not group.startswith(DCLGEN_GROUP_PREFIX):
            return ""
        return group

    def _group_written_on(self, line: str) -> str:
        """The DCLGEN group this line writes into, or ''.

        COBOL qualification only. The SQL host form ":DCLxxx.FIELD"
        belongs to a FETCH INTO list and is owned by
        CursorScopeScanner._group_in_span - matching it here would
        anchor an INITIALIZE inside a generated FETCH paragraph.
        """
        match = COBOL_HOST_GROUP_PATTERN.search(self.geometry.body(line))
        if not match:
            return ""
        group = str(match.group("group") or "").upper()
        if not group.startswith(DCLGEN_GROUP_PREFIX):
            return ""
        return group


__all__ = ["InitializationSite", "PopulationSiteScanner"]
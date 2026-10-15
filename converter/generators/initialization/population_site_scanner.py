# LOCATION: converter/generators/initialization/population_site_scanner.py
# ACTION: REPLACE ENTIRE FILE
"""Finds the paragraph that POPULATES a DCLGEN group.

An update program driven by a flat file through singleton SQL has no
cursor OPEN, so CursorScopeScanner cannot see it and its business group
was never cleared.

FOUR REFUSALS, MEASURED AGAINST THE MANUAL REFERENCE

The manual for VMDZ1567 initialises exactly ONE group - DCLDZBFARTV, as
the first statement of 1000-VERWERKING. It never initialises
DCLDZ01RSTV. The first version of this scanner emitted four extra
INITIALIZE statements and broke the restart family three ways.

R1  THE GROUP MUST BE A MOVE TARGET

        MOVE TE-CH-RS-DATA-TEXT OF DCLDZ01RSTV TO WS-RESTART-REC

    READS the group. Matching "OF DCL..." anywhere on the line made
    710-JOB-IS-RESTART clear the checkpoint row the SELECT had just
    returned. Only the RECEIVING side of a MOVE is a write.

R2  A GROUP WRITTEN IN MORE THAN ONE PARAGRAPH IS CARRIED STATE

    DCLDZ01RSTV is written in four paragraphs and its key must survive
    from the control paragraph into the write and commit paragraphs.
    A per-row buffer is written in exactly one paragraph.

R3  THE ANCHOR IS THE PARAGRAPH'S FIRST EXECUTABLE LINE

    Not the write itself. The first version anchored on the write, so a
    write sitting inside an IF put the statement between IF and THEN -
    invalid COBOL - and a SECOND group populated later in the same
    paragraph was silently dropped. Anchoring on the first executable
    line is the only position that cannot land inside an open scope,
    and it lets two buffers in one paragraph both be cleared.

R4  A GROUP THE PARAGRAPH ALREADY CLEARS IS LEFT ALONE

    R3 makes INITIALIZE itself the first executable line, so a second
    run would otherwise stack a duplicate on every pass. The pass is
    idempotent because it refuses a group it has already placed.

No program, paragraph, record, table, DCLGEN group or host variable
name is hardcoded. Regex lives in patterns/, constants in rules/.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.initialization.paragraph_index import ParagraphIndex
from patterns.initialization_scope_patterns import COBOL_HOST_GROUP_PATTERN
from rules.initialization_placement_rules import (
    DCLGEN_GROUP_PREFIX,
    SCOPE_ROW,
)

NO_CURSOR = ""

# COBOL language vocabulary, not business names.
MOVE_VERB = "MOVE "
INITIALIZE_VERB = "INITIALIZE "
TO_KEYWORD = " TO "
QUALIFIER_OPENERS = ("OF ", "IN ")

# A qualifier follows its data-name immediately; anything further is a
# separate statement.
CONTINUATION_SCAN_LIMIT = 2


@dataclass
class InitializationSite:
    """A place where a DCLGEN group must be cleared.

    Structurally compatible with CursorOpenSite so InitializePlacer
    takes it unchanged. `cursor` exists only for that compatibility and
    is always empty: resolution is the GROUP.
    """

    index: int
    group: str
    indent: str
    owner: str
    scope: str = SCOPE_ROW
    cursor: str = NO_CURSOR

    @property
    def is_resolved(self) -> bool:
        return bool(self.group)


@dataclass
class _Write:
    index: int
    group: str
    owner: str


class PopulationSiteScanner:
    """Locates the one paragraph that fills a per-row DCLGEN buffer."""

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
        source = list(lines)
        excluded = {
            str(name or "").strip().upper()
            for name in (exclude_groups or ())
            if str(name or "").strip()
        }

        writes = self._writes(source)
        if not writes:
            return []

        owners_by_group: Dict[str, Set[str]] = {}
        for write in writes:
            owners_by_group.setdefault(write.group, set()).add(
                write.owner.upper()
            )

        already = self._already_initialised(source)
        first_executable = self._first_executable_by_paragraph(source)

        emitted: Set[str] = set()
        output: List[InitializationSite] = []

        for write in writes:
            owner_key = write.owner.upper()

            if write.group in excluded or write.group in emitted:
                continue

            # R2 - carried state is never cleared at paragraph entry.
            if len(owners_by_group[write.group]) != 1:
                continue

            # R4 - idempotence.
            if (owner_key, write.group) in already:
                continue

            # R3 - anchor on the first executable line of the paragraph.
            anchor = first_executable.get(owner_key, -1)
            if anchor < 0:
                continue

            emitted.add(write.group)
            output.append(
                InitializationSite(
                    index=anchor,
                    group=write.group,
                    indent=self.geometry.indent_of(source[anchor]),
                    owner=write.owner,
                    scope=SCOPE_ROW,
                )
            )

        return output

    def groups(self, lines: List[str]) -> Set[str]:
        return {site.group for site in self.sites(lines)}

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _writes(self, lines: List[str]) -> List[_Write]:
        output: List[_Write] = []

        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue

            group = self._receiving_group(lines, index)
            if not group:
                continue

            owner = self.paragraphs.owner_of(lines, index)
            if not owner:
                continue

            output.append(_Write(index=index, group=group, owner=owner))

        return output

    def _already_initialised(
        self,
        lines: List[str],
    ) -> Set[Tuple[str, str]]:
        found: Set[Tuple[str, str]] = set()

        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue

            body = self._body(line)
            if not body.startswith(INITIALIZE_VERB):
                continue

            group = self._dclgen_group(body[len(INITIALIZE_VERB):])
            if not group:
                continue

            owner = self.paragraphs.owner_of(lines, index)
            if owner:
                found.add((owner.upper(), group))

        return found

    def _receiving_group(self, lines: List[str], index: int) -> str:
        """The DCLGEN group this MOVE writes INTO, or ''."""
        body = self._body(lines[index])
        if not body.startswith(MOVE_VERB):
            return ""

        cut = body.rfind(TO_KEYWORD)
        if cut < 0:
            return ""

        group = self._dclgen_group(body[cut + len(TO_KEYWORD):])
        if group:
            return group

        # Wrapped form:  MOVE <source> TO <field>
        #                  OF <group>
        return self._continuation_group(lines, index)

    def _continuation_group(self, lines: List[str], index: int) -> str:
        scanned = 0
        position = index + 1

        while position < len(lines) and scanned < CONTINUATION_SCAN_LIMIT:
            if self.geometry.is_comment_or_blank(lines[position]):
                position += 1
                continue

            scanned += 1
            tail = self._body(lines[position])
            if not tail.startswith(QUALIFIER_OPENERS):
                return ""
            return self._dclgen_group(tail)

        return ""

    def _dclgen_group(self, text: str) -> str:
        match = COBOL_HOST_GROUP_PATTERN.search(str(text or ""))
        if not match:
            # An unqualified INITIALIZE names the group directly.
            token = str(text or "").strip().rstrip(".").split(" ")[0]
            group = token.upper()
        else:
            group = str(match.group("group") or "").upper()

        if not group.startswith(DCLGEN_GROUP_PREFIX):
            return ""
        return group

    def _first_executable_by_paragraph(
        self,
        lines: List[str],
    ) -> Dict[str, int]:
        first: Dict[str, int] = {}

        for index, line in enumerate(lines):
            if self.geometry.is_comment_or_blank(line):
                continue
            if self.paragraphs.is_paragraph_header(line):
                continue

            owner = self.paragraphs.owner_of(lines, index)
            if not owner:
                continue

            key = owner.upper()
            if key not in first:
                first[key] = index

        return first

    def _body(self, line: str) -> str:
        return " ".join(self.geometry.body(line).upper().split())


__all__ = ["InitializationSite", "PopulationSiteScanner"]
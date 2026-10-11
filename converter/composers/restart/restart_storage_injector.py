# LOCATION: converter/composers/restart/restart_storage_injector.py
# ACTION: REPLACE ENTIRE FILE

"""Places the generated restart working storage into the program.

    inject(lines) -> list[str]

RENDER AND PLACE ARE SEPARATE

RestartStorageBuilder decides WHAT the groups say; this composer decides
WHERE they go. Keeping them apart is why the builder can be tested
against measurements alone, with no COBOL text to position.

DECLARE WHAT THE FAMILY WILL REFERENCE

Two things must exist before the generated restart paragraphs compile:

    the working-storage groups      01 WS-SWITCHES / HELP-VARIABLE / ...
    the restart DCLGEN include      EXEC SQL INCLUDE DZ01RSTV END-EXEC.

CORRECTION 1 - the include was never emitted

The generated SQL moves through the host group:

    INTO :DCLDZ01RSTV.NM-ID-RS-PROGRAM
       , :DCLDZ01RSTV.NB-ID-RS-PHASE

but nothing declared DCLDZ01RSTV. Measured on VMDZ1526 and VMDZ1567:

    700-SELECT-DZ01RSTV : 2      <- the paragraph exists
    INCLUDE DZ01RSTV    : 0      <- the host group does not

The pass that adds a missing DCLGEN include runs in the CONTENT phase
("Cleanup: added missing DCLGEN include DZBEFFTV"); restart injection
runs in the FINISHING phase. By the time the DCLDZ01RSTV references
exist, the pass that would have noticed them has already finished. The
same ordering shape as every other defect in this family: a step that
reacts to an artefact produced after it.

The owner of a reference declares it. This composer emits the include
beside the storage it already places.

CORRECTION 2 - "already declared" was a GROUP-level judgement

A program arriving with

    01  HELP-VARIABLE.
        02  WS-SOMETHING-ELSE      PIC X.

was reported "already declared" and left alone - but RestartNameResolver
had by then SUPPLIED WS-TELLER, WS-RESTART-REC and the rest on the
promise that this composer would declare them. The generated family
then moved to fields that do not exist, which is the defect the legacy
generator shipped as

    ADD 1 TO WS-COMMIT-COUNTER     <- never declared

The judgement is now per FIELD. An existing group keeps its own members
and receives only the subordinates it is missing, appended at the end of
that group. A subtree is added whole - a parent and its children travel
together, so a 02 is never added without its 03s and never duplicated
because one 03 happened to exist.

WORKING-STORAGE ONLY, NEVER FILE SECTION

The legacy path injected 01 groups with VALUE clauses under the FD,
which is illegal and hid the FD's real record behind three impostors.
A new group goes immediately after the WORKING-STORAGE SECTION header
and nowhere else; no header, no insertion, and the refusal is reported.

IDEMPOTENT

A second run finds every group present and every member declared, and
inserts nothing. Insertions are applied from the highest index down, so
one placement cannot invalidate the index of another.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Group names come from the catalog, lines from the
builder, the include member from the resolved role.
"""

from __future__ import annotations

from catalogs.output_sections import INCLUDE_STATEMENT_TEMPLATE
from catalogs.restart_storage_catalog import (
    DATE_GROUP,
    HELP_GROUP,
    SWITCH_GROUP,
)
from converter.composers.restart.restart_line_utils import RestartLineUtils
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_storage_builder import (
    RestartStorageBuilder,
)

WORKING_STORAGE_TOKEN = "WORKING-STORAGE SECTION"
GROUP_LEVEL = "01"

# Levels that END an 01 group: another record, a standalone item, or a
# new section / division.
GROUP_TERMINATOR_LEVELS = ("01", "77")
GROUP_TERMINATOR_TOKENS = (
    "WORKING-STORAGE",
    "LOCAL-STORAGE",
    "LINKAGE",
    "FILE SECTION",
    "PROCEDURE DIVISION",
)

# Group -> the builder method that renders it, and the resolved name
# that proves the layout already exists under some other group.
# Order is declaration order in the generated program.
GROUP_SOURCES = (
    (SWITCH_GROUP, "switch_group", "eof_condition"),
    (HELP_GROUP, "help_group", "restart_record"),
    (DATE_GROUP, "date_group", "run_date_field"),
)

# Where the restart DCLGEN member name lives on the role. Attribute
# NAMES are schema; the VALUES are site vocabulary.
INCLUDE_NAME_ATTRIBUTES = ("include_name", "table_name")

# Columns 8-72. Four spaces puts EXEC at column 12, Area B.
INCLUDE_INDENT = "    "

MESSAGE_PREFIX = "Restart storage:"


class RestartStorageInjector:
    """Inserts the restart storage and its include, once, in the right
    section."""

    def __init__(self, config: RestartConfig, line_utils=None) -> None:
        self.config = config
        self.line_utils = line_utils or RestartLineUtils()
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------
    def inject(self, lines: list[str]) -> list[str]:
        """Return the program with any MISSING storage or include added."""
        self.messages = []
        body = list(lines or [])

        builder = RestartStorageBuilder(self.config)
        if not builder.build():
            self.messages.extend(builder.messages)
            self._say("nothing to place; the builder emitted no storage.")
            return body

        anchor = self._working_storage_index(body)
        if anchor < 0:
            self._say(
                f"no {WORKING_STORAGE_TOKEN} found; the storage was NOT "
                "placed. It must never go under an FD."
            )
            return body

        plan: list[tuple[int, list[str]]] = []
        plan.extend(self._plan_include(body, anchor))
        plan.extend(self._plan_groups(body, builder, anchor))

        if not plan:
            self._say("everything is already declared; nothing inserted.")
            return body

        return self._apply(body, plan)

    # -----------------------------------------------------------------
    # The restart DCLGEN include  -  CORRECTION 1
    # -----------------------------------------------------------------
    def _plan_include(
        self,
        lines: list[str],
        anchor: int,
    ) -> list[tuple[int, list[str]]]:
        member = self._include_member()
        if not member:
            self._say(
                "the role carries no DCLGEN member name; the restart "
                "include was not emitted."
            )
            return []

        if self._declares_include(lines, member):
            self._say(f"{member} is already included; not added again.")
            return []

        statement = INCLUDE_STATEMENT_TEMPLATE.format(name=member)
        self._say(f"{member} was not included; declared it.")
        return [(anchor + 1, [f"{INCLUDE_INDENT}{statement}"])]

    def _include_member(self) -> str:
        role = getattr(self.config, "role", None)
        for attribute in INCLUDE_NAME_ATTRIBUTES:
            value = str(getattr(role, attribute, "") or "").strip().upper()
            if value:
                return value
        return ""

    def _declares_include(self, lines: list[str], member: str) -> bool:
        wanted = f"EXEC SQL INCLUDE {member.upper()} "
        for line in lines:
            logical = self._logical(line)
            if logical.startswith(wanted) or logical == wanted.rstrip():
                return True
            if logical.startswith(f"EXEC SQL INCLUDE {member.upper()}"):
                return True
        return False

    # -----------------------------------------------------------------
    # The storage groups  -  CORRECTION 2
    # -----------------------------------------------------------------
    def _plan_groups(
        self,
        lines: list[str],
        builder: RestartStorageBuilder,
        anchor: int,
    ) -> list[tuple[int, list[str]]]:
        declared_groups = self._declared_groups(lines)
        declared_names = self._declared_names(lines)
        plan: list[tuple[int, list[str]]] = []

        for group, source, anchor_field in GROUP_SOURCES:
            rendered = [
                line for line in getattr(builder, source)() if str(line).strip()
            ]
            if not rendered:
                continue

            if group in declared_groups:
                missing = self._missing_subtrees(rendered, declared_names)
                if not missing:
                    self._say(
                        f"{group} is already declared and complete; "
                        "left unchanged."
                    )
                    continue

                end = self._group_end_index(lines, group)
                if end < 0:
                    self._say(
                        f"{group} exists but its extent could not be "
                        "measured; no member was appended."
                    )
                    continue

                plan.append((end, missing))
                self._say(
                    f"{group} was missing "
                    f"{len(self._subtree_names(missing))} member(s); "
                    "appended them."
                )
                continue

            field = str(
                getattr(self.config.names, anchor_field, "") or ""
            ).upper()
            if field and field in declared_names:
                self._say(
                    f"{field} is already declared; {group} not added. "
                    "The layout exists under another group name."
                )
                continue

            plan.append((anchor + 1, [""] + rendered))
            self._say(f"{group} was absent; declared it.")

        return plan

    # -----------------------------------------------------------------
    # Subtrees: a parent and its children travel together
    # -----------------------------------------------------------------
    def _missing_subtrees(
        self,
        rendered: list[str],
        declared_names: set[str],
    ) -> list[str]:
        """Rendered members whose head name is not already declared."""
        out: list[str] = []
        for name, block in self._subtrees(rendered):
            if name in declared_names:
                continue
            out.extend(block)
        return out

    def _subtrees(self, rendered: list[str]) -> list[tuple[str, list[str]]]:
        """Split a rendered group into its top-level subordinates.

        The child level is read from the first line after the 01 header,
        so a group using 02 and a group using 03 both split correctly.
        """
        body = rendered[1:] if self._level_of(rendered[0]) == GROUP_LEVEL else list(rendered)
        if not body:
            return []

        child_level = ""
        for line in body:
            level = self._level_of(line)
            if level:
                child_level = level
                break
        if not child_level:
            return []

        subtrees: list[tuple[str, list[str]]] = []
        current: list[str] = []
        current_name = ""

        for line in body:
            if self._level_of(line) == child_level:
                if current:
                    subtrees.append((current_name, current))
                current = [line]
                current_name = self._name_of(line)
                continue
            if current:
                current.append(line)

        if current:
            subtrees.append((current_name, current))
        return subtrees

    def _subtree_names(self, block: list[str]) -> list[str]:
        return [name for name, _lines in self._subtrees([""] + block) if name]

    # -----------------------------------------------------------------
    # Placement
    # -----------------------------------------------------------------
    def _working_storage_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if self._logical(line).startswith(WORKING_STORAGE_TOKEN):
                return index
        return -1

    def _group_end_index(self, lines: list[str], group: str) -> int:
        """Index just past the last line of `group`.

        The group ends at the next 01 / 77 entry or the next section or
        division header, whichever comes first.
        """
        start = -1
        wanted = group.upper()
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if (
                self._level_of(logical) == GROUP_LEVEL
                and self._name_of(logical) == wanted
            ):
                start = index
                break
        if start < 0:
            return -1

        for index in range(start + 1, len(lines)):
            logical = self._logical(lines[index])
            if not logical:
                continue
            if self._level_of(logical) in GROUP_TERMINATOR_LEVELS:
                return index
            if logical.startswith(GROUP_TERMINATOR_TOKENS):
                return index
        return len(lines)

    @staticmethod
    def _apply(
        lines: list[str],
        plan: list[tuple[int, list[str]]],
    ) -> list[str]:
        """Apply insertions highest index first, so none invalidates
        another.

        Ties are broken by PLAN POSITION, descending, so blocks planned
        for the same anchor emerge in the order they were planned.
        Without that, the include and all three groups share the
        WORKING-STORAGE anchor and came out reversed:

            WS-DATE-CONVERSION / HELP-VARIABLE / WS-SWITCHES / include

        Legal COBOL, but not the declaration order this module claims.
        """
        out = list(lines)
        ordered = sorted(
            enumerate(plan),
            key=lambda pair: (pair[1][0], pair[0]),
            reverse=True,
        )
        for _position, (index, block) in ordered:
            safe = max(0, min(index, len(out)))
            out = out[:safe] + list(block) + out[safe:]
        return out
    
    # -----------------------------------------------------------------
    # Declarations already present
    # -----------------------------------------------------------------
    def _declared_names(self, lines: list[str]) -> set[str]:
        """Every data name the program declares, at any level."""
        found: set[str] = set()
        for line in lines:
            name = self._name_of(self._logical(line))
            if name:
                found.add(name)
        return found

    def _declared_groups(self, lines: list[str]) -> set[str]:
        """Every 01-level group name the program already declares."""
        found: set[str] = set()
        for line in lines:
            logical = self._logical(line)
            if self._level_of(logical) != GROUP_LEVEL:
                continue
            name = self._name_of(logical)
            if name:
                found.add(name)
        return found

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------
    def _logical(self, line: str) -> str:
        body = str(self.line_utils.logical(line) or "")
        if self.line_utils.is_comment(body):
            return ""
        return " ".join(body.upper().split())

    def _level_of(self, text: str) -> str:
        """The level number of a data description line, or ""."""
        logical = text if text.isupper() else self._logical(text)
        parts = logical.split()
        if len(parts) >= 2 and parts[0].isdigit():
            return parts[0]
        return ""

    def _name_of(self, text: str) -> str:
        """The data name of a data description line, or ""."""
        logical = text if text.isupper() else self._logical(text)
        parts = logical.split()
        if len(parts) >= 2 and parts[0].isdigit():
            return parts[1].rstrip(".").upper()
        return ""

    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")


__all__ = [
    "GROUP_SOURCES",
    "INCLUDE_NAME_ATTRIBUTES",
    "RestartStorageInjector",
    "WORKING_STORAGE_TOKEN",
]
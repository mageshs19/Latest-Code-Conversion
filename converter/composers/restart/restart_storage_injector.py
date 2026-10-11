# LOCATION: converter/composers/restart/restart_storage_injector.py
# ACTION: CREATE NEW FILE
"""Places the generated restart working storage into the program.

    inject(lines) -> list[str]

RENDER AND PLACE ARE SEPARATE

RestartStorageBuilder decides WHAT the groups say; this composer decides
WHERE they go. Keeping them apart is why the builder can be tested
against measurements alone, with no COBOL text to position.

ONLY WHAT IS MISSING

A group already declared in the program is LEFT ALONE and reported. The
legacy generator declares the same three groups, so an unconditional
insertion would duplicate every data name in them - the exact failure
the duplicate DZ01RSTV include produced.

WORKING-STORAGE ONLY, NEVER FILE SECTION

The legacy path injected 01 groups with VALUE clauses under the FD,
which is illegal and hid the FD's real record behind three impostors.
The insertion point here is the WORKING-STORAGE SECTION header and
nothing else; no header, no insertion, and the refusal is reported.

IDEMPOTENT

A second run finds all three groups present and inserts nothing.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Group names come from the catalog, lines from the
builder.
"""

from __future__ import annotations

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

# Group -> the builder method that renders it. Order is declaration
# order in the generated program.
GROUP_SOURCES = (
    (SWITCH_GROUP, "switch_group", "eof_condition"),
    (HELP_GROUP, "help_group", "restart_record"),
    (DATE_GROUP, "date_group", "run_date_field"),
)
MESSAGE_PREFIX = "Restart storage:"


class RestartStorageInjector:
    """Inserts the restart working storage, once, in the right section."""

    def __init__(self, config: RestartConfig, line_utils=None) -> None:
        self.config = config
        self.line_utils = line_utils or RestartLineUtils()
        self.messages: list[str] = []

    #
    # Public surface
    #
    def inject(self, lines: list[str]) -> list[str]:
        """Return the program with any MISSING storage group added."""
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

        rendered = self._missing_groups(body, builder)
        if not rendered:
            self._say(
                "every group is already declared; nothing inserted."
            )
            return body

        return body[: anchor + 1] + rendered + body[anchor + 1 :]

    #
    # Which groups are absent
    #
    def _missing_groups(
        self,
        lines: list[str],
        builder: RestartStorageBuilder,
    ) -> list[str]:
        declared = self._declared_groups(lines)
        names = self._declared_names(lines)
        out: list[str] = []

        for group, source, anchor in GROUP_SOURCES:
            field = str(getattr(self.config.names, anchor, "") or "").upper()

            if group in declared:
                self._say(f"{group} is already declared; left unchanged.")
                continue
            if field and field in names:
                self._say(
                    f"{field} is already declared; {group} not added. "
                    "The layout exists under another group name."
                )
                continue

            out.append("")
            out.extend(getattr(builder, source)())
            self._say(f"{group} was absent; declared it.")

        return out

    def _declared_names(self, lines: list[str]) -> set[str]:
        """Every data name the program declares, at any level."""
        found: set[str] = set()
        for line in lines:
            logical = self._logical(line)
            parts = logical.split()
            if len(parts) >= 2 and parts[0].isdigit():
                found.add(parts[1].rstrip(".").upper())
        return found

    def _declared_groups(self, lines: list[str]) -> set[str]:
        """Every 01-level group name the program already declares."""
        found: set[str] = set()
        for line in lines:
            logical = self._logical(line)
            if not logical.startswith(f"{GROUP_LEVEL} "):
                continue
            parts = logical.split()
            if len(parts) >= 2:
                found.add(parts[1].rstrip(".").upper())
        return found

    #
    # Placement
    #
    def _working_storage_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if self._logical(line).startswith(WORKING_STORAGE_TOKEN):
                return index
        return -1

    #
    # Helpers
    #
    def _logical(self, line: str) -> str:
        body = str(self.line_utils.logical(line) or "")
        if self.line_utils.is_comment(body):
            return ""
        return " ".join(body.upper().split())

    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")


__all__ = [
    "GROUP_SOURCES",
    "RestartStorageInjector",
    "WORKING_STORAGE_TOKEN",
]
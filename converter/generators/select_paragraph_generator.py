# LOCATION: converter/generators/select_paragraph_generator.py
# ACTION: REPLACE ENTIRE FILE

"""The legacy restart path, retired to a reporting role.

WHAT THIS MODULE USED TO DO
---------------------------
It generated restart working storage, the restart table include,
timestamp storage, four restart SQL paragraphs and four handler
paragraphs - for two programs named in an `if` statement:

    if program_id in ["VMDZ1526", "VMDZ1567"]:

It authored the restart table name, the host record name, six column
names, the abend module, the error paragraph and the commit counter. It
seeded a fresh run's record COUNT with the checkpoint payload LENGTH. It
referenced two fields it never declared. It spliced text by character
offset, dragging the next physical line's sequence number into the body:

    EXEC SQL INCLUDE DZ01RSTV END-EXEC.008300

And it performed 810-/820- handlers, which the metadata-driven pass then
regenerated as 710-/720-, leaving a PERFORM of a paragraph that no
longer existed.

WHY IT NO LONGER DOES ANY OF THAT
---------------------------------
Every one of those jobs is already owned, resolved and tested:

    RestartRoleResolver     table + columns from Sheet Mapping + DCLGEN
    RestartNameResolver     16 names + 2 measurements from the source
    RestartConfig.build     refuses rather than inventing
    RestartStorageBuilder   working storage
    RestartSqlBuilder       SELECT / UPDATE / INSERT
    RestartFlowBuilder      control / found / write / commit / abend
    RestartStageAdapter     runs the family for an update program

The resolver MEASURES what this module guessed. Your own run log:

    read_count_size  = 15
    restart_key_size = 1200
    Restart: checkpoint payload measured at 1215 byte(s)

1215 is the number the old builder moved into NB-READ.

WHAT IT DOES NOW
----------------
Stands down, says why, and reports any legacy residue it can see so a
dangling PERFORM is named before the compiler finds it. It authors
nothing.

PUBLIC API - unchanged, so no call site needs editing.
"""

from __future__ import annotations

from typing import Any, Optional

from patterns.sequence_patterns import (
    is_fixed_format_line,
    logical_body,
)
from rules.legacy_restart_rules import (
    ENABLE_LEGACY_RESTART_GENERATOR,
    LEGACY_HANDLER_NUMBER_PREFIXES,
    LEGACY_RESTART_MESSAGES,
    REPORT_DANGLING_PERFORM,
    REPORT_LEGACY_RESIDUE,
    STAND_DOWN_REASONS,
)

# The owner pass injects this role. Its presence proves the owner ran.
# Imported lazily by NAME so a wrong path reports itself instead of
# aborting every program in the batch.
_OWNER_ROLE_KEY = "restart_found"


class SelectParagraphGenerator:
    """Reports on legacy restart residue. Generates nothing."""

    def __init__(self, line_utils: Any = None) -> None:
        self.line_utils = line_utils
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------
    def apply(
        self,
        cobol_text: str,
        program_id: Optional[str] = None,
        operations: list | None = None,
        *,
        is_update: Optional[bool] = None,
        restart_context: Any = None,
    ) -> tuple[str, list[str]]:
        self.messages = []
        text = str(cobol_text or "")

        if not text.strip():
            self._stood_down("empty_source")
            return text, self.messages

        if ENABLE_LEGACY_RESTART_GENERATOR:
            self._say("enabled_warning")

        self._decide(text, is_update, restart_context)

        if REPORT_LEGACY_RESIDUE:
            self._report_residue(text)

        # The text is returned untouched. Always.
        return text, self.messages

    # -----------------------------------------------------------------
    # Stand-down
    # -----------------------------------------------------------------
    def _decide(
        self,
        text: str,
        is_update: Optional[bool],
        restart_context: Any,
    ) -> None:
        if restart_context is not None:
            if not self._context_is_update(restart_context):
                self._stood_down("retrieval")
                return
            self._stood_down("context_present")
            return

        owner_paragraph = self._owner_paragraph(text)
        if owner_paragraph:
            self._stood_down(
                "owner_paragraph_present", paragraph=owner_paragraph
            )
            return

        if is_update is False:
            self._stood_down("retrieval")
            return

        self._stood_down("switch_off")

    @staticmethod
    def _context_is_update(context: Any) -> bool:
        """RestartRunContext exposes is_update. Duck-typed on purpose."""
        value = getattr(context, "is_update", None)
        if value is None:
            return True
        return bool(value)

    def _owner_paragraph(self, text: str) -> str:
        """The first seven-series handler the owner pass would inject."""
        try:
            from rules.restart_standard_rules import (
                RESTART_PARAGRAPH_NAMES,
            )
        except ImportError:
            return ""

        wanted = str(
            RESTART_PARAGRAPH_NAMES.get(_OWNER_ROLE_KEY, "")
        ).strip().upper()
        if not wanted:
            return ""

        header = f"{wanted}."
        for line in self._logical_lines(text):
            if line == header:
                return wanted
        return ""

    # -----------------------------------------------------------------
    # Residue reporting
    # -----------------------------------------------------------------
    def _report_residue(self, text: str) -> None:
        lines = self._logical_lines(text)

        defined: set[str] = set()
        performed: dict[str, int] = {}

        for line in lines:
            if line.endswith(".") and " " not in line[:-1]:
                defined.add(line[:-1])
            if line.startswith("PERFORM "):
                target = line.split()[1].rstrip(".")
                performed[target] = performed.get(target, 0) + 1

        residue = [
            name
            for name in sorted(defined | set(performed))
            if name.startswith(LEGACY_HANDLER_NUMBER_PREFIXES)
        ]

        if not residue:
            self._say("no_residue")
            return

        self._say("residue_found", count=len(residue))

        if not REPORT_DANGLING_PERFORM:
            return

        for name in residue:
            if name in performed and name not in defined:
                self._say("dangling_perform", paragraph=name)

    # -----------------------------------------------------------------
    # Line helpers
    # -----------------------------------------------------------------
    @staticmethod
    def _logical_lines(text: str) -> list[str]:
        raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
        out: list[str] = []
        for line in raw.split("\n"):
            body = (
                logical_body(line)
                if is_fixed_format_line(line)
                else line.strip()
            )
            if body:
                out.append(" ".join(body.upper().split()))
        return out

    # -----------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------
    def _stood_down(self, key: str, **values: Any) -> None:
        reason = STAND_DOWN_REASONS.get(key, key)
        try:
            reason = reason.format(**values)
        except (IndexError, KeyError):
            pass
        self._say("stood_down", reason=reason)

    def _say(self, key: str, **values: Any) -> None:
        template = LEGACY_RESTART_MESSAGES.get(key, "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(template)


__all__ = ["SelectParagraphGenerator"]
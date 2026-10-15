# LOCATION: converter/postprocess/update_business_sql/update_counter_declarer.py
# ACTION: CREATE NEW FILE
"""Declares the row counter the business UPDATE increments.

WHY THIS FILE EXISTS

UpdateSqlBlockExtractor emits

    ADD 1 TO WS-NB-BFAR-UPD-I

inside the paragraph it extracts. That happens in update POST-PROCESS,
after the conversion pipeline has finished - and CounterDeclarationComposer,
the only pass that declares counters, runs inside that pipeline. Nothing
downstream declares anything, so VMDZ1567 shipped with an undefined
data-name and would not compile.

RestartStorageBuilder cannot take the field either: it has no
update_counter, and its REQUIRED_NAMES is a contract - adding an entry
would make every update program without a business write unusable.

So the pass that writes the REFERENCE writes the DECLARATION. One owner.

GEOMETRY IS CLONED, NOT RE-STATED

The new line is built from the sibling counter already present in the
help group, so the level number, name column and comment columns are
inherited. No column arithmetic lives here.

IDEMPOTENT

A field already declared is left alone and reported, so a second run
cannot stack a duplicate.
"""

from __future__ import annotations

from typing import List, Optional

from rules.update_business_sql_rules import (
    ENSURE_UPDATE_COUNTER_DECLARED,
    UPDATE_COUNTER_DIAGNOSTICS,
    UPDATE_COUNTER_PICTURE,
)
from rules.update_restart_rules import UPDATE_RESTART_WS_NAMES

PICTURE_TOKEN = "PIC"


class UpdateCounterDeclarer:
    """Places the update row counter beside the input counter."""

    def __init__(self, line_utils) -> None:
        self.line_utils = line_utils

    # ------------------------------------------------------------------ #
    # Public surface
    # ------------------------------------------------------------------ #
    def ensure(self, *, lines: List[str], diagnostics=None) -> List[str]:
        if not ENSURE_UPDATE_COUNTER_DECLARED:
            return lines

        names = UPDATE_RESTART_WS_NAMES
        counter = str(names.get("update_counter") or "").strip().upper()
        sibling = str(names.get("input_counter") or "").strip().upper()
        if not counter or not sibling:
            return lines

        if self._declared(lines, counter):
            self._say(diagnostics, "already", name=counter)
            return lines

        anchor = self._declaration_index(lines, sibling)
        if anchor < 0:
            self._say(
                diagnostics, "no_anchor", name=counter, sibling=sibling
            )
            return lines

        declaration = self._clone(lines[anchor], sibling, counter)
        self._say(diagnostics, "declared", name=counter, sibling=sibling)
        return lines[: anchor + 1] + [declaration] + lines[anchor + 1:]

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _declared(self, lines: List[str], name: str) -> bool:
        return self._declaration_index(lines, name) >= 0

    def _declaration_index(self, lines: List[str], name: str) -> int:
        """Index of `NN <name> PIC ...`, or -1.

        A DISPLAY or an ADD that mentions the name is not a declaration,
        so the PIC keyword is required.
        """
        wanted = str(name or "").strip().upper()
        if not wanted:
            return -1

        for index, line in enumerate(lines):
            body = self._logical(line).upper()
            parts = body.split()
            if len(parts) < 3:
                continue
            if not parts[0].isdigit():
                continue
            if parts[1].rstrip(".") != wanted:
                continue
            if not any(token.startswith(PICTURE_TOKEN) for token in parts[2:]):
                continue
            return index

        return -1

    def _clone(self, reference: str, sibling: str, counter: str) -> str:
        """The sibling's line, renamed and re-pictured.

        Padding the new name to the sibling's width keeps the PIC column
        where the rest of the group has it.
        """
        body = self._logical(reference)
        head, _, tail = body.partition(sibling)
        gap = len(tail) - len(tail.lstrip())
        width = max(len(sibling), len(counter))
        rendered = (
            f"{head}{counter.ljust(width)}"
            f"{' ' * max(gap, 1)}{UPDATE_COUNTER_PICTURE}"
        )
        return self._like(reference, rendered)

    def _logical(self, line: str) -> str:
        try:
            return str(self.line_utils.logical(line) or "")
        except Exception:  # noqa: BLE001 - reading must never abort
            return str(line or "")

    def _like(self, reference: str, body: str) -> str:
        """Render `body` with the reference line's fixed-format geometry."""
        for name in ("active_line_like", "line_like", "replace_body"):
            renderer = getattr(self.line_utils, name, None)
            if callable(renderer):
                try:
                    return renderer(reference_line=reference, body=body)
                except TypeError:
                    try:
                        return renderer(reference, body)
                    except Exception:  # noqa: BLE001
                        continue
                except Exception:  # noqa: BLE001
                    continue
        return body

    @staticmethod
    def _say(diagnostics, key, **values) -> None:
        if diagnostics is None:
            return
        template = UPDATE_COUNTER_DIAGNOSTICS.get(key, "")
        if not template:
            diagnostics.append(f"Update business SQL: {key} {values}")
            return
        try:
            diagnostics.append(template.format(**values))
        except (IndexError, KeyError):
            diagnostics.append(f"{template} [{key}: {values}]")


__all__ = ["UpdateCounterDeclarer"]
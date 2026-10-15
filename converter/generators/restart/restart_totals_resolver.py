# LOCATION: converter/generators/restart/restart_totals_resolver.py
# ACTION: CREATE NEW FILE
"""Builds the end-of-run DISPLAY totals for a restart mainline.

RestartMainFlowBuilder renders {totals_block} from whatever it is
handed and never authors a DISPLAY itself - deliberately, because two
authors mean two sets of totals that disagree. Nothing ever filled the
other side of that contract:

    restart_context_builder.py:103    totals=(),

a literal empty tuple. The marker line was always dropped, and no update
program with restart control could report how many records it read or
wrote.

REFERENCE-DRIVEN

A total is emitted for every WS-NB- field the PROCEDURE DIVISION
actually increments, so this resolver can never display a counter that
is never maintained, and never invent one. It reads; it does not
rewrite.
"""

from __future__ import annotations

from typing import List, Sequence

from rules.counter_rules import (
    COUNTER_ADD_TEMPLATE,
    COUNTER_DISPLAY_TEMPLATE,
    COUNTER_TOTAL_LABEL_BY_SUFFIX,
    COUNTER_TOTAL_LABEL_DEFAULT,
    COUNTER_TOTAL_MESSAGES,
    COUNTER_TOTAL_NAME_PREFIX,
)

SENTENCE_TERMINATOR = "."

# "ADD 1 TO x" and "ADD +1 TO x" are both emitted by the generators, so
# both are read. The first is derived from the one template, so a change
# to it cannot leave this module behind.
_ADD_VERBS = (
    COUNTER_ADD_TEMPLATE.split("{name}")[0].strip().upper() + " ",
    "ADD +1 TO ",
)


class RestartTotalsResolver:
    """One DISPLAY per counter the program increments."""

    def __init__(self, line_utils=None) -> None:
        self.line_utils = line_utils
        self.messages: List[str] = []

    def resolve(
        self,
        lines: Sequence[str],
        guaranteed: Sequence[str] = (),
    ) -> tuple[str, ...]:
        """Totals for every counter the program increments.

        `guaranteed` carries names the CALLER can prove will be
        incremented by a pass that has not run yet. Everything else is
        still reference-driven: a counter is never displayed because a
        table exists, only because something adds to it.

        ALWAYS returns a tuple. A None return reached
        RestartMainFlowBuilder.build(), which iterates totals directly,
        and crashed the whole conversion with
        "'NoneType' object is not iterable".
        """
        self.messages = []

        names = self._incremented_counters(lines)

        for raw in guaranteed or ():
            name = str(raw or "").strip().upper()
            if not name.startswith(COUNTER_TOTAL_NAME_PREFIX):
                continue
            if name in names:
                continue
            names.append(name)
            self._say("guaranteed", name=name)

        if not names:
            self._say("none")
            return ()

        labels = {name: self._label(name) for name in names}
        width = max(len(text) for text in labels.values())

        totals = tuple(
            self._display(name, labels[name].ljust(width)) for name in names
        )
        self._say("resolved", count=len(names), names=", ".join(names))
        return totals
    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _incremented_counters(self, lines: Sequence[str]) -> List[str]:
        found: List[str] = []

        for line in lines:
            body = self._body(line)
            for verb in _ADD_VERBS:
                if not body.startswith(verb):
                    continue
                name = body[len(verb):].strip().rstrip(SENTENCE_TERMINATOR)
                name = name.split(" ")[0].upper()
                if name.startswith(COUNTER_TOTAL_NAME_PREFIX) and name not in found:
                    found.append(name)
                break

        return found

    def _label(self, name: str) -> str:
        for suffix in sorted(COUNTER_TOTAL_LABEL_BY_SUFFIX, key=len, reverse=True):
            if not name.endswith(suffix):
                continue
            token = name[len(COUNTER_TOTAL_NAME_PREFIX): -len(suffix)]
            return COUNTER_TOTAL_LABEL_BY_SUFFIX[suffix].format(token=token)

        return COUNTER_TOTAL_LABEL_DEFAULT.format(
            token=name[len(COUNTER_TOTAL_NAME_PREFIX):]
        )

    def _display(self, name: str, label: str) -> str:
        line = COUNTER_DISPLAY_TEMPLATE.format(label=label, name=name)
        if not line.rstrip().endswith(SENTENCE_TERMINATOR):
            line = f"{line}{SENTENCE_TERMINATOR}"
        return line

    def _body(self, line: str) -> str:
        if self.line_utils is not None:
            try:
                raw = self.line_utils.logical(line)
            except Exception:  # noqa: BLE001
                raw = str(line or "")
        else:
            raw = self._fixed_body(line)
        return " ".join(str(raw or "").upper().split())

    @staticmethod
    def _fixed_body(line: str) -> str:
        text = str(line or "").rstrip("\r\n")
        if len(text) >= 72 and text[:6].strip().isdigit():
            return text[7:72]
        return text

    def _say(self, key: str, **values: object) -> None:
        template = COUNTER_TOTAL_MESSAGES.get(key, "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(template)


__all__ = ["RestartTotalsResolver"]
# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_diagnostics.py
# ACTION: CREATE NEW FILE
"""Collects the declaration decisions of one program.

Every refusal, every stand-down and every success is recorded here. A
silent decision is how an unguarded builder reached production and
stayed invisible across several runs.
"""

from __future__ import annotations

from rules.cursor_declaration_rules import DECLARATION_MESSAGES


class DeclareDiagnostics:
    """One message list, one render path."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def reset(self) -> None:
        """Drop the previous program's messages.

        One builder instance renders every cursor of every program in a
        folder run, so an uncleared list carries program 1's report
        into program 2.
        """
        self.messages = []

    def log(self, key: str, **fields) -> None:
        """Render and record one catalogued diagnostic."""
        text = self.render(key, **fields)
        if text:
            self.messages.append(text)

    def add(self, text: str) -> None:
        """Record an already-rendered message."""
        if text:
            self.messages.append(text)

    @staticmethod
    def render(key: str, **fields) -> str:
        """One catalogued diagnostic, or "".

        A key the catalogue does not carry yields "" rather than
        KeyError: a missing diagnostic must never abort a conversion.
        tools/rules_probe.py reports the gap instead.
        """
        template = DECLARATION_MESSAGES.get(key, "")
        if not template:
            return ""
        try:
            return template.format(**fields)
        except (KeyError, IndexError):
            return ""


__all__ = ["DeclareDiagnostics"]
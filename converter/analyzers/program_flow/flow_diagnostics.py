# LOCATION: converter/analyzers/program_flow/flow_diagnostics.py
# ACTION: CREATE NEW FILE
"""Assembles the analyzer's diagnostic report.

Every string comes from rules/program_flow_rules.py. A key the
catalogue does not carry yields nothing rather than KeyError: a missing
diagnostic must never abort an analysis.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import CursorLoop
from rules.program_flow_rules import FLOW_MESSAGES, LOOP_SAMPLE_LIMIT


class FlowDiagnostics:
    """Collects analyzer messages in report order."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def add(self, key: str, **values) -> None:
        template = FLOW_MESSAGES.get(key, "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (KeyError, IndexError):
            return

    def extend(self, messages: list[str] | None) -> None:
        for message in messages or []:
            if message:
                self.messages.append(message)

    def counts(self, **named_counts: int) -> None:
        """One count line per key, in the order given."""
        for key, count in named_counts.items():
            self.add(key, count=count)

    def loop_samples(self, loops: list[CursorLoop]) -> None:
        for loop in (loops or [])[:LOOP_SAMPLE_LIMIT]:
            self.add(
                "loop_sample",
                record=loop.record_name,
                set_name=loop.set_name,
                loop_type=loop.loop_type,
                cursor=loop.cursor_name,
            )

    def drain(self) -> list[str]:
        output = list(self.messages)
        self.messages = []
        return output


__all__ = ["FlowDiagnostics"]
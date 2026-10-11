from __future__ import annotations

from typing import List

from rules.initialization_placement_rules import (
    INITIALIZATION_PLACEMENT_MESSAGES,
)


class InitializationDiagnostics:

    def __init__(self) -> None:
        self.messages: List[str] = []

    def reset(self) -> None:
        self.messages = []

    def log(self, key: str, **values: object) -> None:
        template = INITIALIZATION_PLACEMENT_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(f"{template} [{key}: {values}]")

    def extend(self, other: "InitializationDiagnostics") -> None:
        if other is None:
            return
        self.messages.extend(other.messages)

    def all(self) -> List[str]:
        return list(self.messages)


__all__ = ["InitializationDiagnostics"]
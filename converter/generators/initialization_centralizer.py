from __future__ import annotations

from typing import List, Set

from converter.generators.initialization.scope_initializer import (
    CursorScopedInitializer,
)


class InitializationCentralizer:

    def __init__(self, program_text: str) -> None:
        self._delegate = CursorScopedInitializer(program_text)

    @property
    def program_text(self) -> str:
        return self._delegate.program_text

    @property
    def dclgen_groups(self) -> Set[str]:
        return self._delegate.dclgen_groups

    @property
    def messages(self) -> List[str]:
        return self._delegate.messages

    def process(self) -> str:
        return self._delegate.process()


def centralize_initialization(program_text: str) -> str:
    return InitializationCentralizer(program_text).process()


__all__ = ["InitializationCentralizer", "centralize_initialization"]
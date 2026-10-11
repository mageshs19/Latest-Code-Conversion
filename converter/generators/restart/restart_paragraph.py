# LOCATION: converter/generators/restart/restart_paragraph.py
# ACTION: CREATE NEW FILE
"""The value object every restart builder returns.

WHY IT MOVED HERE

M4 declared this class privately. M5 produces paragraphs of exactly the
same shape, and the geometry renderer consumes ONE type. Two identical
dataclasses in two modules is drift waiting to happen: the day one of
them gains a field, the renderer silently handles half the paragraphs.

M4 re-exports the old name, so every existing import keeps working.

GEOMETRY IS NOT OURS

`body` carries logical lines with meaningful RELATIVE indent. The
absolute Area B offset and the column 7 debug indicator are applied by
the shared renderer the retrieval path already uses, so both program
kinds share one geometry owner.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

from dataclasses import dataclass

from rules.restart_sql_templates import PARAGRAPH_HEADER


@dataclass(frozen=True)
class RestartParagraph:
    """One generated paragraph, ready for the geometry renderer."""

    role: str
    name: str
    debug_trace: str
    body: tuple[str, ...]

    def lines(self) -> tuple[str, ...]:
        """Header plus body. The trace carries its own indicator."""
        return (PARAGRAPH_HEADER.format(paragraph=self.name), *self.body)

    def executable(self) -> tuple[str, ...]:
        """Body lines with blanks removed and indent stripped."""
        return tuple(line.strip() for line in self.body if line.strip())


__all__ = ["RestartParagraph"]
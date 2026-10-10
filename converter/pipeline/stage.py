"""The pipeline contract.

ONE shape for every conversion step, so ordering is data and diagnostics
are uniform.

CORRECTION - diagnostics were collected by introspection
    conversion_service used

        messages = getattr(component, "messages", [])
        if callable(messages): messages = messages()

    because no two passes agreed on how to report. Every Stage now returns
    its notes in the Document, so that guesswork is gone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol


@dataclass
class Document:
    """What flows through the pipeline. One program, one instance."""

    cobol: str
    program_id: str = ""
    metadata: dict = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)

    def replace(self, cobol: str, notes: list[str] | None = None) -> "Document":
        return Document(
            cobol=cobol,
            program_id=self.program_id,
            metadata=self.metadata,
            messages=self.messages + [str(n) for n in (notes or []) if str(n).strip()],
        )


class Stage(Protocol):
    name: str
    description: str
    enabled: bool

    def run(self, doc: Document) -> Document: ...


@dataclass
class FunctionStage:
    """A stage backed by a plain function: (str) -> (str, list[str])."""

    name: str
    description: str
    fn: Callable[[str], tuple[str, list[str]]]
    enabled: bool = True

    def run(self, doc: Document) -> Document:
        text, notes = self.fn(doc.cobol)
        return doc.replace(text, notes)


def composer_stage(
    name: str,
    description: str,
    factory: Callable[[], object],
    method: str = "compose",
    enabled: bool = True,
) -> FunctionStage:
    """Adapt an EXISTING composer into a Stage. No composer changes needed.

    Works with any object exposing:
        .compose(text) -> text        (or another method name)
        .messages      -> list[str]   (optional)
    """

    def _run(text: str) -> tuple[str, list[str]]:
        obj = factory()
        out = getattr(obj, method)(text)
        notes = getattr(obj, "messages", []) or []
        if callable(notes):
            notes = notes()
        return out, list(notes)

    return FunctionStage(name=name, description=description, fn=_run, enabled=enabled)


__all__ = ["Document", "Stage", "FunctionStage", "composer_stage"]
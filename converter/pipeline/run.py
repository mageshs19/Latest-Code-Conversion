"""Runs the registry. Twelve lines that never need to change again."""

from __future__ import annotations

from converter.pipeline.registry import PIPELINE
from converter.pipeline.stage import Document


def run_pipeline(doc: Document, pipeline=PIPELINE) -> Document:
    for stage in pipeline:
        if not getattr(stage, "enabled", True):
            doc.messages.append(f"[skip] {stage.name}: disabled")
            continue
        try:
            doc = stage.run(doc)
        except Exception as exc:  # noqa: BLE001
            doc.messages.append(f"[error] {stage.name}: {type(exc).__name__}: {exc}")
    return doc


__all__ = ["run_pipeline"]
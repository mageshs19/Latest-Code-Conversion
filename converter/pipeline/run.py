"""Runs the registry.

TWO ENTRY POINTS, for the two phases of migration.

  run_stage(name, doc)   PHASE A - one named stage.
                         Each existing call site keeps its exact position
                         in the sequence while the registry owns the
                         stage DEFINITION. Use this while migrating.

  run_pipeline(doc)      PHASE B - every enabled stage, in registry order.
                         Use this once all passes are migrated and the
                         wrapper methods are collapsed. The registry then
                         owns the ORDER too.

CORRECTION - disabled stages were noisy
    A `[skip]` note was appended for every disabled stage, so a parked
    pass added a line to EVERY program's validation report. Skips are
    silent unless verbose=True.
"""

from __future__ import annotations

from converter.pipeline.registry import PIPELINE
from converter.pipeline.stage import Document


def run_stage(name: str, doc: Document, pipeline=PIPELINE) -> Document:
    """Run exactly ONE registered stage, by name.

    A disabled stage is a no-op. An unknown name is reported rather than
    silently ignored, so a typo in a call site cannot drop a pass.
    """
    for stage in pipeline:
        if stage.name != name:
            continue
        if not getattr(stage, "enabled", True):
            return doc
        try:
            return stage.run(doc)
        except Exception as exc:  # noqa: BLE001
            doc.messages.append(f"[error] {name}: {type(exc).__name__}: {exc}")
            return doc

    doc.messages.append(f"[error] unknown pipeline stage: {name}")
    return doc


def run_pipeline(doc: Document, pipeline=PIPELINE, verbose: bool = False) -> Document:
    """Run every enabled stage in registry order.

    A stage that raises is reported and skipped; the pipeline continues,
    so one broken pass cannot abort a conversion.
    """
    for stage in pipeline:
        if not getattr(stage, "enabled", True):
            if verbose:
                doc.messages.append(f"[skip] {stage.name}: disabled")
            continue
        try:
            doc = stage.run(doc)
        except Exception as exc:  # noqa: BLE001
            doc.messages.append(f"[error] {stage.name}: {type(exc).__name__}: {exc}")
    return doc


__all__ = ["run_stage", "run_pipeline"]
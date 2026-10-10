"""Runs the registry.

Twelve lines that should never need to change again.

CORRECTION - disabled stages were noisy
    A `[skip]` note was appended for every disabled stage, so a parked
    pass added a line to EVERY program's validation report. Skips are
    now silent by default and only reported when verbose=True, which
    tools/pipeline_doc.py already shows statically.
"""

from __future__ import annotations

from converter.pipeline.registry import PIPELINE
from converter.pipeline.stage import Document


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


__all__ = ["run_pipeline"]
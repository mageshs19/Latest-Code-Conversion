# LOCATION: converter/analyzers/program_flow_analyzer.py
# ACTION: REPLACE ENTIRE FILE
"""Backward-compatible import point.

converter/pipeline/conversion/conversion_pipeline.py does

    from converter.analyzers.program_flow_analyzer import ProgramFlowAnalyzer

The implementation lives in
converter/analyzers/program_flow/program_flow_analyzer.py; this module
keeps the old path valid so the package split needs no call-site edits.
Delete this file only once every importer has been repointed.

This module DECLARES NOTHING. It re-exports and nothing else, so it
cannot change analyzer behaviour.

CORRECTION - this module imported the PACKAGE

    from converter.analyzers.program_flow import (
        CursorLoop,
        ...
    )

A stale or partially updated program_flow/__init__.py therefore broke
the entire conversion pipeline at import time:

    ImportError: cannot import name 'CursorLoop' from
    'converter.analyzers.program_flow'

Concrete module imports, not the package. The shim can then no longer
be taken down by the package's export surface, which is the same policy
already applied to converter/composers/output_write.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import (  # noqa: F401
    CursorLoop,
    DateUsage,
    LogicalLine,
    OutputWrite,
    ParagraphSpan,
    ProgramFlowAnalysis,
)
from converter.analyzers.program_flow.program_flow_analyzer import (  # noqa: F401
    ProgramFlowAnalyzer,
)

__all__ = [
    "CursorLoop",
    "DateUsage",
    "LogicalLine",
    "OutputWrite",
    "ParagraphSpan",
    "ProgramFlowAnalyzer",
    "ProgramFlowAnalysis",
]
# LOCATION: converter/analyzers/program_flow_analyzer.py
# ACTION: REPLACE ENTIRE FILE
"""Backward-compatible import point.

converter/pipeline/ imports ProgramFlowAnalyzer from HERE. The
implementation moved into converter/analyzers/program_flow/; this
module keeps the old path valid so the split needs no call-site edits.

Delete this file only once every importer has been repointed.
"""

from converter.analyzers.program_flow import (  # noqa: F401
    CursorLoop,
    DateUsage,
    OutputWrite,
    ParagraphSpan,
    ProgramFlowAnalysis,
    ProgramFlowAnalyzer,
)

__all__ = [
    "ProgramFlowAnalyzer", "ProgramFlowAnalysis", "ParagraphSpan",
    "CursorLoop", "OutputWrite", "DateUsage",
]
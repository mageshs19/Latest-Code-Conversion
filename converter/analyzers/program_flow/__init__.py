# LOCATION: converter/analyzers/program_flow/__init__.py
# ACTION: REPLACE ENTIRE FILE
"""Program flow analysis package.

This module DECLARES NOTHING of its own. Every name below is
re-exported from the module that owns it, never re-declared. A second
copy of CursorLoop diverges the day one of them gains a field.

Import order is dependency order, so a circular import fails loudly
here rather than intermittently at call time:

    flow_models.py                 value objects, no package dependency
    flow_line_reader.py            raw records -> classified lines
    flow_paragraph_scanner.py      paragraph spans, line ownership
    flow_cursor_loop_scanner.py    IDMS operations -> CursorLoop
    flow_write_scanner.py          WRITE vs IDMS update verbs
    flow_date_scanner.py           date / timestamp tokens
    flow_diagnostics.py            the report
    program_flow_analyzer.py       the facade, imported LAST

WHY THIS EXISTS

The package exported nothing, so every caller writing

    from converter.analyzers.program_flow import CursorLoop

failed at import time with

    ImportError: cannot import name 'CursorLoop' from
    'converter.analyzers.program_flow'

and took the whole conversion pipeline down with it, because
conversion_service -> conversion_pipeline -> program_flow_analyzer
all resolve through this one line.
"""

from __future__ import annotations

# ---------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------
from converter.analyzers.program_flow.flow_models import (  # noqa: F401
    CursorLoop,
    DateUsage,
    LogicalLine,
    OutputWrite,
    ParagraphSpan,
    ProgramFlowAnalysis,
)

# ---------------------------------------------------------------
# Scanners
# ---------------------------------------------------------------
from converter.analyzers.program_flow.flow_line_reader import (  # noqa: F401
    FlowLineReader,
)
from converter.analyzers.program_flow.flow_paragraph_scanner import (  # noqa: F401
    FlowParagraphScanner,
)
from converter.analyzers.program_flow.flow_cursor_loop_scanner import (  # noqa: F401
    FlowCursorLoopScanner,
)
from converter.analyzers.program_flow.flow_write_scanner import (  # noqa: F401
    FlowWriteScanner,
)
from converter.analyzers.program_flow.flow_date_scanner import (  # noqa: F401
    FlowDateScanner,
)
from converter.analyzers.program_flow.flow_diagnostics import (  # noqa: F401
    FlowDiagnostics,
)

# ---------------------------------------------------------------
# Facade, imported LAST
# ---------------------------------------------------------------
from converter.analyzers.program_flow.program_flow_analyzer import (  # noqa: F401
    ProgramFlowAnalyzer,
)

__all__ = [
    # value objects
    "CursorLoop",
    "DateUsage",
    "LogicalLine",
    "OutputWrite",
    "ParagraphSpan",
    "ProgramFlowAnalysis",
    # scanners
    "FlowCursorLoopScanner",
    "FlowDateScanner",
    "FlowDiagnostics",
    "FlowLineReader",
    "FlowParagraphScanner",
    "FlowWriteScanner",
    # facade
    "ProgramFlowAnalyzer",
]
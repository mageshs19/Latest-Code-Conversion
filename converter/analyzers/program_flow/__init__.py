# LOCATION: converter/analyzers/program_flow/program_flow_analyzer.py
# ACTION: CREATE NEW FILE
"""Generic flow analyzer for diagnostics.

This analyzer does not rewrite COBOL. It detects:

    - procedure paragraphs
    - cursor-like operations from parsed IDMS operations
    - output write statements, separated from IDMS update verbs
    - date / timestamp usage hints

REFACTOR - one 330-line class became six collaborators:

    flow_line_reader.py            raw records -> classified lines
    flow_paragraph_scanner.py      paragraph spans, line ownership
    flow_cursor_loop_scanner.py    IDMS operations -> CursorLoop
    flow_write_scanner.py          WRITE vs IDMS update verbs
    flow_date_scanner.py           date / timestamp tokens
    flow_diagnostics.py            the report

The public surface is UNCHANGED: analyze() still returns one
ProgramFlowAnalysis and ProgramFlowAnalyzer keeps its constructor.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_cursor_loop_scanner import (
    FlowCursorLoopScanner,
)
from converter.analyzers.program_flow.flow_date_scanner import FlowDateScanner
from converter.analyzers.program_flow.flow_diagnostics import FlowDiagnostics
from converter.analyzers.program_flow.flow_line_reader import FlowLineReader
from converter.analyzers.program_flow.flow_models import ProgramFlowAnalysis
from converter.analyzers.program_flow.flow_paragraph_scanner import (
    FlowParagraphScanner,
)
from converter.analyzers.program_flow.flow_write_scanner import FlowWriteScanner
from converter.domain.models import DclgenColumn, IdmsOperation, SheetMappingRow
from converter.resolvers.cursor_name_resolver import CursorNameResolver
from rules.program_flow_rules import FLOW_MESSAGES


class ProgramFlowAnalyzer:
    """Read-only program flow analysis."""

    def __init__(
        self,
        mapping_rows: list[SheetMappingRow] | None = None,
        dclgen_columns: list[DclgenColumn] | None = None,
        table_name_resolver=None,
    ) -> None:
        self.mapping_rows = mapping_rows or []
        self.dclgen_columns = dclgen_columns or []

        self.reader = FlowLineReader()
        self.paragraphs = FlowParagraphScanner()
        self.cursors = FlowCursorLoopScanner(
            cursor_name_resolver=CursorNameResolver(),
            table_name_resolver=table_name_resolver,
        )
        self.writes = FlowWriteScanner()
        self.dates = FlowDateScanner()

    def analyze(
        self,
        cobol_text: str,
        operations: list[IdmsOperation] | None = None,
    ) -> ProgramFlowAnalysis:
        if not str(cobol_text or "").strip():
            return ProgramFlowAnalysis(
                diagnostics=[FLOW_MESSAGES["empty_source"]]
            )

        lines = self.reader.read(cobol_text)
        paragraphs = self.paragraphs.spans(lines)
        owner_by_line = self.paragraphs.name_by_line(paragraphs)

        loops = self.cursors.loops(operations)
        writes, idms_writes = self.writes.scan(lines, owner_by_line)
        date_usages = self.dates.usages(lines)

        report = FlowDiagnostics()
        report.counts(
            mapping_rows=len(self.mapping_rows),
            dclgen_columns=len(self.dclgen_columns),
            paragraphs=len(paragraphs),
            cursor_loops=len(loops),
            output_writes=len(writes),
            idms_writes=len(idms_writes),
            date_usages=len(date_usages),
        )
        report.extend(self.cursors.diagnostics)
        report.loop_samples(loops)

        return ProgramFlowAnalysis(
            paragraphs=paragraphs,
            cursor_loops=loops,
            output_writes=writes,
            idms_writes=idms_writes,
            date_usages=date_usages,
            diagnostics=report.drain(),
        )


__all__ = ["ProgramFlowAnalyzer"]
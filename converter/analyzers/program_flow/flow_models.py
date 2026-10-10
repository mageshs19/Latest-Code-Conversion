# LOCATION: converter/analyzers/program_flow/flow_models.py
# ACTION: REPLACE ENTIRE FILE
"""Value objects for one program flow analysis.

Dataclasses and lookups only. No parsing, no I/O, no decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from converter.services.name_normalizer import NameNormalizer
from rules.program_flow_rules import LOOP_TYPE_UNKNOWN


@dataclass
class LogicalLine:
    """One source record reduced to its executable body.

    Replaces the bare (number, logical, raw) tuple, which left every
    consumer re-deciding what index 1 meant - and left none of them
    able to tell a COMMENT from code.
    """

    number: int = 0
    logical: str = ""
    raw: str = ""
    is_comment: bool = False

    @property
    def body(self) -> str:
        return self.logical.strip()

    @property
    def upper(self) -> str:
        return self.body.upper()


@dataclass
class ParagraphSpan:
    name: str
    start_line: int
    end_line: int
    lines: list[str] = field(default_factory=list)


@dataclass
class CursorLoop:
    record_name: str = ""
    table_name: str = ""
    set_name: str = ""
    operation: str = ""
    operation_line: int = 0
    process_paragraph: str = ""
    perform_line: int = 0
    until_line: int = 0
    loop_type: str = LOOP_TYPE_UNKNOWN
    cursor_name: str = ""
    open_paragraph: str = ""
    fetch_paragraph: str = ""
    close_paragraph: str = ""


@dataclass
class OutputWrite:
    output_record: str = ""
    paragraph_name: str = ""
    write_line: int = 0
    verb: str = ""
    move_lines: list[str] = field(default_factory=list)


@dataclass
class DateUsage:
    host_field: str = ""
    dclgen_group: str = ""
    idms_record: str = ""
    line_number: int = 0
    line_text: str = ""
    usage_type: str = ""


@dataclass
class ProgramFlowAnalysis:
    paragraphs: list[ParagraphSpan] = field(default_factory=list)
    cursor_loops: list[CursorLoop] = field(default_factory=list)
    output_writes: list[OutputWrite] = field(default_factory=list)
    idms_writes: list[OutputWrite] = field(default_factory=list)
    date_usages: list[DateUsage] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def process_paragraph_for_cursor(self, cursor_name: str) -> str:
        wanted = self._cobol(cursor_name)
        for loop in self.cursor_loops:
            if self._cobol(loop.cursor_name) == wanted:
                return loop.process_paragraph
        return ""

    def loop_for_set(self, set_name: str) -> CursorLoop | None:
        return self._first(lambda loop: loop.set_name, set_name)

    def loop_for_record(self, record_name: str) -> CursorLoop | None:
        return self._first(lambda loop: loop.record_name, record_name)

    def loop_for_table(self, table_name: str) -> CursorLoop | None:
        return self._first(lambda loop: loop.table_name, table_name)

    # ---- helpers
    def _first(self, reader, wanted: str) -> CursorLoop | None:
        target = NameNormalizer.normalize(wanted)
        if not target:
            return None
        for loop in self.cursor_loops:
            if NameNormalizer.normalize(reader(loop)) == target:
                return loop
        return None

    @staticmethod
    def _cobol(value: str) -> str:
        return NameNormalizer.to_cobol(NameNormalizer.normalize(value))


__all__ = [
    "LogicalLine", "ParagraphSpan", "CursorLoop",
    "OutputWrite", "DateUsage", "ProgramFlowAnalysis",
]
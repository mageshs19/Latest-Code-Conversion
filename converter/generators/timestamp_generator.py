from __future__ import annotations

from typing import List, Tuple

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.timestamp.cs_program_declarator import (
    CsProgramDeclarator,
)
from converter.generators.timestamp.program_id_resolver import (
    ProgramIdResolver,
)
from converter.generators.timestamp.timestamp_anchors import (
    TimestampAnchors,
)
from converter.generators.timestamp.timestamp_paragraph_builder import (
    TimestampParagraphBuilder,
)
from converter.generators.timestamp.timestamp_ws_builder import (
    TimestampWorkingStorageBuilder,
)
from patterns.timestamp_patterns import (
    COBOL_WRITE_OPERATION_PATTERN,
    DB2_WRITE_OPERATION_PATTERN,
    END_EXEC_PATTERN,
    EXEC_SQL_PATTERN,
)
from rules.timestamp_audit_rules import (
    TIMESTAMP_MESSAGES,
    TIMESTAMP_PARAGRAPH_EXIT_NAME,
    TIMESTAMP_PARAGRAPH_NAME,
    TIMESTAMP_WS_MARKER,
)

from converter.generators.timestamp.program_name_binder import (
    ProgramNameBinder,
)

class TimestampGenerator:

    WS_MARKER = TIMESTAMP_WS_MARKER
    PARAGRAPH_NAME = TIMESTAMP_PARAGRAPH_NAME
    PARAGRAPH_EXIT_NAME = TIMESTAMP_PARAGRAPH_EXIT_NAME

    def __init__(
        self,
        mapping_repository=None,
        table_name_resolver=None,
        host_variable_resolver=None,
    ) -> None:
        self.mapping_repository = mapping_repository
        self.table_name_resolver = table_name_resolver
        self.host_variable_resolver = host_variable_resolver
        self.geometry = LineGeometry()
        self.anchors = TimestampAnchors(self.geometry)
        self.program_ids = ProgramIdResolver()
        self.cs_program = CsProgramDeclarator(
            geometry=self.geometry,
            anchors=self.anchors,
            program_ids=self.program_ids,
        )
        self.program_name = ProgramNameBinder(
            geometry=self.geometry,
            anchors=self.anchors,
        )
        self.working_storage = TimestampWorkingStorageBuilder(
            geometry=self.geometry,
            anchors=self.anchors,
        )
        self.paragraph = TimestampParagraphBuilder(
            geometry=self.geometry,
            anchors=self.anchors,
            paragraph_name=self.PARAGRAPH_NAME,
        )
        self.messages: List[str] = []

    def apply(
        self,
        cobol_text: str,
        target_program_id: str = "",
    ) -> Tuple[str, List[str]]:
        self.messages = []

        text = str(cobol_text or "")
        if not text.strip():
            return "", self.messages

        lines = self.geometry.split(text)

        lines = self.cs_program.declare(lines, target_program_id)
        self.messages.extend(self.cs_program.messages)

        lines = self.program_name.bind(lines)
        self.messages.extend(self.program_name.messages)
        
        lines = self.working_storage.ensure(lines)
        self.messages.extend(self.working_storage.messages)

        lines = self.paragraph.ensure_paragraph(lines)
        self.messages.extend(self.paragraph.messages)

        lines = self.paragraph.ensure_perform(lines)
        self.messages.extend(self.paragraph.messages)

        self._log("summary")

        return self.geometry.join(lines).rstrip() + "\n", self.messages

    def has_db2_write_activity(self, cobol_text: str) -> bool:
        in_exec_sql = False

        for line in self.geometry.split(str(cobol_text or "")):
            if self.geometry.is_comment_or_blank(line):
                continue
            body = self.geometry.body(line)

            if EXEC_SQL_PATTERN.match(body):
                in_exec_sql = True
                continue

            if in_exec_sql and DB2_WRITE_OPERATION_PATTERN.match(body):
                return True

            if END_EXEC_PATTERN.match(body):
                in_exec_sql = False
                continue

            if COBOL_WRITE_OPERATION_PATTERN.match(body):
                return True

        return False

    def _has_db2_write_activity(self, text: str) -> bool:
        return self.has_db2_write_activity(text)

    def _log(self, key: str, **values) -> None:
        template = TIMESTAMP_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(f"{template} [{key}: {values}]")


__all__ = ["TimestampGenerator"]
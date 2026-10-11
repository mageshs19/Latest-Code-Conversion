from __future__ import annotations

from typing import List

from converter.generators.initialization.diagnostics import (
    InitializationDiagnostics,
)
from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.timestamp.program_id_resolver import (
    ProgramIdResolver,
)
from converter.generators.timestamp.timestamp_anchors import (
    TimestampAnchors,
)
from converter.services.generated_field_anchor import (
    GeneratedFieldAnchorResolver,
)
from rules.timestamp_audit_rules import (
    CS_PROGRAM_FIELD,
    CS_PROGRAM_NAME_COLUMN,
    CS_PROGRAM_PICTURE,
    CS_PROGRAM_PICTURE_COLUMN,
    CS_PROGRAM_VALUE_COLUMN,
    TIMESTAMP_MESSAGES,
)


class CsProgramDeclarator:

    def __init__(
        self,
        diagnostics=None,
        geometry: LineGeometry | None = None,
        anchors: TimestampAnchors | None = None,
        field_anchor: GeneratedFieldAnchorResolver | None = None,
        program_ids: ProgramIdResolver | None = None,
    ) -> None:
        self.diagnostics = diagnostics or InitializationDiagnostics()
        self.geometry = geometry or LineGeometry()
        self.anchors = anchors or TimestampAnchors(self.geometry)
        self.field_anchor = field_anchor or GeneratedFieldAnchorResolver()
        self.program_ids = program_ids or ProgramIdResolver()
        self.messages: List[str] = []

    def declare(
        self,
        lines: List[str],
        target_program_id: str,
    ) -> List[str]:
        self.messages = []

        existing = self.anchors.declaration_level(lines, CS_PROGRAM_FIELD)
        if existing:
            self._log(
                "cs_program_present",
                field=CS_PROGRAM_FIELD,
                level=existing,
            )
            return list(lines)

        program_id = self.program_ids.resolve_with_fallback(
            target_program_id,
            self.anchors.bodies(lines),
        )

        updated, anchor = self.field_anchor.resolve(lines)
        for message in self.field_anchor.messages:
            self.messages.append(message)
            self.diagnostics.messages.append(message)

        if not anchor.is_usable:
            self._log("cs_program_refused", field=CS_PROGRAM_FIELD)
            return list(lines)

        statement = self._render(anchor.level, anchor.indent, program_id)
        self._log(
            "cs_program_in_group",
            field=CS_PROGRAM_FIELD,
            level=anchor.level,
            group=anchor.group,
        )

        return (
            updated[: anchor.insert_index]
            + [statement]
            + updated[anchor.insert_index :]
        )

    def _render(self, level: str, indent: str, program_id: str) -> str:
        value = self.program_ids.padded(program_id)
        prefix = self._pad(str(level), CS_PROGRAM_NAME_COLUMN)
        prefix = f"{prefix}{CS_PROGRAM_FIELD}"
        with_picture = self._pad(prefix, CS_PROGRAM_PICTURE_COLUMN)
        with_picture = f"{with_picture}{CS_PROGRAM_PICTURE}"
        body = self._pad(with_picture, CS_PROGRAM_VALUE_COLUMN)
        return f"{indent}{body}VALUE '{value}'."

    @staticmethod
    def _pad(text: str, column: int) -> str:
        current = str(text or "")
        width = max(1, int(column) - len(current))
        return f"{current}{' ' * width}"

    def _log(self, key: str, **values) -> None:
        template = TIMESTAMP_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            message = template.format(**values)
        except (IndexError, KeyError):
            message = f"{template} [{key}: {values}]"
        self.messages.append(message)
        self.diagnostics.messages.append(message)


__all__ = ["CsProgramDeclarator"]
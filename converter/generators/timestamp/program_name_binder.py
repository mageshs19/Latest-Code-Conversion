from __future__ import annotations

from typing import List

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.timestamp.timestamp_anchors import (
    TimestampAnchors,
)
from patterns.timestamp_patterns import (
    constant_move_pattern,
    literal_move_pattern,
)
from rules.timestamp_audit_rules import (
    CS_PROGRAM_FIELD,
    ENFORCE_PROGRAM_NAME_CONSTANT,
    PROGRAM_NAME_FIELD,
    PROGRAM_NAME_MOVE_TEMPLATE,
    TIMESTAMP_MESSAGES,
)

STATEMENT_TERMINATOR = "."


class ProgramNameBinder:

    def __init__(
        self,
        geometry: LineGeometry | None = None,
        anchors: TimestampAnchors | None = None,
    ) -> None:
        self.geometry = geometry or LineGeometry()
        self.anchors = anchors or TimestampAnchors(self.geometry)
        self.literal = literal_move_pattern(PROGRAM_NAME_FIELD)
        self.constant = constant_move_pattern(
            CS_PROGRAM_FIELD, PROGRAM_NAME_FIELD
        )
        self.messages: List[str] = []

    def bind(self, lines: List[str]) -> List[str]:
        self.messages = []

        if not ENFORCE_PROGRAM_NAME_CONSTANT:
            return list(lines)

        if not self.anchors.declaration_level(lines, CS_PROGRAM_FIELD):
            self._log("program_name_refused", constant=CS_PROGRAM_FIELD)
            return list(lines)

        output: List[str] = []
        rewritten = 0
        already = 0

        for line in lines:
            if self.geometry.is_comment_or_blank(line):
                output.append(line)
                continue

            body = self.geometry.body(line)

            if self.constant.match(body):
                already += 1
                output.append(line)
                continue

            if not self.literal.match(body):
                output.append(line)
                continue

            output.append(self.geometry.replace_body(line, self._body(body)))
            rewritten += 1

        if rewritten:
            self._log(
                "program_name_bound",
                count=rewritten,
                constant=CS_PROGRAM_FIELD,
            )
        elif already:
            self._log("program_name_present", constant=CS_PROGRAM_FIELD)

        return output

    @staticmethod
    def _body(original: str) -> str:
        statement = PROGRAM_NAME_MOVE_TEMPLATE.format(
            constant=CS_PROGRAM_FIELD,
            field=PROGRAM_NAME_FIELD,
        )
        if str(original or "").rstrip().endswith(STATEMENT_TERMINATOR):
            return statement + STATEMENT_TERMINATOR
        return statement

    def _log(self, key: str, **values) -> None:
        template = TIMESTAMP_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(f"{template} [{key}: {values}]")


__all__ = ["ProgramNameBinder"]
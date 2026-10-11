from __future__ import annotations

from typing import List

from converter.generators.initialization.line_geometry import LineGeometry
from converter.generators.timestamp.timestamp_anchors import (
    NOT_FOUND,
    TimestampAnchors,
)
from rules.timestamp_audit_rules import (
    TIMESTAMP_MESSAGES,
    TIMESTAMP_WS_LINES,
    TIMESTAMP_WS_MARKER,
)

MARKER_LINE_TEMPLATE = "* {marker}"


class TimestampWorkingStorageBuilder:

    def __init__(
        self,
        geometry: LineGeometry | None = None,
        anchors: TimestampAnchors | None = None,
    ) -> None:
        self.geometry = geometry or LineGeometry()
        self.anchors = anchors or TimestampAnchors(self.geometry)
        self.messages: List[str] = []

    def block(self) -> List[str]:
        lines = [MARKER_LINE_TEMPLATE.format(marker=TIMESTAMP_WS_MARKER)]
        lines.extend(TIMESTAMP_WS_LINES)
        return lines

    def ensure(self, lines: List[str]) -> List[str]:
        self.messages = []

        if self.anchors.has_marker(lines, TIMESTAMP_WS_MARKER):
            self._log("working_storage_present")
            return list(lines)

        block = self.block()
        index = self.anchors.working_storage_insert_index(lines)

        if index == NOT_FOUND:
            self._log("no_working_storage")
            return block + [""] + list(lines)

        self._log("working_storage_added")
        return lines[:index] + [""] + block + [""] + lines[index:]

    def _log(self, key: str, **values) -> None:
        template = TIMESTAMP_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(f"{template} [{key}: {values}]")


__all__ = ["TimestampWorkingStorageBuilder"]
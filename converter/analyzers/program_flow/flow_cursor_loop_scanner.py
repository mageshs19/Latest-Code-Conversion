# LOCATION: converter/analyzers/program_flow/flow_cursor_loop_scanner.py
# ACTION: REPLACE ENTIRE FILE
"""Derives one CursorLoop per IDMS cursor-style operation.

CORRECTION - the cursor name was derived from the RECORD.

    cursor_name_from_table(record_name)

CursorNameResolver names a cursor from the DB2 TABLE: it strips the
table suffix and appends the cursor suffix. Db2InfrastructureGenerator
calls it with table_name. This analyzer called it with VMBEFF instead
of DZBEFFTV, so it produced a DIFFERENT cursor name and a different
710/720/730 set from the ones actually generated.

Nothing failed loudly. process_paragraph_for_cursor() and
loop_for_record() simply never matched, and every caller read "".

The record is resolved to its table first. With no resolver, or with an
unmapped record, the record name is still used - the previous
behaviour - but the limitation is REPORTED rather than silent.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import CursorLoop
from converter.domain.models import IdmsOperation
from converter.resolvers.cursor_name_resolver import CursorNameResolver
from converter.services.name_normalizer import NameNormalizer
from rules.program_flow_rules import (
    IDMS_RETRIEVAL_VERBS,
    FLOW_MESSAGES,
    LOOP_TYPE_CURSOR,
)


class FlowCursorLoopScanner:
    """Builds CursorLoop values from parsed IDMS operations."""

    def __init__(
        self,
        cursor_name_resolver: CursorNameResolver | None = None,
        table_name_resolver=None,
    ) -> None:
        self.cursor_name_resolver = cursor_name_resolver or CursorNameResolver()
        self.table_name_resolver = table_name_resolver
        self.diagnostics: list[str] = []

    def loops(self, operations: list[IdmsOperation] | None) -> list[CursorLoop]:
        self.diagnostics = []

        if self.table_name_resolver is None:
            self._log("no_table_resolver")

        output: list[CursorLoop] = []
        order_by_cursor: dict[str, int] = {}

        for operation in operations or []:
            name = str(getattr(operation, "operation", "") or "").upper()
            if name not in IDMS_RETRIEVAL_VERBS:
                continue

            record = NameNormalizer.normalize(
                getattr(operation, "record_name", "")
            )
            if not record:
                continue

            table = self._table_for_record(record)
            if not table:
                self._log("no_table_for_record", record=record)

            cursor = self.cursor_name_resolver.cursor_name_from_table(
                table or record
            )
            if cursor not in order_by_cursor:
                order_by_cursor[cursor] = len(order_by_cursor) + 1

            paragraphs = self.cursor_name_resolver.paragraph_names(
                cursor_order=order_by_cursor[cursor],
                cursor_name=cursor,
            )

            output.append(
                CursorLoop(
                    record_name=record,
                    table_name=table,
                    set_name=NameNormalizer.normalize(
                        getattr(operation, "set_name", "")
                    ),
                    operation=name,
                    operation_line=int(
                        getattr(operation, "line_number", 0) or 0
                    ),
                    loop_type=LOOP_TYPE_CURSOR,
                    cursor_name=cursor,
                    open_paragraph=paragraphs["open"],
                    fetch_paragraph=paragraphs["fetch"],
                    close_paragraph=paragraphs["close"],
                )
            )

        return output

    # ---- helpers
    def _table_for_record(self, record: str) -> str:
        resolver = self.table_name_resolver
        if resolver is None:
            return ""
        try:
            return NameNormalizer.normalize(resolver.table_for_record(record))
        except Exception:  # noqa: BLE001 - diagnostics must never abort
            return ""

    def _log(self, key: str, **values) -> None:
        template = FLOW_MESSAGES.get(key, "")
        if template:
            self.diagnostics.append(template.format(**values))


__all__ = ["FlowCursorLoopScanner"]
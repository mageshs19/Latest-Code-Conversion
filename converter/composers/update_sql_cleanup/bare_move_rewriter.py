"""Rewrites bare 'MOVE ... TO field' targets before a MODIFY into DB2 host moves.

CORRECTION 1 - a LOOKUP KEY was emitted as a COBOL data-name
--------------------------------------------------------------
The rewritten target came from owner._host_reference_key(), which
returns 'DCLGROUP.FIELD' - the SQL reference with its colon removed.
That is a dictionary key, not COBOL:

    MOVE DA-DD-MM-CCYY TO DCLDZBFARTV.DA-INFSDGD-479BFAR

The compiler reads the period as a sentence terminator. The correct
form is 'FIELD OF DCLGROUP', now supplied by _host_reference_cobol().

The key form is still used for the DATE branch's lookup, because the
date builder needs to identify the host; the EMITTED text is the COBOL
form in both branches.

CORRECTION 2 - a qualified target on a CONTINUATION looked bare
-----------------------------------------------------------------
MOVE_TO_BARE_FIELD_PATTERN is matched against ONE PHYSICAL LINE. A
statement that carries its qualifier on the next line

    MOVE NR-ID-FORM-AS OF VMDZ205I TO NR-ID-FORM-AS
      OF VMBFAR

presents a target that LOOKS bare. It was rewritten, and the orphaned
'OF VMBFAR' continuation survived to be renamed by a later pass, so one
statement ended up carrying BOTH conventions and overflowing column 72:

    TO DCLDZBFARTV.NR-IDFMAS-479BFAR
      OF DCLDZBFARTV

The target is now REFUSED, with a diagnostic, when the following
logical line opens with OF or IN. A refusal leaves working code; a
half-rewrite does not.
"""

from __future__ import annotations

from converter.composers.update_sql_cleanup.date_move_builder import (
    DateMoveBuilder,
)
from converter.services.name_normalizer import NameNormalizer

# COBOL qualifier connectors. A continuation opening with one of these
# means the target on the previous line was never bare.
QUALIFIER_CONNECTORS = ("OF ", "IN ")

# How far ahead to look for the continuation. A qualifier follows its
# data-name immediately; anything further is a separate statement.
CONTINUATION_SCAN_LIMIT = 3

MESSAGES = {
    "resolved": (
        "Update SQL cleanup: resolved bare MOVE target through "
        "Sheet Mapping and DCLGEN."
    ),
    "qualified_continuation": (
        "Update SQL cleanup: MOVE target {target} is qualified on the "
        "next line; left unchanged rather than half-rewritten."
    ),
}


class BareMoveRewriter:
    def __init__(self, owner, scanner, date_builder: DateMoveBuilder) -> None:
        self.owner = owner
        self.scanner = scanner
        self.date_builder = date_builder

    def rewrite(self, text: str) -> str:
        lines = text.splitlines()
        output: list[str] = []
        changed = False

        for index, line in enumerate(lines):
            logical = self.owner._logical(line)
            match = self.owner.MOVE_TO_BARE_FIELD_PATTERN.match(logical)

            if not match:
                output.append(line)
                continue

            target = NameNormalizer.to_cobol(match.group("tgt"))

            if self.owner._is_protected_bare_target(target):
                output.append(line)
                continue

            # CORRECTION 2 - the target may be qualified on the next line.
            if self._is_qualified_on_continuation(lines, index):
                self.owner.messages.append(
                    MESSAGES["qualified_continuation"].format(target=target)
                )
                output.append(line)
                continue

            record = self.scanner.next_modify_record(
                lines, index, max_distance=15
            )
            if not record:
                output.append(line)
                continue

            table = self.owner._table_for_record(record)
            column = self.owner._column_for_source_field(record, target)

            if not table or not column:
                output.append(line)
                continue

            # CORRECTION 1 - the EMITTED form is COBOL, not the key.
            host_cobol = self.owner._host_reference_cobol(table, column)
            if not host_cobol:
                output.append(line)
                continue

            leading = self.owner._leading_spaces(line)
            source_value = match.group("src").strip()

            if self.date_builder.is_db2_date_column(column):
                output.extend(
                    self.date_builder.date_ymd8_to_db2_external_move(
                        source_value=source_value,
                        host_key=host_cobol,
                        leading=leading,
                    )
                )
            else:
                output.append(f"{leading}MOVE {source_value} TO {host_cobol}")

            changed = True

        if changed:
            self.owner.messages.append(MESSAGES["resolved"])

        return "\n".join(output).rstrip() + "\n"

    #
    # Continuation inspection
    #
    def _is_qualified_on_continuation(
        self,
        lines: list[str],
        index: int,
    ) -> bool:
        """True when the next logical line opens with OF or IN."""
        limit = min(index + 1 + CONTINUATION_SCAN_LIMIT, len(lines))

        for offset in range(index + 1, limit):
            body = str(self.owner._logical(lines[offset]) or "").strip()
            if not body:
                continue
            return body.upper().startswith(QUALIFIER_CONNECTORS)

        return False


__all__ = ["QUALIFIER_CONNECTORS", "BareMoveRewriter"]
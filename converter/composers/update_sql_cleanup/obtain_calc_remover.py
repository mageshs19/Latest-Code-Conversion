# LOCATION: converter/composers/update_sql_cleanup/obtain_calc_remover.py
# ACTION: REPLACE ENTIRE FILE
"""Removes a generated OBTAIN CALC SELECT block before a direct UPDATE.

WHY THE REMOVAL IS CORRECT - FOR AN UPDATE PROGRAM

A direct ``UPDATE ... WHERE <composite key>`` carries every key column
in its own predicate, so the positioning read that preceded it is
redundant. Removing it saves a round trip and removes a SELECT whose
result nothing consumes.

CORRECTION - IT RAN ON RETRIEVAL PROGRAMS TOO
----------------------------------------------
This pass is reached through UpdateSqlCleanupComposer, which
_apply_cleanup_composers runs for EVERY program. It has never been told
the program kind, so it applied the update rule to retrieval programs
as well.

For a retrieval program the read is not redundant - it is the ONLY
population of the DCLGEN host group, and every later MOVE sources from
it. Measured on VMDZ4310: LrfPathExpander emitted the keyed parent,
_convert_lrf_calc_read converted it to a keyed SELECT and logged

    LRF keyed read: VMBEFF converted to a keyed SELECT ...

and this pass then matched the marker, consumed the block through
skip_generated_sql_and_sqlcode, and substituted

    *DB2: Removed OBTAIN CALC SELECT for VMBEFF.
    *DB2: Direct UPDATE will use mapped composite key WHERE clause.
    CONTINUE.

leaving twelve MOVEs out of DCLDZBEFFTV reading an unpopulated group,
and a comment claiming a direct UPDATE that a read-only program does
not contain.

This is the THIRD component to apply update semantics without the kind.
_convert_obtain_calc was the first; ConversionPipelineSteps records the
second. The kind is measured correctly for every program on every run -
the defect has always been delivery, never measurement.

The stand-down REPORTS. A pass that silently does nothing is
indistinguishable from a pass that is not wired, which is how the
original deletion went unnoticed for as long as it did.

SCOPE
-----
Only this rewriter stands down. ``_bare_move``, ``_qualified_date_move``
and ``_modify_update`` are also update-side and also run on retrieval
programs; whether they should is a real question and a SEPARATE change,
with its own measurement. Widening this one would move programs that
are currently correct.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.program_kind_rules import KIND_RETRIEVAL

# Attribute the owning composer carries. Named so producer and consumer
# cannot drift on a literal; matches PROGRAM_KIND_ATTRIBUTE in
# converter/pipeline/conversion/conversion_pipeline_steps.py.
PROGRAM_KIND_ATTRIBUTE = "program_kind"

STOOD_DOWN_MESSAGE = (
    "Update SQL cleanup: OBTAIN CALC removal stood down; this is a "
    "retrieval program and the keyed SELECT is the only population of "
    "the DCLGEN host group."
)
REMOVED_MESSAGE = (
    "Update SQL cleanup: removed unnecessary OBTAIN CALC SELECT "
    "before direct UPDATE."
)


class ObtainCalcRemover:
    def __init__(self, owner, scanner) -> None:
        self.owner = owner
        self.scanner = scanner

    def _stands_down(self) -> bool:
        """True when this program is read-only.

        Read through getattr so an owner that predates the attribute
        keeps today's behaviour rather than raising. An EMPTY kind means
        'not delivered' and is NOT treated as retrieval: refusing to
        remove on an undelivered kind would change update programs,
        which is the direction that must never move by accident.
        """
        kind = str(
            getattr(self.owner, PROGRAM_KIND_ATTRIBUTE, "") or ""
        ).strip().lower()
        return kind == KIND_RETRIEVAL

    def rewrite(self, text: str) -> str:
        if self._stands_down():
            if self.owner.CONVERTED_OBTAIN_CALC_PATTERN.search(str(text or "")):
                self.owner.messages.append(STOOD_DOWN_MESSAGE)
            return text

        lines = text.splitlines()
        output: list[str] = []
        index = 0
        changed = False

        while index < len(lines):
            logical = self.owner._logical(lines[index])
            match = self.owner.CONVERTED_OBTAIN_CALC_PATTERN.match(logical)

            if not match:
                output.append(lines[index])
                index += 1
                continue

            record = NameNormalizer.normalize(match.group("record"))
            cobol_record = NameNormalizer.to_cobol(record)
            leading = self.owner._leading_spaces(lines[index])
            table = self.owner._table_for_record(record)

            block_end = self.scanner.skip_generated_sql_and_sqlcode(
                lines, index + 1
            )

            if not table:
                output.extend(
                    [
                        f"{leading}*DB2: OBTAIN CALC conversion skipped for "
                        f"{cobol_record}.",
                        f"{leading}*DB2: Missing Sheet Mapping or DCLGEN "
                        f"table metadata.",
                        f"{leading}CONTINUE.",
                    ]
                )
                changed = True
                index = block_end
                continue

            key_columns = self.owner._db2_primary_key_columns(
                record=record,
                table=table,
            )

            if not key_columns:
                output.extend(
                    [
                        f"{leading}*DB2: OBTAIN CALC conversion skipped for "
                        f"{cobol_record}.",
                        f"{leading}*DB2: Missing key column metadata.",
                        f"{leading}CONTINUE.",
                    ]
                )
                changed = True
                index = block_end
                continue

            output.extend(
                [
                    f"{leading}*DB2: Removed OBTAIN CALC SELECT for "
                    f"{cobol_record}.",
                    f"{leading}*DB2: Direct UPDATE will use mapped composite "
                    f"key WHERE clause.",
                    f"{leading}CONTINUE.",
                ]
            )
            changed = True
            index = block_end

        if changed:
            self.owner.messages.append(REMOVED_MESSAGE)

        return "\n".join(output).rstrip() + "\n"


__all__ = ["ObtainCalcRemover"]
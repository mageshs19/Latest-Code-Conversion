# LOCATION: converter/composers/cleanup/initialize_before_output_cleanup.py
# ACTION: REPLACE ENTIRE FILE

"""
Initialize-before-output cleanup.

Ensures an INITIALIZE of the output record appears immediately before the
FIRST output-field population MOVE preceding a WRITE, and removes any
duplicate INITIALIZE for that record inside the population block.

CORRECTION - population MOVEs were matched on PHYSICAL lines
-------------------------------------------------------------
_line_targets_output_field() recognised two wrap shapes and missed a
third:

    MOVE src TO UIT-X             matched
    MOVE src / TO UIT-X           matched
    MOVE src TO / UIT-X           MISSED

The third is what the body wrapper emits when it breaks at a word
boundary, leaving TO as the last token of line 1 and a bare target on
line 2. Neither pattern can see it: line 1 has nothing after TO, line 2
has no TO at all.

Consequence in a production program:

    MOVE AM-CNSTK-479BEFF  OF DCLDZBEFFTV TO
    UIT-AM-CN-STOCK
    MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO
    UIT-AM-CND-STOCK
    INITIALIZE UITRECORD          <- inserted here
    MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE

Both amounts were zeroed in every written record, silently.

Matching is now performed against LOGICAL statements, assembled from
however many physical lines they occupy, and the insertion point is the
FIRST PHYSICAL LINE of the first matching statement.
"""

from converter.composers.cleanup.cleanup_message_collector import (
    CleanupMessageCollector,
)
from converter.composers.cleanup.cobol_cleanup_line_utils import (
    CobolCleanupLineUtils,
)
from converter.services.name_normalizer import NameNormalizer
from patterns.cobol_cleanup_patterns import (
    INITIALIZE_PATTERN,
    MOVE_TO_OUTPUT_FIELD_PATTERN,
    WRITE_PATTERN,
)
from rules.cobol_cleanup_rules import (
    INITIALIZE_LOOKBACK_WINDOW,
    OUTPUT_MOVE_SCAN_WINDOW,
    STATEMENT_CONTINUATION_TOKENS,
)

NOT_FOUND = -1


class InitializeBeforeOutputCleanup:
    def __init__(
        self,
        messages: CleanupMessageCollector,
        line_utils: CobolCleanupLineUtils | None = None,
    ) -> None:
        self.messages = messages
        self.line_utils = line_utils or CobolCleanupLineUtils()

    # ------------------------------------------------------------------
    # Line helpers
    # ------------------------------------------------------------------
    def _logical(self, line: str) -> str:
        return self.line_utils.logical(line)

    def _leading_spaces(self, line: str) -> str:
        return self.line_utils.leading_spaces(line)

    def _is_comment_or_blank(self, logical: str) -> bool:
        return self.line_utils.is_comment_or_blank(logical)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def ensure_initialize_before_output_population(self, text: str) -> str:
        lines = text.splitlines()
        output = list(lines)
        changed = False

        write_blocks = self._output_write_blocks(output)

        for block in reversed(write_blocks):
            write_index = int(block["write_index"])
            record = str(block["record"])
            first_move_index = int(block["first_move_index"])

            if write_index < 0 or first_move_index < 0:
                continue

            output, removed_count = (
                self._remove_initialize_for_record_in_range(
                    lines=output,
                    record=record,
                    start_index=first_move_index,
                    end_index=write_index,
                )
            )

            if removed_count:
                changed = True
                write_index -= removed_count

            if self._has_initialize_immediately_before(
                lines=output,
                index=first_move_index,
                record=record,
            ):
                continue

            leading = self._leading_spaces(output[first_move_index])
            output.insert(first_move_index, f"{leading}INITIALIZE {record}")
            changed = True
            self.messages.add("moved_initialize", record=record)

        if changed:
            return "\n".join(output).rstrip() + "\n"

        return text

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def _output_write_blocks(
        self,
        lines: list[str],
    ) -> list[dict[str, object]]:
        output: list[dict[str, object]] = []

        for index, line in enumerate(lines):
            logical = self._logical(line)
            match = WRITE_PATTERN.match(logical)

            if not match:
                continue

            record = match.group("record")
            first_move_index = (
                self._first_output_move_block_start_before_write(
                    lines=lines,
                    write_index=index,
                )
            )

            output.append(
                {
                    "write_index": index,
                    "record": record,
                    "first_move_index": first_move_index,
                }
            )

        return output

    def _first_output_move_block_start_before_write(
        self,
        lines: list[str],
        write_index: int,
    ) -> int:
        """First PHYSICAL line of the first statement targeting output.

        Statements are iterated in source order, so the first match is
        already the earliest. The returned index is the statement's own
        first line, never a continuation of it.
        """
        start = max(0, write_index - OUTPUT_MOVE_SCAN_WINDOW)

        for statement, first_index in self._logical_statements(
            lines=lines,
            start=start,
            end=write_index,
        ):
            if MOVE_TO_OUTPUT_FIELD_PATTERN.match(statement):
                return first_index

        return NOT_FOUND

    # ------------------------------------------------------------------
    # Logical statement assembly
    # ------------------------------------------------------------------
    def _logical_statements(
        self,
        lines: list[str],
        start: int,
        end: int,
    ):
        """Yield (statement_text, first_physical_index) in source order.

        Comment, blank and page-eject lines are skipped and never start
        or terminate a statement.
        """
        buffer = ""
        first = NOT_FOUND

        for index in range(max(0, start), min(end, len(lines))):
            logical = self._logical(lines[index])

            if not logical or self._is_comment_or_blank(logical):
                continue

            if first < 0:
                first = index

            buffer = f"{buffer} {logical}".strip() if buffer else logical

            if self._is_complete(buffer):
                yield buffer, first
                buffer, first = "", NOT_FOUND

        if first >= 0 and buffer:
            yield buffer, first

    @staticmethod
    def _is_complete(buffer: str) -> bool:
        """False while the statement ends on a continuation token.

        A line ending in TO, OF, AND and the rest cannot be the end of a
        statement; its operand is on the next line.
        """
        text = str(buffer or "").rstrip()

        if not text:
            return False

        if text.endswith(","):
            return False

        last = text.split()[-1].upper().rstrip(".")
        return last not in STATEMENT_CONTINUATION_TOKENS

    # ------------------------------------------------------------------
    # INITIALIZE handling
    # ------------------------------------------------------------------
    def _remove_initialize_for_record_in_range(
        self,
        lines: list[str],
        record: str,
        start_index: int,
        end_index: int,
    ) -> tuple[list[str], int]:
        output: list[str] = []
        removed_count = 0
        target_record = NameNormalizer.normalize(record)

        for index, line in enumerate(lines):
            if start_index <= index < end_index:
                match = INITIALIZE_PATTERN.match(self._logical(line))

                if match:
                    current = NameNormalizer.normalize(match.group("record"))

                    if current == target_record:
                        removed_count += 1
                        continue

            output.append(line)

        return output, removed_count

    def _has_initialize_immediately_before(
        self,
        lines: list[str],
        index: int,
        record: str,
    ) -> bool:
        lookback_start = max(0, index - INITIALIZE_LOOKBACK_WINDOW)
        target_record = NameNormalizer.normalize(record)

        for prior_index in range(lookback_start, index):
            match = INITIALIZE_PATTERN.match(self._logical(lines[prior_index]))

            if not match:
                continue

            if NameNormalizer.normalize(match.group("record")) == target_record:
                return True

        return False
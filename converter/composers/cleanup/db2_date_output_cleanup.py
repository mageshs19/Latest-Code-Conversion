# LOCATION: converter/composers/cleanup/db2_date_output_cleanup.py
# ACTION: REPLACE ENTIRE FILE

"""
DB2 date output cleanup.

Converts a DB2 date host move (MOVE DA-/DT- OF DCLxxx TO UIT-/OUT- date
field) into the shared output-date realignment block before a WRITE.

CORRECTION 1 - two of three wrap shapes were handled
-----------------------------------------------------
The pass matched PHYSICAL lines and recognised:

    MOVE DA-X OF DCLY TO UIT-Z          one line
    MOVE DA-X OF DCLY / TO UIT-Z        TO leads the continuation

but not:

    MOVE DA-X OF DCLY TO / UIT-Z        TO trails line 1, bare target

which is what the body wrapper emits when it breaks at a word boundary.
DB2_DATE_MOVE_ONE_LINE_PATTERN needs a target after TO;
DB2_DATE_MOVE_START_PATTERN needs the line to end at the group. Neither
matches, so a raw DB2 DATE reached the output record:

    MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO
    UIT-DA-UBSEC

UIT-DA-UBSEC is PIC X(08) and received a 10-byte DD.MM.CCYY value. The
pass said nothing, in any program.

Matching is now performed against LOGICAL statements, assembled from
however many physical lines they occupy. ONE pattern covers all three
shapes, and the whole physical span is replaced.

A statement whose span contains a comment or a blank line is never
converted: the conversion replaces the span, and a swallowed comment is
a silent loss of source.

CORRECTION 2 - one diagnostic for three different outcomes
-----------------------------------------------------------
A single "nothing converted" message made a successful run look like a
failure. CobolCleanupComposer is invoked TWICE per program - a known
duplication recorded in conversion_pipeline.py - so the log read:

    Cleanup: converted DB2 date move before output write.
    ...
    DB2 date output: no DB2 DATE host is moved to an output date field.

Both true, read together contradictory. Invocation 1 converted;
invocation 2 found the move already converted and reported zero
candidates.

Three outcomes are now reported distinctly:

    converted > 0                 the conversion happened
    candidates > 0, converted 0   a move was seen and declined
    candidates == 0               nothing to convert, with the line count
                                  so a second idempotent pass is obvious
"""

from converter.composers.cleanup.cleanup_message_collector import (
    CleanupMessageCollector,
)
from converter.composers.cleanup.cobol_cleanup_line_utils import (
    CobolCleanupLineUtils,
)
from converter.services.name_normalizer import NameNormalizer
from patterns.cobol_cleanup_patterns import (
    DB2_DATE_MOVE_ONE_LINE_PATTERN,
)
from rules.cobol_cleanup_rules import STATEMENT_CONTINUATION_TOKENS
from rules.db2_output_date_conversion_rules import (
    DB2_OUTPUT_DATE_CONVERSION_LINE_TEMPLATES,
    DB2_OUTPUT_DATE_HIGH_NUMERIC_LITERAL,
    DB2_OUTPUT_DATE_HIGH_VALUE_LITERAL,
    DB2_OUTPUT_DATE_LOW_VALUE_LITERAL,
)

NOT_FOUND = -1

DB2_DATE_HOST_PREFIXES = ("DA-", "DT-")
OUTPUT_DATE_FIELD_PREFIXES = (
    "UIT-DA-",
    "UIT-DT-",
    "OUT-DA-",
    "OUT-DT-",
)


class Db2DateOutputCleanup:
    def __init__(
        self,
        messages: CleanupMessageCollector,
        line_utils: CobolCleanupLineUtils | None = None,
    ) -> None:
        self.messages = messages
        self.line_utils = line_utils or CobolCleanupLineUtils()

    def _logical(self, line: str) -> str:
        return self.line_utils.logical(line)

    def _leading_spaces(self, line: str) -> str:
        return self.line_utils.leading_spaces(line)

    def _is_comment_or_blank(self, logical: str) -> bool:
        return self.line_utils.is_comment_or_blank(logical)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def convert_db2_date_moves_to_output_dates(self, text: str) -> str:
        lines = text.splitlines()
        output: list[str] = []
        converted = 0
        candidates = 0

        for statement, first, last in self._logical_statements(lines):
            if statement:
                match = DB2_DATE_MOVE_ONE_LINE_PATTERN.match(statement)

                if match:
                    candidates += 1
                    block = self._date_conversion_lines(
                        leading=self._leading_spaces(lines[first]),
                        field=match.group("field"),
                        group=match.group("group"),
                        target=match.group("target"),
                    )

                    if block:
                        output.extend(block)
                        converted += 1
                        continue

            output.extend(lines[first : last + 1])

        return self._report(
            text=text,
            output=output,
            converted=converted,
            candidates=candidates,
            examined=len(lines),
        )

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------
    def _report(
        self,
        text: str,
        output: list[str],
        converted: int,
        candidates: int,
        examined: int,
    ) -> str:
        """Report exactly one of three outcomes and return the result.

        Silence here cost a full debugging cycle: a raw DB2 DATE reached
        the output record and no pass admitted to having looked.
        """
        if converted:
            self.messages.add("converted_db2_date_move", count=converted)
            return "\n".join(output).rstrip() + "\n"

        if candidates:
            # A move was recognised and declined by the eligibility gate.
            # Worth knowing: the target was not an output date field.
            self.messages.add(
                "db2_date_move_not_eligible",
                count=candidates,
            )
            return text

        # No candidate at all. Not a refusal. Either the program has no
        # DB2 DATE host moved to an output date field, or this is the
        # second, idempotent invocation of the cleanup composer and the
        # move is already converted. The line count distinguishes them.
        self.messages.add("db2_date_no_output_move", examined=examined)
        return text

    # ------------------------------------------------------------------
    # Logical statement assembly
    # ------------------------------------------------------------------
    def _logical_statements(self, lines: list[str]):
        """Yield (statement_text, first_index, last_index) in source order.

        A comment or blank line yields as its own ("", index, index) entry
        and closes any statement being accumulated, so it is copied
        through verbatim and can never be absorbed into a conversion.
        """
        buffer = ""
        first = NOT_FOUND

        for index, line in enumerate(lines):
            logical = self._logical(line)

            if not logical or self._is_comment_or_blank(logical):
                if first >= 0:
                    yield buffer, first, index - 1
                    buffer, first = "", NOT_FOUND
                yield "", index, index
                continue

            if first < 0:
                first = index

            buffer = f"{buffer} {logical}".strip() if buffer else logical

            if self._is_complete(buffer):
                yield buffer, first, index
                buffer, first = "", NOT_FOUND

        if first >= 0:
            yield buffer, first, len(lines) - 1

    @staticmethod
    def _is_complete(buffer: str) -> bool:
        """False while the statement ends on a continuation token.

        A line ending in TO, OF, AND and the rest cannot end a statement;
        its operand is on the next line.
        """
        text = str(buffer or "").rstrip()

        if not text:
            return False

        if text.endswith(","):
            return False

        last = text.split()[-1].upper().rstrip(".")
        return last not in STATEMENT_CONTINUATION_TOKENS

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------
    def _should_generate_output_date_conversion(
        self,
        field_name: str,
        target_name: str,
    ) -> bool:
        """True only for a DB2 date host moved to an output date field.

        Prevents ZEROES/SPACES date logic being generated for:
        - non-date output fields
        - DB2 DCLGEN host variables
        - update host moves
        - unrelated MOVE statements
        """
        field = str(field_name or "").strip().upper()
        target = str(target_name or "").strip().upper()

        if not field or not target:
            return False

        if not field.startswith(DB2_DATE_HOST_PREFIXES):
            return False

        if not target.startswith(OUTPUT_DATE_FIELD_PREFIXES):
            return False

        if " OF DCL" in target:
            return False

        if target.startswith("DCL"):
            return False

        return True

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _date_conversion_lines(
        self,
        leading: str,
        field: str,
        group: str,
        target: str,
    ) -> list[str]:
        field_name = NameNormalizer.to_cobol(field)
        group_name = NameNormalizer.to_cobol(group)
        target_name = NameNormalizer.to_cobol(target)

        if not self._should_generate_output_date_conversion(
            field_name=field_name,
            target_name=target_name,
        ):
            return []

        output: list[str] = []

        for template in DB2_OUTPUT_DATE_CONVERSION_LINE_TEMPLATES:
            line = template.format(
                indent=leading,
                field_name=field_name,
                group_name=group_name,
                target_name=target_name,
                low_value=DB2_OUTPUT_DATE_LOW_VALUE_LITERAL,
                high_value=DB2_OUTPUT_DATE_HIGH_VALUE_LITERAL,
                high_numeric=DB2_OUTPUT_DATE_HIGH_NUMERIC_LITERAL,
            )

            if not line.strip():
                continue

            output.append(line.rstrip())

        return output


__all__ = ["Db2DateOutputCleanup"]
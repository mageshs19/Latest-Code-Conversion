# LOCATION: converter/composers/structural_safety_composer.py
# ACTION: REPLACE ENTIRE FILE

"""Final structural safety pass. COMMENT-ONLY, never deletes.

A2 - orphaned whole-record reference
    MOVE VMBFAS TO F-FORM survives after COPY IDMS LR is removed, so
    VMBFAS is an undefined data-name.

A4 - unreachable statement after a paragraph EXIT
    A statement between EXIT. and the next paragraph header can never
    run and sits outside any paragraph.

CORRECTION 1 - EXIT. matched the paragraph-header pattern
    The exit test now runs BEFORE the header test.

CORRECTION 2 - long markers lost their sequence numbers
    Comments are wrapped through emit().

CORRECTION 3 - comment lines were never recognised
    _is_comment() tested FixedFormatLineService.logical(), which returns
    columns 8-72 only. The '*' indicator lives in column 7, so it was
    never in the string being tested and every comment was treated as
    executable. Classification now reads the RAW line.

CORRECTION 4 - a tracking bug could comment out the whole program
    With CORRECTION 1 and 3 missing, the A4 guard stayed armed past the
    generated cursor block and commented 60+ lines. A hard cap now
    reverts the entire pass when it matches more lines than real
    unreachable code ever spans.

CORRECTION 5 - a COPY'd record was treated as undeclared
    _declared_names harvested LEVEL-NUMBER lines only. A record brought
    in by

        COPY VMDZ205I.

    has no level-number line in the converted source - the copybook text
    is not expanded - so VMDZ205I looked undeclared and the guard
    commented out

        MOVE VMDZ205I TO WS-INPUT-KASBONS

    which RestartReadParagraphBuilder had written one pass earlier. That
    statement saves the input record into the checkpoint key, so
    KY-RESTART became permanently spaces and a restart could not
    reposition the file.

    A name is DECLARED when the program carries any of:

        a level-number entry          01 / 05 / 77 ...
        a COPY member                 COPY VMDZ205I.
        an FD file or its record      FD INFIL / DATA RECORD IS ...
        an EXEC SQL INCLUDE member    and its DCL<member> host group

    Nothing here needs mapping knowledge; it is all readable from the
    program.

CORRECTION 6 - the fallback comment sat in Area B
    FALLBACK_COMMENT_PREFIX was six spaces then '*'. On a free-form line
    - which is every line this pass sees before the final resequencer -
    the resequencer then prepends six sequence digits and a blank
    indicator, putting the '*' at column 13:

        002420       *DB2-KEEP: VMDZ205I has no DB2 layout ...

    That is not a comment, it is a statement beginning with '*'. A
    free-form comment is simply '*text'; the resequencer promotes a
    leading indicator into column 7, the same contract
    FixedFormatLineService.build() follows.

KNOWN GAP - only MOVE forms are commented
    VMBWCEF is genuinely undeclared in VMDZ4302 and appears twice:

        MOVE SPACES TO VMBWCEF              <- commented
        DISPLAY 'VMBWCEF    ' VMBWCEF       <- not matched

    Widening the net to arbitrary operands is how a guard ends up
    eating a program, so the second form is REPORTED and left alone.
    The log names the record, the line and the statement, and the
    compiler catches it either way.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.structural_safety_patterns import (
    EXIT_STATEMENT_PATTERN,
    MOVE_BARE_SOURCE_PATTERN,
    MOVE_BARE_TARGET_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    QUALIFIER_PATTERN,
    SECTION_HEADER_PATTERN,
)
from rules.structural_safety_rules import (
    ENFORCE_ORPHANED_RECORD_GUARD,
    ENFORCE_UNREACHABLE_STATEMENT_GUARD,
    MAX_UNREACHABLE_STATEMENTS,
    ORPHANED_LINE_PREFIX,
    ORPHANED_RECORD_MARKER_TEMPLATE,
    STRUCTURAL_SAFETY_MESSAGES,
    UNREACHABLE_MARKER,
)

DCLGEN_PREFIX = "DCL"

# A free-form comment is '*text'. The resequencer promotes a leading
# indicator into column 7 - see CORRECTION 6.
FALLBACK_COMMENT_PREFIX = "*"

# Statement words that DECLARE a name without using a level number.
COPY_VERB = "COPY"
FD_VERBS = ("FD", "SD")
INCLUDE_WORD = "INCLUDE"
EXEC_WORD = "EXEC"
DATA_RECORD_PREFIXES = ("DATA RECORD IS ", "DATA RECORDS ARE ")

# Words that never name a record, so they are never reported as one.
NON_RECORD_WORDS = frozenset(
    {"SPACE", "SPACES", "ZERO", "ZEROS", "ZEROES", "LOW-VALUES",
     "HIGH-VALUES", "QUOTE", "QUOTES", "NULL", "NULLS"}
)


class StructuralSafetyComposer:
    """Comments references the compiler would reject."""

    def __init__(
        self,
        original_idms_text: str = "",
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.original_idms_text = str(original_idms_text or "")
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

    # ---------------------------------------------------------- public
    def compose(self, text: str) -> str:
        self.messages = []

        if not text:
            return ""

        lines = (
            str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
        )

        if ENFORCE_ORPHANED_RECORD_GUARD:
            lines = self._guard_orphaned_records(lines)

        if ENFORCE_UNREACHABLE_STATEMENT_GUARD:
            lines = self._guard_unreachable_statements(lines)

        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------- A2
    # ------------------------------------------------------------- A2
    def _guard_orphaned_records(self, lines: list[str]) -> list[str]:
        records = self._idms_record_names()
        if not records:
            return lines

        declared = self._declared_names(lines)
        orphans = {name for name in records if name not in declared}
        if not orphans:
            return lines

        # record -> (first line, first body, count)
        seen: dict[str, tuple[int, str, int]] = {}
        output: list[str] = []

        for number, line in enumerate(lines, start=1):
            if self._is_skippable(line):
                output.append(line)
                continue

            body = self._logical(line)
            if not body:
                output.append(line)
                continue

            record = self._whole_record_reference(body, orphans)
            if not record:
                self._note_reference(body, orphans, number, seen)
                output.append(line)
                continue

            output.extend(
                self._comment_lines(
                    line,
                    ORPHANED_RECORD_MARKER_TEMPLATE.format(record=record),
                )
            )
            output.extend(
                self._comment_lines(line, f"{ORPHANED_LINE_PREFIX}{body}")
            )
            self.messages.append(
                STRUCTURAL_SAFETY_MESSAGES[
                    "orphaned_record_commented"
                ].format(record=record)
            )

        self._report_references(seen)
        return output

    def _note_reference(
        self,
        body: str,
        orphans: set[str],
        number: int,
        seen: dict[str, tuple[int, str, int]],
    ) -> None:
        """Record an orphan used in a form this pass will not comment.

        CORRECTION - quoted literals were tokenised as data references.

            DISPLAY 'PARAMETER DATE IN ERROR = ' DATE6
            DISPLAY 'BIND VMBWCEF MISLUKT '

        matched ERROR and VMBWCEF inside the literal, producing reports
        for text that is not a reference at all. Literals are blanked
        before tokenising, and each record is reported ONCE with a
        count rather than once per line - twenty-seven messages for two
        programs is noise, not a finding.
        """
        words = {
            word.strip(".,()")
            for word in self._without_literals(body).upper().split()
        }
        for record in orphans & words:
            if record in NON_RECORD_WORDS:
                continue
            first_line, first_body, count = seen.get(
                record, (number, body, 0)
            )
            seen[record] = (first_line, first_body, count + 1)

    def _report_references(
        self,
        seen: dict[str, tuple[int, str, int]],
    ) -> None:
        template = STRUCTURAL_SAFETY_MESSAGES.get(
            "orphaned_record_referenced", ""
        )
        if not template:
            return
        for record in sorted(seen):
            line, body, count = seen[record]
            self.messages.append(
                template.format(
                    record=record, count=count, line=line, body=body
                )
            )

    @staticmethod
    def _without_literals(body: str) -> str:
        """The statement with quoted literals blanked out.

        A record name inside a DISPLAY literal is text, not a
        reference. Blanking rather than removing preserves word
        boundaries, so adjacent tokens cannot be glued together.
        """
        out: list[str] = []
        quote = ""
        for char in str(body or ""):
            if quote:
                if char == quote:
                    quote = ""
                out.append(" ")
                continue
            if char in ("'", '"'):
                quote = char
                out.append(" ")
                continue
            out.append(char)
        return "".join(out)
    

    def _idms_record_names(self) -> set[str]:
        names: set[str] = set()
        for match in QUALIFIER_PATTERN.finditer(self.original_idms_text):
            name = match.group("record").upper()
            if name and not name.startswith(DCLGEN_PREFIX):
                names.add(name)
        return names

    # ----------------------------------------------- CORRECTION 5
    def _declared_names(self, lines: list[str]) -> set[str]:
        """Every name the program declares, by any means.

        A level-number entry is only one of four ways. Harvesting just
        that treated every COPY'd record as an orphan.
        """
        declared: set[str] = set()

        for line in lines:
            if self._is_skippable(line):
                continue

            body = self._logical(line)
            if not body:
                continue

            if PROCEDURE_DIVISION_PATTERN.match(body):
                break

            upper = body.upper()
            parts = upper.split()
            if not parts:
                continue

            # 1. A level-number entry.
            if len(parts) >= 2 and parts[0].rstrip(".").isdigit():
                declared.add(parts[1].rstrip(".").upper())
                continue

            # 2. A COPY member. Its text is not expanded here, but the
            #    compiler will expand it, so the name IS declared.
            if parts[0] == COPY_VERB and len(parts) >= 2:
                declared.add(parts[1].rstrip(".").upper())
                continue

            # 3. An FD / SD file name.
            if parts[0] in FD_VERBS and len(parts) >= 2:
                declared.add(parts[1].rstrip(".").upper())
                continue

            # 4. The record an FD names explicitly.
            for prefix in DATA_RECORD_PREFIXES:
                if upper.startswith(prefix):
                    declared.add(
                        upper[len(prefix):].split()[0].rstrip(".").upper()
                    )
                    break

            # 5. A DCLGEN member and the host group it declares.
            if parts[0] == EXEC_WORD and INCLUDE_WORD in parts:
                position = parts.index(INCLUDE_WORD)
                if position + 1 < len(parts):
                    member = parts[position + 1].rstrip(".").upper()
                    declared.add(member)
                    declared.add(f"{DCLGEN_PREFIX}{member}")

        return declared

    @staticmethod
    def _whole_record_reference(body: str, orphans: set[str]) -> str:
        for pattern in (MOVE_BARE_SOURCE_PATTERN, MOVE_BARE_TARGET_PATTERN):
            match = pattern.match(body)
            if not match:
                continue
            name = match.group("name").upper()
            if name in orphans and name not in NON_RECORD_WORDS:
                return name
        return ""

    def _report_other_reference(
        self,
        body: str,
        orphans: set[str],
        number: int,
    ) -> None:
        """Name an orphan used in a form this pass will not comment.

        Reporting, never editing. See KNOWN GAP in the module docstring.
        """
        template = STRUCTURAL_SAFETY_MESSAGES.get(
            "orphaned_record_referenced", ""
        )
        if not template:
            return

        words = {
            word.strip(".,()'\"").upper()
            for word in body.split()
        }
        for record in sorted(orphans & words):
            if record in NON_RECORD_WORDS:
                continue
            message = template.format(
                record=record, line=number, body=body
            )
            if message not in self.messages:
                self.messages.append(message)

    # ------------------------------------------------------------- A4
    def _guard_unreachable_statements(self, lines: list[str]) -> list[str]:
        output: list[str] = []
        after_exit = False
        in_procedure = False
        commented = 0

        for line in lines:
            # Comment, page-eject, debug and continuation lines are
            # classified from the RAW line: the indicator is column 7,
            # which logical() does not return.
            if self._is_skippable(line):
                output.append(line)
                continue

            body = self._logical(line)

            if PROCEDURE_DIVISION_PATTERN.match(body):
                in_procedure = True
                after_exit = False
                output.append(line)
                continue

            if not in_procedure or not body:
                output.append(line)
                continue

            # EXIT test FIRST: "EXIT." also matches the header pattern.
            if EXIT_STATEMENT_PATTERN.match(body):
                after_exit = True
                output.append(line)
                continue

            # Paragraph and section headers disarm the guard. The name
            # may start with a digit: 710-OPEN-<cursor>.
            if PARAGRAPH_HEADER_PATTERN.match(body) or (
                SECTION_HEADER_PATTERN.match(body)
            ):
                after_exit = False
                output.append(line)
                continue

            if not after_exit:
                output.append(line)
                continue

            output.extend(self._comment_lines(line, UNREACHABLE_MARKER))
            output.extend(
                self._comment_lines(line, f"{ORPHANED_LINE_PREFIX}{body}")
            )
            commented += 1

        # Blast-radius cap: revert everything rather than trust a guard
        # that has clearly lost sync with the paragraph structure.
        if commented > MAX_UNREACHABLE_STATEMENTS:
            self.messages.append(
                STRUCTURAL_SAFETY_MESSAGES["unreachable_aborted"].format(
                    count=commented,
                    limit=MAX_UNREACHABLE_STATEMENTS,
                )
            )
            return lines

        if commented:
            self.messages.append(
                STRUCTURAL_SAFETY_MESSAGES["unreachable_commented"].format(
                    count=commented,
                )
            )

        return output

    # -------------------------------------------------------- helpers
    def _comment_lines(self, reference: str, body: str) -> list[str]:
        """Comment line(s), wrapped when the text exceeds columns 8-72."""
        text = str(body or "").lstrip("*").strip()
        try:
            if self.fixed_format.is_fixed_line(reference):
                left, _ind, _old, right = self.fixed_format.split(reference)
                return self.fixed_format.emit(left, "*", text, right)
        except Exception:  # noqa: BLE001
            pass
        return [f"{FALLBACK_COMMENT_PREFIX}{text}"]

    def _logical(self, line: str) -> str:
        try:
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:  # noqa: BLE001
            return str(line or "").strip()

    def _is_skippable(self, line: str) -> bool:
        """Comment / page-eject / debug / continuation, read from column 7."""
        try:
            return bool(self.fixed_format.is_comment_or_control_line(line))
        except Exception:  # noqa: BLE001
            return str(line or "").lstrip().startswith(("*", "/"))


__all__ = ["StructuralSafetyComposer"]
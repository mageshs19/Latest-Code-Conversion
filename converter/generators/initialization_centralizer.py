"""
INITIALIZATION CENTRALIZER

Consolidates DCLGEN INITIALIZE statements into a single 100-INITIALIZE
paragraph performed once at startup.

Invariants:
  - The paragraph is CREATED and PROVEN before anything is removed. A
    half-applied pass leaves the program fetching into host groups that
    were never cleared, which is silent data corruption rather than a
    compile error.
  - An anonymous mainline is never captured. A PROCEDURE DIVISION whose
    first statement carries no paragraph header would otherwise be
    absorbed by the inserted header, taking STOP RUN with it.
  - Nothing is ever replaced by an explanatory comment. Generated
    comments are written into columns 8-72 and truncate mid-word.
    Decisions go to self.messages.
  - All matching is done against the logical body (columns 8-72), so
    fixed-format right sequence numbers cannot defeat a pattern.
"""

from __future__ import annotations

import re
from typing import List, Set, Tuple


class InitializationCentralizer:
    """Centralizes DCLGEN INITIALIZE statements into 100-INITIALIZE."""

    INIT_PARAGRAPH_NAME = "100-INITIALIZE"
    TIMESTAMP_PARAGRAPH_NAME = "600-GET-TIMESTAMP"
    PROGRAM_CONSTANT = "CS-PROGRAM"
    PROGRAM_NAME_FIELD = "PROGRAM-NAME"
    STATEMENT_INDENT = " " * 4

    LINE_WIDTH = 80
    BODY_START = 7
    BODY_END = 72

    NON_PARAGRAPH_WORDS = frozenset({
        "CONTINUE", "EXIT", "GOBACK", "END-IF", "END-EVALUATE", "END-EXEC",
        "END-PERFORM", "END-READ", "END-SEARCH", "END-STRING", "END-WRITE",
        "STOP",
    })

    DCLGEN_PATTERN = re.compile(
        r"(?:EXEC\s+SQL\s+INCLUDE|\bCOPY)\s+(?P<group>DCL\w+)\b",
        re.IGNORECASE,
    )
    DCLGEN_REFERENCE_PATTERN = re.compile(
        r"(?::|\bOF\s+)(?P<group>DCL\w+)\b",
        re.IGNORECASE,
    )
    INITIALIZE_PATTERN = re.compile(
        r"^INITIALIZE\s+(?P<group>[A-Z0-9][A-Z0-9-]*)\s*\.?$",
        re.IGNORECASE,
    )
    PARAGRAPH_HEADER_PATTERN = re.compile(
        r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s*\.$",
        re.IGNORECASE,
    )
    SECTION_HEADER_PATTERN = re.compile(
        r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s+SECTION\s*\.$",
        re.IGNORECASE,
    )
    DIVISION_PATTERN = re.compile(
        r"^[A-Z]+\s+DIVISION\b",
        re.IGNORECASE,
    )
    PROCEDURE_DIVISION_PATTERN = re.compile(
        r"^PROCEDURE\s+DIVISION\b",
        re.IGNORECASE,
    )
    FETCH_PARAGRAPH_NAME_PATTERN = re.compile(
        r"^\d{3,6}-\w*FETCH\w*",
        re.IGNORECASE,
    )
    LITERAL_PROGRAM_MOVE_PATTERN = re.compile(
        r"^MOVE\s+'[^']+'\s+TO\s+PROGRAM-NAME\s*\.?$",
        re.IGNORECASE,
    )

    def __init__(self, program_text: str):
        self.program_text = program_text
        self.dclgen_groups: Set[str] = set()
        self.messages: List[str] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def process(self) -> str:
        text = str(self.program_text or "")
        if not text.strip():
            return text

        lines = self._split(text)

        self._find_dclgen_groups(lines)
        if not self.dclgen_groups:
            self._note("no DCLGEN group referenced; pass skipped")
            return text

        if self._procedure_division_index(lines) < 0:
            self._note("no PROCEDURE DIVISION found; pass skipped")
            return text

        # Standalone block cleanup runs FIRST, while the mainline region is
        # still the only place a generated block can be.
        working = self._remove_standalone_initialize_block(lines)

        working = self._insert_initialize_paragraph(working)
        if not self._initialize_block_present(working):
            self._note(
                f"{self.INIT_PARAGRAPH_NAME} was not created; "
                f"fetch-prologue INITIALIZE statements left in place"
            )
            return text

        working = self._ensure_perform_initialize(working)
        if not self._perform_initialize_present(working):
            self._note(
                f"PERFORM {self.INIT_PARAGRAPH_NAME} could not be "
                f"inserted; pass rolled back"
            )
            return text

        working = self._remove_initialize_from_fetches(working)
        working = self._ensure_variable_program_name_move(working)

        self._note(
            f"centralized {len(self.dclgen_groups)} DCLGEN group(s) "
            f"into {self.INIT_PARAGRAPH_NAME}"
        )
        return "\n".join(working)

    # ------------------------------------------------------------------
    # Line geometry
    # ------------------------------------------------------------------

    @staticmethod
    def _split(text: str) -> List[str]:
        return str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")

    def _body(self, line: str) -> str:
        """Columns 8-72 of a fixed-format record, else the stripped line."""
        text = str(line or "").rstrip("\r\n")
        if not text:
            return ""
        if len(text) > self.BODY_START and text[:6].isdigit():
            return text[self.BODY_START:self.BODY_END].strip()
        return text.strip()

    def _indicator(self, line: str) -> str:
        text = str(line or "")
        if len(text) > 6 and text[:6].isdigit():
            return text[6:7]
        stripped = text.lstrip()
        return stripped[:1] if stripped[:1] in ("*", "/") else " "

    def _is_comment_or_blank(self, line: str) -> bool:
        if self._indicator(line) in ("*", "/"):
            return True
        return not self._body(line)

    def _is_paragraph_header(self, line: str) -> bool:
        body = self._body(line)
        if not body or self._is_comment_or_blank(line):
            return False
        if self.DIVISION_PATTERN.match(body):
            return False
        if self.SECTION_HEADER_PATTERN.match(body):
            return True
        match = self.PARAGRAPH_HEADER_PATTERN.match(body)
        if not match:
            return False
        return match.group("name").upper() not in self.NON_PARAGRAPH_WORDS

    def _paragraph_name(self, line: str) -> str:
        body = self._body(line)
        match = (
            self.PARAGRAPH_HEADER_PATTERN.match(body)
            or self.SECTION_HEADER_PATTERN.match(body)
        )
        return match.group("name").upper() if match else ""

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _find_dclgen_groups(self, lines: List[str]) -> None:
        for line in lines:
            if self._is_comment_or_blank(line):
                continue
            body = self._body(line)
            for pattern in (
                self.DCLGEN_PATTERN,
                self.DCLGEN_REFERENCE_PATTERN,
            ):
                for match in pattern.finditer(body):
                    self.dclgen_groups.add(match.group("group").upper())

    def _procedure_division_index(self, lines: List[str]) -> int:
        for index, line in enumerate(lines):
            if self._is_comment_or_blank(line):
                continue
            if self.PROCEDURE_DIVISION_PATTERN.match(self._body(line)):
                return index
        return -1

    def _first_statement_index(self, lines: List[str], after: int) -> int:
        for index in range(after + 1, len(lines)):
            if not self._is_comment_or_blank(lines[index]):
                return index
        return -1

    def _fetch_paragraph_spans(
        self, lines: List[str]
    ) -> List[Tuple[int, int]]:
        spans: List[Tuple[int, int]] = []
        start = -1
        for index, line in enumerate(lines):
            if not self._is_paragraph_header(line):
                continue
            if start >= 0:
                spans.append((start, index - 1))
                start = -1
            if self.FETCH_PARAGRAPH_NAME_PATTERN.match(
                self._paragraph_name(line)
            ):
                start = index
        if start >= 0:
            spans.append((start, len(lines) - 1))
        return spans

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def _build_initialize_paragraph(self, lines: List[str]) -> List[str]:
        bodies = [self._body(line).upper() for line in lines]
        joined = "\n".join(bodies)

        block = ["", f"{self.INIT_PARAGRAPH_NAME}."]
        for group in sorted(self.dclgen_groups):
            block.append(f"{self.STATEMENT_INDENT}INITIALIZE {group}.")

        if self.PROGRAM_CONSTANT in joined:
            block.append(
                f"{self.STATEMENT_INDENT}MOVE {self.PROGRAM_CONSTANT}   "
                f"TO {self.PROGRAM_NAME_FIELD}."
            )
        if self.TIMESTAMP_PARAGRAPH_NAME in joined:
            block.append(
                f"{self.STATEMENT_INDENT}"
                f"PERFORM {self.TIMESTAMP_PARAGRAPH_NAME}."
            )

        block.append("")
        return block

    def _insert_initialize_paragraph(self, lines: List[str]) -> List[str]:
        """Insert the paragraph where it cannot absorb the mainline.

        The header goes immediately BEFORE the first named paragraph that
        follows the mainline. Placing it directly after PROCEDURE DIVISION
        renames an anonymous mainline, which is how the generated program
        ended up with STOP RUN inside 100-INITIALIZE.
        """
        if self._initialize_paragraph_exists(lines):
            return lines

        pd_index = self._procedure_division_index(lines)
        first_statement = self._first_statement_index(lines, pd_index)
        if first_statement < 0:
            return lines

        search_from = first_statement
        if self._is_paragraph_header(lines[first_statement]):
            search_from = first_statement + 1

        anchor = len(lines)
        for index in range(search_from, len(lines)):
            if self._is_paragraph_header(lines[index]):
                anchor = index
                break

        block = self._build_initialize_paragraph(lines)
        return lines[:anchor] + block + lines[anchor:]

    def _ensure_perform_initialize(self, lines: List[str]) -> List[str]:
        if self._perform_initialize_present(lines):
            return lines

        pd_index = self._procedure_division_index(lines)
        first_statement = self._first_statement_index(lines, pd_index)
        if first_statement < 0:
            return lines

        at = first_statement
        if self._is_paragraph_header(lines[first_statement]):
            at = first_statement + 1

        statement = (
            f"{self.STATEMENT_INDENT}PERFORM {self.INIT_PARAGRAPH_NAME}."
        )
        return lines[:at] + [statement] + lines[at:]

    # ------------------------------------------------------------------
    # Post-condition guards
    # ------------------------------------------------------------------

    def _initialize_paragraph_exists(self, lines: List[str]) -> bool:
        target = self.INIT_PARAGRAPH_NAME.upper()
        return any(
            self._is_paragraph_header(line)
            and self._paragraph_name(line) == target
            for line in lines
        )

    def _initialize_block_present(self, lines: List[str]) -> bool:
        bodies = {
            self._body(line).upper().rstrip(".")
            for line in lines
            if not self._is_comment_or_blank(line)
        }
        if not self._initialize_paragraph_exists(lines):
            return False
        return all(
            f"INITIALIZE {group}" in bodies for group in self.dclgen_groups
        )

    def _perform_initialize_present(self, lines: List[str]) -> bool:
        target = f"PERFORM {self.INIT_PARAGRAPH_NAME}".upper()
        return any(
            not self._is_comment_or_blank(line)
            and self._body(line).upper().rstrip(".").strip() == target
            for line in lines
        )

    # ------------------------------------------------------------------
    # Removal
    # ------------------------------------------------------------------

    def _remove_initialize_from_fetches(
        self, lines: List[str]
    ) -> List[str]:
        spans = self._fetch_paragraph_spans(lines)
        if not spans:
            return lines

        doomed: Set[int] = set()
        for start, end in spans:
            for index in range(start, end + 1):
                if self._is_comment_or_blank(lines[index]):
                    continue
                match = self.INITIALIZE_PATTERN.match(self._body(lines[index]))
                if match and match.group("group").upper() in self.dclgen_groups:
                    doomed.add(index)

        if not doomed:
            return lines

        self._note(
            f"removed {len(doomed)} fetch-prologue INITIALIZE statement(s)"
        )
        return [line for index, line in enumerate(lines) if index not in doomed]

    def _remove_standalone_initialize_block(
        self, lines: List[str]
    ) -> List[str]:
        """Drop a run of 2+ INITIALIZE lines sitting in the mainline.

        Scoped to the region between PROCEDURE DIVISION and the first
        paragraph header, which is the only place the inserted block can
        be. Running before creation guarantees the generated paragraph is
        never in scope.
        """
        pd_index = self._procedure_division_index(lines)
        if pd_index < 0:
            return lines

        limit = len(lines)
        for index in range(pd_index + 1, len(lines)):
            if self._is_paragraph_header(lines[index]):
                limit = index
                break

        doomed: Set[int] = set()
        run: List[int] = []
        for index in range(pd_index + 1, limit):
            if self._is_comment_or_blank(lines[index]):
                continue
            if self.INITIALIZE_PATTERN.match(self._body(lines[index])):
                run.append(index)
                continue
            if len(run) >= 2:
                doomed.update(run)
            run = []
        if len(run) >= 2:
            doomed.update(run)

        if not doomed:
            return lines

        self._note(
            f"removed standalone INITIALIZE block ({len(doomed)} line(s))"
        )
        return [line for index, line in enumerate(lines) if index not in doomed]

    # ------------------------------------------------------------------
    # Program-name constant
    # ------------------------------------------------------------------

    def _ensure_variable_program_name_move(
        self, lines: List[str]
    ) -> List[str]:
        """Replace MOVE 'literal' TO PROGRAM-NAME with the constant.

        Rewrites the BODY only and reuses the original record, so columns
        1-6 and 73-80 cannot be displaced. A whole-text re.sub was what
        previously contaminated the sequence areas and caused this step to
        be disabled.
        """
        bodies = "\n".join(
            self._body(line).upper()
            for line in lines
            if not self._is_comment_or_blank(line)
        )
        if self.PROGRAM_CONSTANT not in bodies:
            return lines

        canonical = (
            f"MOVE {self.PROGRAM_CONSTANT}   TO {self.PROGRAM_NAME_FIELD}."
        )
        output: List[str] = []
        rewritten = 0
        seen_canonical = False

        for line in lines:
            if self._is_comment_or_blank(line):
                output.append(line)
                continue

            body = self._body(line)
            if body.upper().rstrip(".") == canonical.upper().rstrip("."):
                if seen_canonical:
                    rewritten += 1
                    continue
                seen_canonical = True
                output.append(line)
                continue

            if not self.LITERAL_PROGRAM_MOVE_PATTERN.match(body):
                output.append(line)
                continue

            if seen_canonical:
                rewritten += 1
                continue

            seen_canonical = True
            rewritten += 1
            output.append(self._replace_body(line, canonical))

        if rewritten:
            self._note(
                f"replaced {rewritten} hardcoded PROGRAM-NAME move(s) "
                f"with {self.PROGRAM_CONSTANT}"
            )
        return output

    def _replace_body(self, line: str, body: str) -> str:
        text = str(line or "").rstrip("\r\n")
        if len(text) > self.BODY_START and text[:6].isdigit():
            left = text[:6]
            indicator = text[6:7] if text[6:7] in (" ", "D", "-") else " "
            right = text[self.BODY_END:self.LINE_WIDTH]
            width = self.BODY_END - self.BODY_START
            new_body = f"{self.STATEMENT_INDENT}{body}"[:width].ljust(width)
            return f"{left}{indicator}{new_body}{right}"
        return f"{self.STATEMENT_INDENT}{body}"

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _note(self, text: str) -> None:
        self.messages.append(f"Initialization: {text}")


def centralize_initialization(program_text: str) -> str:
    """Centralize all DCLGEN initialization in a program."""
    centralizer = InitializationCentralizer(program_text)
    return centralizer.process()
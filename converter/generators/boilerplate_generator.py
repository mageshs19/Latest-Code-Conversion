# LOCATION: converter/generators/boilerplate_generator.py
# ACTION: CREATE NEW FILE

from __future__ import annotations

import re

from converter.generators.db2_infrastructure.include_renderer import (
    IncludeRenderer,
)
from converter.services.cobol_area_alignment_service import (
    CobolAreaAlignmentService,
)
from rules.boilerplate_rules import (
    BOILERPLATE_DCLGEN_INCLUDES,
    BOILERPLATE_END_PROGRAM,
    BOILERPLATE_INCLUDE_INDENT,
    BOILERPLATE_MESSAGES,
)


class BoilerplateGenerator:
    """Adds final boilerplate: DCLGEN includes and END PROGRAM statement.
    
    This generator ensures:
    1. DCLGEN/SQLCA/SQLERRWS includes are present after WORKING-STORAGE
    2. END PROGRAM statement is added at the end of the program
    
    Both are added according to site standards for DB2 COBOL programs.
    """

    WORKING_STORAGE_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?WORKING-STORAGE\s+SECTION\.\s*(?:\d{8})?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    PROCEDURE_DIVISION_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?PROCEDURE\s+DIVISION\b.*\.?\s*(?:\d{8})?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    END_PROGRAM_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?END\s+PROGRAM\b.*\.?\s*(?:\d{8})?\s*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )

    STOP_RUN_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?STOP\s+RUN\.?\s*(?:\d{8})?\s*$",
        flags=re.IGNORECASE,
    )

    EXEC_SQL_INCLUDE_PATTERN = re.compile(
        r"^\s*EXEC\s+SQL\s+INCLUDE\s+\w+\s+END-EXEC",
        flags=re.IGNORECASE,
    )

    def __init__(
        self,
        line_utils=None,
    ) -> None:
        self.line_utils = line_utils or CobolAreaAlignmentService()
        self.messages: list[str] = []

    def apply(
        self,
        cobol_text: str,
        operations: list | None = None,
    ) -> tuple[str, list[str]]:
        """Apply boilerplate enhancements to COBOL text."""
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        # Add DCLGEN/SQLCA/SQLERRWS includes after WORKING-STORAGE
        text = self._ensure_dclgen_includes(text)

        # Add END PROGRAM before end of file
        text = self._ensure_end_program(text)

        return text.rstrip() + "\n", self.messages

    def _ensure_dclgen_includes(self, text: str) -> str:
        """Ensure DCLGEN and DB2 infrastructure includes are present."""
        lines = text.splitlines()

        # Find WORKING-STORAGE SECTION
        ws_index = self._find_pattern_index(
            lines=lines,
            pattern=self.WORKING_STORAGE_PATTERN,
        )

        if ws_index < 0:
            self.messages.append(
                BOILERPLATE_MESSAGES["no_working_storage"]
            )
            return text

        # Find PROCEDURE DIVISION
        pd_index = self._find_pattern_index(
            lines=lines,
            pattern=self.PROCEDURE_DIVISION_PATTERN,
        )

        if pd_index < 0:
            self.messages.append(
                BOILERPLATE_MESSAGES["no_procedure_division"]
            )
            return text

        # Check if includes already exist between WS and PD
        includes_exist = self._includes_exist(lines, ws_index, pd_index)
        if includes_exist:
            self.messages.append(
                BOILERPLATE_MESSAGES["includes_exist"]
            )
            return text

        # Find insertion point (just before PROCEDURE DIVISION)
        insert_index = pd_index

        # Build include block
        include_lines = self._build_include_block()

        # Insert includes
        updated_lines = (
            lines[:insert_index]
            + [""]
            + include_lines
            + [""]
            + lines[insert_index:]
        )

        self.messages.append(
            BOILERPLATE_MESSAGES["includes_added"].format(
                count=len(include_lines)
            )
        )

        return "\n".join(updated_lines)

    def _ensure_end_program(self, text: str) -> str:
        """Ensure END PROGRAM statement is present at end of program."""
        lines = text.splitlines()

        # Check if END PROGRAM already exists
        for line in lines:
            logical = self._logical_line(line)
            if self.END_PROGRAM_PATTERN.match(logical):
                self.messages.append(
                    BOILERPLATE_MESSAGES["end_program_exists"]
                )
                return text

        # Add END PROGRAM before last line (usually blank)
        if lines and not lines[-1].strip():
            # Last line is blank, insert before it
            updated_lines = lines[:-1] + [BOILERPLATE_END_PROGRAM, ""]
        else:
            # No blank line at end, just append
            updated_lines = lines + ["", BOILERPLATE_END_PROGRAM]

        self.messages.append(BOILERPLATE_MESSAGES["end_program_added"])

        return "\n".join(updated_lines)

    def _includes_exist(
        self,
        lines: list[str],
        start_index: int,
        end_index: int,
    ) -> bool:
        """Check if EXEC SQL INCLUDE statements exist in range."""
        for i in range(start_index, min(end_index, len(lines))):
            logical = self._logical_line(lines[i])
            if self.EXEC_SQL_INCLUDE_PATTERN.match(logical):
                return True
        return False

    def _build_include_block(self) -> list[str]:
        """Build the DCLGEN include block lines."""
        includes = []

        for include_name in BOILERPLATE_DCLGEN_INCLUDES:
            line = (
                BOILERPLATE_INCLUDE_INDENT
                + f"EXEC SQL INCLUDE {include_name} END-EXEC."
            )
            includes.append(line)

        return includes

    def _find_pattern_index(
        self,
        lines: list[str],
        pattern: re.Pattern,
    ) -> int:
        """Find the first line matching the pattern."""
        for index, line in enumerate(lines):
            logical = self._logical_line(line)
            if pattern.match(logical):
                return index
        return -1

    def _logical_line(self, line: str) -> str:
        """Extract logical COBOL line (remove sequence area)."""
        text = str(line or "").rstrip()

        # Remove COBOL sequence area (first 6 chars)
        if len(text) > 6 and text[:6].strip().isdigit():
            return text[6:].strip()

        return text.strip()


__all__ = ["BoilerplateGenerator"]

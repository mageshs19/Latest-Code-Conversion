# LOCATION: src/idms_db2_phase2/generators/restart_infrastructure_fixer.py
# PURPOSE: Fix remaining restart infrastructure issues: legacy SQLCODE, SQL-LOCATION

from __future__ import annotations

import re
from typing import Optional


class RestartInfrastructureFixer:
    """Fixes remaining restart infrastructure issues in COBOL programs.
    
    This fixer addresses:
    - Legacy SQLCODE tests (IF NOT SQLCODE = 100 -> EVALUATE SQLCODE)
    - Missing SQL-LOCATION before retrieval SELECTs
    - Adds stub control paragraph comments
    """

    # Pattern for legacy SQLCODE IF tests
    LEGACY_SQLCODE_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?IF\s+NOT\s+SQLCODE\s*=\s*100",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Pattern for SELECT statements without preceding SQL-LOCATION
    SELECT_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?EXEC\s+SQL\s*\n\s*(?:\d{6}\s+)?SELECT",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Pattern for WHERE clauses in non-restart SELECTs
    WHERE_PATTERN = re.compile(
        r"WHERE\s+(\w+)\s*=",
        flags=re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.messages: list[str] = []

    def apply(
        self,
        cobol_text: str,
        program_id: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        """Apply restart infrastructure fixes to COBOL text.
        
        Args:
            cobol_text: COBOL program source
            program_id: Program identifier
            
        Returns:
            tuple: (modified_cobol_text, messages)
        """
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        # Apply fixes
        text = self._fix_legacy_sqlcode(text)
        text = self._add_sql_location_before_retrieval(text)
        text = self._add_restart_control_hints(text, program_id)

        return text, self.messages

    def _fix_legacy_sqlcode(self, text: str) -> str:
        """Convert legacy IF NOT SQLCODE = 100 to EVALUATE SQLCODE."""
        lines = text.split("\n")
        result_lines = []
        i = 0
        modified = False
        
        while i < len(lines):
            line = lines[i]
            
            # Check for legacy pattern: IF NOT SQLCODE = 100
            if re.search(r"^\s*(?:\d{6}\s+)?IF\s+NOT\s+SQLCODE\s*=\s*100", line, re.IGNORECASE):
                # Found legacy pattern - convert it
                # Pattern is:
                #     IF NOT SQLCODE = 100
                #        ... display/call block ...
                #     END-IF.
                
                # Extract indentation
                indent_match = re.match(r"^(\s*)(?:\d{6}\s+)?", line)
                indent = indent_match.group(1) if indent_match else "    "
                cobol_indent = " " * max(len(indent), 12)
                
                # Start EVALUATE block
                result_lines.append(f"{cobol_indent}EVALUATE SQLCODE")
                result_lines.append(f"{cobol_indent}    WHEN 0")
                result_lines.append(f"{cobol_indent}        CONTINUE")
                result_lines.append(f"{cobol_indent}    WHEN 100")
                result_lines.append(f"{cobol_indent}        CONTINUE")
                result_lines.append(f"{cobol_indent}    WHEN OTHER")
                
                # Copy the body (DISPLAY/CALL statements until END-IF)
                i += 1
                while i < len(lines):
                    body_line = lines[i]
                    
                    if re.search(r"END-IF", body_line, re.IGNORECASE):
                        # End of IF block
                        result_lines.append(f"{cobol_indent}        PERFORM SQLERROR")
                        result_lines.append(f"{cobol_indent}END-EVALUATE")
                        modified = True
                        break
                    else:
                        # Include body lines - strip sequence numbers from columns 1-6
                        if body_line.strip():
                            # Remove sequence number (first 6 characters if they look like a number)
                            cleaned_line = body_line
                            if len(cleaned_line) > 6:
                                first_six = cleaned_line[:6]
                                if first_six.strip() and first_six.strip().isdigit():
                                    # This looks like a sequence number - remove it
                                    cleaned_line = cleaned_line[6:]
                                    # Ensure at least column 7 is a space for fixed format
                                    if not cleaned_line.startswith(' '):
                                        cleaned_line = ' ' + cleaned_line
                            
                            result_lines.append(f"{cobol_indent}        {cleaned_line.strip()}")
                        else:
                            result_lines.append(body_line)
                    
                    i += 1
                
                self.messages.append(
                    f"Line {i+1}: Converted legacy 'IF NOT SQLCODE = 100' to EVALUATE SQLCODE"
                )
            else:
                result_lines.append(line)
            
            i += 1
        
        return "\n".join(result_lines)

    def _add_sql_location_before_retrieval(self, text: str) -> str:
        """Add SQL-LOCATION MOVE before retrieval SELECTs that lack it."""
        lines = text.split("\n")
        result_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this is an EXEC SQL line
            if re.search(r"EXEC\s+SQL", line, re.IGNORECASE):
                # Look ahead for SELECT keyword
                j = i + 1
                found_select = False
                select_line_num = -1
                
                while j < len(lines) and j < i + 5:
                    if re.search(r"^\s*(?:\d{6}\s+)?SELECT", lines[j], re.IGNORECASE):
                        found_select = True
                        select_line_num = j
                        break
                    j += 1
                
                if found_select:
                    # Check if this is NOT a restart SELECT (700-, 211-, 221-)
                    if not self._is_restart_select(line):
                        # Check if there's a SQL-LOCATION MOVE in the previous lines
                        has_sql_location = False
                        for k in range(max(0, i - 3), i):
                            if re.search(
                                r"MOVE\s+['\"].*['\"].*TO\s+SQL-LOCATION",
                                lines[k],
                                re.IGNORECASE,
                            ):
                                has_sql_location = True
                                break
                        
                        # If no SQL-LOCATION found, add it
                        if not has_sql_location:
                            # Extract indentation from EXEC SQL line
                            indent_match = re.match(r"^(\s*)(?:\d{6}\s+)?", line)
                            indent = indent_match.group(1) if indent_match else "    "
                            cobol_indent = " " * max(len(indent), 12)
                            
                            # Add SQL-LOCATION MOVE
                            sql_location_move = f"{cobol_indent}MOVE 'RETRIEVAL-SELECT' TO SQL-LOCATION."
                            result_lines.append(sql_location_move)
                            self.messages.append(
                                f"Line {i+1}: Added SQL-LOCATION before retrieval SELECT"
                            )
            
            result_lines.append(line)
            i += 1
        
        return "\n".join(result_lines)

    def _add_restart_control_hints(self, text: str, program_id: Optional[str]) -> str:
        """Add comments about missing restart control paragraphs."""
        if program_id not in ["VMDZ1526", "VMDZ1567"]:
            return text
        
        # Check if control paragraphs are present
        has_restart_control = "700-RESTART-CONTROL" in text or "800-RESTART-CONTROL" in text
        has_job_is_restart = "810-JOB-IS-RESTART" in text
        has_write_restart = "820-WRITE-RESTART-REC" in text or "720-WRITE-RESTART-REC" in text
        has_process_commit = "800-PROCESS-COMMIT" in text or "830-PROCESS-COMMIT" in text
        has_call_useraben = "810000-CALL-USERABEN" in text or "850-CALL-USERABEN" in text
        
        if not all([has_restart_control, has_job_is_restart, has_write_restart]):
            self.messages.append(
                f"{program_id}: CRITICAL - Missing restart control paragraph structure. "
                f"Needs: 800-RESTART-CONTROL, 810-JOB-IS-RESTART, 820-WRITE-RESTART-REC"
            )
        
        return text

    def _is_restart_select(self, line: str) -> bool:
        """Check if this is a restart SELECT (700- prefix)."""
        return bool(re.search(r"700-SELECT", line, re.IGNORECASE))

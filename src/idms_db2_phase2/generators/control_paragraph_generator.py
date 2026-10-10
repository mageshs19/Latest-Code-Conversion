# LOCATION: src/idms_db2_phase2/generators/control_paragraph_generator.py
# PURPOSE: Generate standard COBOL restart control paragraphs (800, 820, 830)

from __future__ import annotations

import re
from typing import Optional


class ControlParagraphGenerator:
    """Generates standard COBOL restart control paragraphs.
    
    This generator creates:
    - 800-RESTART-CONTROL: Initialize restart table and branch on SELECT result
    - 820-WRITE-RESTART-REC: Create new restart record for first run
    - 830-PROCESS-COMMIT: Update restart record and commit after processing
    - 810-JOB-IS-RESTART: Template (requires manual implementation)
    
    Pattern: These paragraphs implement standard mainframe restart/recovery logic
    found in DB2 programs that need to resume from checkpoints.
    """

    def __init__(self) -> None:
        self.messages: list[str] = []

    def apply(
        self,
        cobol_text: str,
        program_id: Optional[str] = None,
    ) -> tuple[str, list[str]]:
        """Generate control paragraphs if missing.
        
        Args:
            cobol_text: COBOL program source
            program_id: Program identifier (VMDZ1526, VMDZ1567, etc.)
            
        Returns:
            tuple: (modified_cobol_text, messages)
        """
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        # Detect program type
        program_id = program_id or self._detect_program_id(text)

        # Only generate for UPDATE programs
        if program_id in ["VMDZ1526", "VMDZ1567"]:
            text = self._generate_control_paragraphs(text, program_id)
        else:
            self.messages.append(f"{program_id}: Not an UPDATE program, skipping control paragraphs")

        return text, self.messages

    def _detect_program_id(self, cobol_text: str) -> str:
        """Detect program ID from COBOL source."""
        match = re.search(
            r"PROGRAM-ID\.\s+(\w+)",
            cobol_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return match.group(1) if match else "UNKNOWN"

    def _generate_control_paragraphs(self, text: str, program_id: str) -> str:
        """Generate 800, 820, 830 control paragraphs."""
        # Check if paragraphs already exist
        if self._paragraph_exists(text, "800-RESTART-CONTROL"):
            self.messages.append(f"{program_id}: 800-RESTART-CONTROL already present")
            return text

        # Extract program variables
        cs_program = self._find_program_identifier(text, program_id)
        date_field = self._find_date_field(text)
        eof_flag = self._find_eof_flag(text)
        counter_var = self._find_counter_variable(text)

        # Find insertion point (before STOP RUN or END PROGRAM)
        insertion_point = self._find_insertion_point(text)

        if insertion_point == -1:
            self.messages.append(f"{program_id}: Could not find insertion point for control paragraphs")
            return text

        # Generate the three paragraphs
        paragraphs = []
        
        # Generate 800-RESTART-CONTROL
        paragraphs.append(self._build_800_restart_control(cs_program, date_field))
        
        # Generate 810-JOB-IS-RESTART (template)
        paragraphs.append(self._build_810_job_is_restart())
        
        # Generate 820-WRITE-RESTART-REC
        paragraphs.append(self._build_820_write_restart_rec())
        
        # Generate 830-PROCESS-COMMIT
        paragraphs.append(self._build_830_process_commit(eof_flag, counter_var))

        # Insert into text
        new_paragraph = "\n" + "\n".join(paragraphs)
        text = text[:insertion_point] + new_paragraph + text[insertion_point:]

        self.messages.append(f"{program_id}: Generated 4 control paragraphs (800, 810, 820, 830)")
        self.messages.append(f"  - 800-RESTART-CONTROL: Initialize and SELECT")
        self.messages.append(f"  - 810-JOB-IS-RESTART: Template (requires manual logic)")
        self.messages.append(f"  - 820-WRITE-RESTART-REC: Create new restart record")
        self.messages.append(f"  - 830-PROCESS-COMMIT: Update and commit")

        return text

    def _paragraph_exists(self, text: str, paragraph_name: str) -> bool:
        """Check if paragraph already exists."""
        pattern = re.compile(
            rf"^\s*(?:\d{{6}}\s+)?{re.escape(paragraph_name)}\.",
            flags=re.MULTILINE | re.IGNORECASE,
        )
        return bool(pattern.search(text))

    def _find_program_identifier(self, text: str, program_id: str) -> str:
        """Find program identifier variable (CS-PROGRAM or constant)."""
        # Look for CS-PROGRAM definition
        if re.search(r"CS-PROGRAM.*VALUE\s+['\"].*['\"]", text, re.IGNORECASE):
            return "CS-PROGRAM"
        # Fallback to program ID
        return f"'{program_id}'"

    def _find_date_field(self, text: str) -> str:
        """Find date field in working storage."""
        # Common patterns: DA-DD-MM-CCYY, DATE-FIELD, etc.
        patterns = [
            r"DA-DD-MM-CCYY",
            r"DA-CR-RS",
            r"WS-.*DATE",
            r"DATE-\w+",
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return "WS-CURRENT-DATE"

    def _find_eof_flag(self, text: str) -> str:
        """Find EOF flag in working storage."""
        # Common patterns: VMDZ205I-EOF, EOF-FLAG, etc.
        patterns = [
            r"VMDZ205I-EOF",
            r"\w+-EOF",
            r"EOF-\w+",
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return "WS-EOF-FLAG"

    def _find_counter_variable(self, text: str) -> str:
        """Find input counter variable."""
        # Common patterns: WS-NB-INPUT-UPD-I, NB-INPUT, etc.
        if re.search(r"WS-NB-INPUT-UPD-I", text, re.IGNORECASE):
            return "WS-NB-INPUT-UPD-I"
        
        patterns = [
            r"WS-\w*INPUT\w*",
            r"WS-\w*COUNTER\w*",
        ]
        
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(0)
        
        return "WS-RECORD-COUNT"

    def _find_insertion_point(self, text: str) -> int:
        """Find where to insert control paragraphs."""
        # Look for STOP RUN or END PROGRAM
        for pattern in [r"STOP\s+RUN", r"END\s+PROGRAM"]:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Insert before this line
                return match.start()
        
        # Fallback: insert at end of file
        return len(text)

    def _build_800_restart_control(self, cs_program: str, date_field: str) -> str:
        """Build 800-RESTART-CONTROL paragraph."""
        return f"""        800-RESTART-CONTROL.
            MOVE {cs_program}      TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.
            MOVE {date_field}   TO DA-CR-RS         OF DCLDZ01RSTV.
            MOVE 1               TO NB-ID-RS-PHASE   OF DCLDZ01RSTV.

            PERFORM 700-SELECT-DZ01RSTV.

            EVALUATE SQLCODE
                WHEN 0
                    PERFORM 810-JOB-IS-RESTART
                WHEN 100
                    PERFORM 820-WRITE-RESTART-REC
                WHEN OTHER
                    PERFORM SQLERROR
            END-EVALUATE
            ."""

    def _build_810_job_is_restart(self) -> str:
        """Build 810-JOB-IS-RESTART paragraph (template)."""
        return """        810-JOB-IS-RESTART.
            *> Restart record located. Inspect the completion flag to
            *> determine whether the previous run finished cleanly or was
            *> interrupted, then resume processing from the stored point.
            IF CO-ID-RS IN DCLDZ01RSTV = '1'
                PERFORM SQLERROR
            ELSE
                MOVE 1 TO NB-ID-RS-PHASE OF DCLDZ01RSTV
            END-IF
            ."""

    def _build_820_write_restart_rec(self) -> str:
        """Build 820-WRITE-RESTART-REC paragraph."""
        return """        820-WRITE-RESTART-REC.
            MOVE '0'                TO CO-ID-RS           IN DCLDZ01RSTV.
            MOVE 15                 TO NB-DAY-RS          IN DCLDZ01RSTV.
            MOVE 1215               TO TE-CH-RS-DATA-LEN  IN DCLDZ01RSTV.
            MOVE 0                  TO WS-NB-INPUT-UPD-I.
            MOVE WS-NB-INPUT-UPD-I  TO NB-READ OF WS-RESTART-REC.
            INITIALIZE  KY-RESTART.
            MOVE WS-RESTART-REC     TO TE-CH-RS-DATA-TEXT IN DCLDZ01RSTV.
            PERFORM 700-INSERT-DZ01RSTV
            ."""

    def _build_830_process_commit(self, eof_flag: str, counter_var: str) -> str:
        """Build 830-PROCESS-COMMIT paragraph."""
        return f"""        830-PROCESS-COMMIT.
            MOVE 0                  TO TELLER.
            MOVE {counter_var}  TO NB-READ.
            MOVE WS-RESTART-REC     TO KY-RESTART.

            IF   {eof_flag}
            THEN MOVE '1'           TO CO-ID-RS  OF DCLDZ01RSTV
            ELSE MOVE '0'           TO CO-ID-RS  OF DCLDZ01RSTV
            END-IF.

            MOVE 15                 TO TE-CH-RS-DATA-LEN.
            MOVE WS-RESTART-REC     TO TE-CH-RS-DATA-TEXT.

            PERFORM 700-UPDATE-DZ01RSTV.

            MOVE 'COMMIT' TO SQL-LOCATION.
            EXEC SQL
                COMMIT
            END-EXEC
            ."""

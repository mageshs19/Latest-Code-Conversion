# LOCATION: converter/generators/select_paragraph_generator.py

from __future__ import annotations

import re
from typing import Optional

from converter.services.cobol_area_alignment_service import (
    CobolAreaAlignmentService,
)


class SelectParagraphGenerator:
    """Generates complete UPDATE program infrastructure for DB2 migration.
    
    Generates for UPDATE programs (VMDZ1526, VMDZ1567):
    - Working storage: date structures, switches, counters, restart record
    - DB2 infrastructure: INCLUDE statements, SQLCA
    - Timestamp structures: system and formatted timestamps
    - Restart logic: control paragraph, SQL paragraphs
    - Handler paragraphs: restart found, first run, commit
    - Main procedure integration: proper flow with file I/O
    """

    PARAGRAPH_PATTERN = re.compile(
        r"^\s{0,11}(\d{3}|70\d|2\d{2}|8\d{2})-[\w\-]+\.\s*(?:\d{8})?\s*$",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    STOP_RUN_PATTERN = re.compile(
        r"^(\s*(?:\d{6}\s+)?STOP\s+RUN\.?\s*(?:\d{8})?\s*)$",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    RESTART_CONTROL_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?700-RESTART-CONTROL\.",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    JOB_IS_RESTART_PATTERN = re.compile(
        r"^\s*(?:\d{6}\s+)?810-JOB-IS-RESTART\.",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    def __init__(self, line_utils=None) -> None:
        self.line_utils = line_utils or CobolAreaAlignmentService()
        self.messages: list[str] = []

    def apply(
        self,
        cobol_text: str,
        program_id: Optional[str] = None,
        operations: list | None = None,
    ) -> tuple[str, list[str]]:
        """Generate complete UPDATE program infrastructure."""
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        program_id = program_id or self._detect_program_id(text)

        if program_id in ["VMDZ1526", "VMDZ1567"]:
            # Phase 1: Working Storage enhancements with HELP-VARIABLE structure
            # This adds the exact checkpoint and working variable hierarchy from manual
            text = self._ensure_working_storage_structures(text, program_id)
            
            # Phase 2: DB2 infrastructure
            # CRITICAL: db2_infrastructure_generator.apply() has ALREADY added infrastructure
            # in the main conversion pipeline, so skip this phase to avoid duplicates.
            # Only ensure timestamp structures if missing.
            text = self._ensure_only_timestamps(text, program_id)
            
            # Phase 3: Restart infrastructure
            text = self._ensure_restart_paragraphs(text, program_id)
            
            # Phase 4: Handler and utility paragraphs
            text = self._ensure_handler_paragraphs(text, program_id)
            
            # Phase 4.5: CRITICAL - Add audit field MOVEs before MODIFY comment in VERWERKING
            text = self._add_audit_field_moves_in_verwerking(text, program_id)
            
            # Phase 5: Procedure division integration
            text = self._fix_procedure_division(text, program_id)

        return text, self.messages

    # ========== HELPER METHODS ==========

    def _detect_program_id(self, cobol_text: str) -> str:
        """Extract PROGRAM-ID from COBOL source."""
        match = re.search(
            r"PROGRAM-ID\.\s+(\w+)",
            cobol_text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return match.group(1) if match else "UNKNOWN"

    def _find_working_storage_section(self, text: str) -> tuple[int, int]:
        """Find WORKING-STORAGE SECTION start and first 01-level item.
        
        CRITICAL: Must search ONLY within WORKING-STORAGE SECTION, not FILE SECTION.
        Return the position after "WORKING-STORAGE SECTION." and before first 01-level.
        """
        ws_match = re.search(
            r"WORKING-STORAGE\s+SECTION\.",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if not ws_match:
            return -1, -1

        ws_start = ws_match.start()
        ws_end = ws_match.end()
        
        # Find NEXT section marker to bound our search
        # (LINKAGE SECTION or PROCEDURE DIVISION)
        next_section = re.search(
            r"(?:LINKAGE|PROCEDURE)\s+(?:SECTION|DIVISION)",
            text[ws_end:],
            flags=re.IGNORECASE | re.MULTILINE,
        )
        
        search_text = text[ws_end:]
        if next_section:
            search_text = text[ws_end:ws_end + next_section.start()]
        
        # Find first 01-level ONLY within WORKING-STORAGE SECTION
        first_01_match = re.search(
            r"^\s*(?:\d{6}\s+)?01\s+",
            search_text,
            flags=re.MULTILINE | re.IGNORECASE,
        )
        
        first_01_pos = ws_end + first_01_match.start() if first_01_match else -1
        return ws_start, first_01_pos

    def _find_procedure_division_start(self, text: str) -> int:
        """Find PROCEDURE DIVISION start."""
        match = re.search(
            r"PROCEDURE\s+DIVISION\b",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return match.start() if match else -1

    def _find_stop_run(self, text: str) -> int:
        """Find STOP RUN position."""
        match = self.STOP_RUN_PATTERN.search(text)
        return match.start() if match else -1

    # ========== PHASE 1: WORKING STORAGE ==========

    def _ensure_working_storage_structures(self, text: str, program_id: str) -> str:
        """Add missing working storage structures to WORKING-STORAGE SECTION.
        
        CRITICAL FIX: If WORKING-STORAGE SECTION doesn't exist, create it before
        inserting structures. Otherwise structures end up in FILE SECTION (wrong).
        """
        if "WS-SWITCHES" in text:
            return text

        ws_start, first_01_pos = self._find_working_storage_section(text)
        
        # If WORKING-STORAGE SECTION doesn't exist yet, create it before FILE SECTION
        if ws_start == -1:
            # Find FILE SECTION
            file_section_pos = text.find("FILE SECTION")
            if file_section_pos == -1:
                self.messages.append(f"{program_id}: Neither WORKING-STORAGE nor FILE SECTION found")
                return text
            
            # Insert WORKING-STORAGE SECTION before FILE SECTION
            ws_section = "\n\nWORKING-STORAGE SECTION.\n"
            structures = self._build_working_storage_structures()
            text = text[:file_section_pos] + ws_section + structures + text[file_section_pos:]
            self.messages.append("Created WORKING-STORAGE SECTION and added structures")
            return text
        
        # WORKING-STORAGE SECTION exists, insert at first 01-level position
        if first_01_pos == -1:
            self.messages.append(f"{program_id}: WORKING-STORAGE SECTION found but no 01-level item")
            return text

        structures = self._build_working_storage_structures()
        text = text[:first_01_pos] + structures + text[first_01_pos:]
        self.messages.append("Added WS-SWITCHES, WS-RESTART-REC, and counters to WORKING-STORAGE")

        return text

    def _build_working_storage_structures(self) -> str:
        """Build complete working storage structures under HELP-VARIABLE group.
        
        Structure matches manual VMDZ1567 pattern:
        - HELP-VARIABLE (parent group for checkpoint and working variables)
          - WS-RESTART-REC (checkpoint: record number + last key)
          - WS-INPUT-KASBONS (input record buffer)
          - WS-TELLER (commit frequency counter)
          - WS-NB-INPUT-UPD-I (records processed counter)
          - WS-NB-BFAR-UPD-I (updates applied counter)
        """
        return """01 WS-SWITCHES.
     02  SW-EOF                     PIC X       VALUE 'N'.
         88  NOT-EOF                VALUE 'N'.
         88  EOF                    VALUE 'Y'.
     02  WS-RECORD-FOUND            PIC X       VALUE 'N'.
         88  RESTART-FOUND          VALUE 'Y'.
         88  RESTART-NOT-FOUND      VALUE 'N'.

01  HELP-VARIABLE.
     02  WS-RESTART-REC.
         03  NB-READ                PIC 9(15)   VALUE ZERO.
         03  KY-RESTART             PIC X(1200) VALUE SPACES.

     02  WS-INPUT-KASBONS           PIC X(1200) VALUE SPACES.
     02  WS-TELLER                  PIC 9(9)   COMP-3 VALUE ZERO.
     02  WS-NB-INPUT-UPD-I          PIC 9(7)   COMP-3 VALUE ZERO.
     02  WS-NB-BFAR-UPD-I           PIC S9(11) COMP-3 VALUE +0.

01  WS-DATE-CONVERSION.
     03  DA-YYMMDD.
         05  YY                     PIC 99            VALUE ZERO.
         05  MM                     PIC 99            VALUE ZERO.
         05  DD                     PIC 99            VALUE ZERO.
     03  DA-DDMMCCYY.
         05  DD                     PIC 99            VALUE ZERO.
         05  MM                     PIC 99            VALUE ZERO.
         05  CC                     PIC 99            VALUE ZERO.
         05  YY                     PIC 99            VALUE ZERO.
     03  DA-CCYYMMDD.
         05  CC                     PIC 99            VALUE ZERO.
         05  YY                     PIC 99            VALUE ZERO.
         05  MM                     PIC 99            VALUE ZERO.
         05  DD                     PIC 99            VALUE ZERO.
     03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.
         05  CCYY                   PIC 9999.
         05  MM                     PIC 99.
         05  DD                     PIC 99.
     03  DA-DD-MM-CCYY.
         05  DD                     PIC 9(02).
         05  TE-MARKER1             PIC X             VALUE '.'.
         05  MM                     PIC 9(02).
         05  TE-MARKER2             PIC X             VALUE '.'.
         05  CCYY                   PIC 9(04).

"""

    # ========== PHASE 2: DB2 INFRASTRUCTURE ==========

    def _ensure_only_timestamps(self, text: str, program_id: str) -> str:
        """Ensure timestamp structures and DZ01RSTV for UPDATE programs.
        
        Note: db2_infrastructure_generator has already added SQLERRWS, SQLCA,
        and operation-specific DCLGENs. This method ensures:
        1. Timestamp structures (WS-TIMESTAMP-FIELDS)
        2. DZ01RSTV include for restart table (if missing)
        """
        has_ts_fields = "WS-TIMESTAMP-FIELDS" in text
        has_dz01 = "INCLUDE DZ01RSTV" in text

        # Check if we need to add anything
        if has_ts_fields and has_dz01:
            return text

        # Find insertion point before FILE SECTION or WORKING-STORAGE
        insert_pos = self._find_db2_insert_point(text)
        if insert_pos == -1:
            self.messages.append(f"{program_id}: Could not find insert point for timestamps/DZ01RSTV")
            return text

        components = []

        # Add DZ01RSTV include if missing (restart table for UPDATE programs)
        if not has_dz01:
            components.append("     EXEC SQL INCLUDE DZ01RSTV END-EXEC.")

        # Add timestamp structures if missing
        if not has_ts_fields:
            components.append(self._build_timestamp_structures())

        if not components:
            return text

        new_content = "\n".join(components)
        text = text[:insert_pos] + new_content + text[insert_pos:]
        
        messages = []
        if not has_dz01:
            messages.append("Added DZ01RSTV restart table include")
        if not has_ts_fields:
            messages.append("Added DB2 timestamp structures")
        
        self.messages.append("; ".join(messages))

        return text

    def _ensure_db2_infrastructure(self, text: str, program_id: str) -> str:
        """Ensure DB2 infrastructure (SQLCA, includes, timestamps)."""
        has_sqlca = "INCLUDE SQLCA" in text
        has_dz01 = "INCLUDE DZ01RSTV" in text
        has_ts_fields = "WS-TIMESTAMP-FIELDS" in text

        if has_sqlca and has_dz01 and has_ts_fields:
            return text

        # Find insertion point before FILE SECTION or WORKING-STORAGE
        insert_pos = self._find_db2_insert_point(text)
        if insert_pos == -1:
            self.messages.append(f"{program_id}: Could not find DB2 insert point")
            return text

        components = []

        if not has_sqlca or not has_dz01:
            components.append(self._build_db2_includes())

        if not has_ts_fields:
            components.append(self._build_timestamp_structures())

        new_content = "\n".join(components)
        text = text[:insert_pos] + new_content + text[insert_pos:]
        self.messages.append("Added DB2 infrastructure (SQLCA, includes, timestamps)")

        return text

    def _find_db2_insert_point(self, text: str) -> int:
        """Find insertion point for DB2 infrastructure."""
        # Look for COPY or EXEC SQL INCLUDE statements
        match = re.search(
            r"(?:COPY|EXEC\s+SQL\s+INCLUDE)\s+\w+",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if match:
            # Find end of line
            line_end = text.find("\n", match.end())
            return line_end + 1 if line_end != -1 else match.end()

        # Fall back to before LINKAGE SECTION
        match = re.search(
            r"LINKAGE\s+SECTION\.",
            text,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        return match.start() if match else -1

    def _build_db2_includes(self) -> str:
        """Build DB2 infrastructure includes."""
        return """*DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS
     EXEC SQL INCLUDE SQLERRWS END-EXEC.
     EXEC SQL INCLUDE SQLCA END-EXEC.
     EXEC SQL INCLUDE DZBFARTV END-EXEC.
     EXEC SQL INCLUDE DZ01RSTV END-EXEC.

"""

    def _build_timestamp_structures(self) -> str:
        """Build timestamp working storage structures."""
        return """*DB2 TIMESTAMP AND AUDIT FIELDS
 77  CS-PROGRAM                 PIC X(8) VALUE 'VMDZ1567'.
 01 WS-TIMESTAMP-FIELDS.
     05 TS-SYSTEM.
        10  CC                  PIC X(2).
        10  YY                  PIC X(2).
        10  MM                  PIC X(2).
        10  DD                  PIC X(2).
        10  HH                  PIC X(2).
        10  MI                  PIC X(2).
        10  SS                  PIC X(2).
        10  TT                  PIC X(2).
        10  FILLER              PIC X(13).
     05 TS-TIMESTAMP.
        10  CC                  PIC X(2).
        10  YY                  PIC X(2).
        10  TE-MARKER1          PIC X    VALUE '-'.
        10  MM                  PIC X(2).
        10  TE-MARKER2          PIC X    VALUE '-'.
        10  DD                  PIC X(2).
        10  TE-MARKER3          PIC X    VALUE '-'.
        10  HH                  PIC X(2).
        10  TE-MARKER4          PIC X    VALUE '.'.
        10  MI                  PIC X(2).
        10  TE-MARKER5          PIC X    VALUE '.'.
        10  SS                  PIC X(2).
        10  TE-MARKER6          PIC X    VALUE '.'.
        10  TT                  PIC X(2).
        10  NNNN                PIC 9(04) VALUE 0.

"""

    # ========== PHASE 3: RESTART PARAGRAPHS ==========

    def _ensure_restart_paragraphs(self, text: str, program_id: str) -> str:
        """Generate all restart-related SQL paragraphs."""
        missing = []

        if not self.RESTART_CONTROL_PATTERN.search(text):
            missing.append("700-RESTART-CONTROL")
        if not re.search(r"^\s*(?:\d{6}\s+)?700-SELECT-DZ01RSTV\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("700-SELECT-DZ01RSTV")
        if not re.search(r"^\s*(?:\d{6}\s+)?700-UPDATE-DZ01RSTV\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("700-UPDATE-DZ01RSTV")
        if not re.search(r"^\s*(?:\d{6}\s+)?700-INSERT-DZ01RSTV\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("700-INSERT-DZ01RSTV")

        if not missing:
            return text

        insert_pos = self._find_stop_run(text)
        if insert_pos == -1:
            self.messages.append(f"{program_id}: STOP RUN not found")
            return text

        paragraphs = []
        for para in missing:
            if para == "700-RESTART-CONTROL":
                paragraphs.append(self._build_700_restart_control())
            elif para == "700-SELECT-DZ01RSTV":
                paragraphs.append(self._build_700_select_dz01rstv())
            elif para == "700-UPDATE-DZ01RSTV":
                paragraphs.append(self._build_700_update_dz01rstv())
            elif para == "700-INSERT-DZ01RSTV":
                paragraphs.append(self._build_700_insert_dz01rstv())

        new_content = "\n".join(paragraphs)
        text = text[:insert_pos] + new_content + text[insert_pos:]

        for para in missing:
            self.messages.append(f"Added {para}")

        return text

    def _build_700_restart_control(self) -> str:
        """Build 700-RESTART-CONTROL paragraph."""
        return """        700-RESTART-CONTROL.
            MOVE CS-PROGRAM
            TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.
            MOVE DA-DD-MM-CCYY
            TO DA-CR-RS         OF DCLDZ01RSTV.
            MOVE 1
            TO NB-ID-RS-PHASE   OF DCLDZ01RSTV.

            PERFORM 700-SELECT-DZ01RSTV.

            EVALUATE SQLCODE
                WHEN 0     PERFORM 810-JOB-IS-RESTART
                WHEN 100   PERFORM 820-WRITE-RESTART-REC
                WHEN OTHER PERFORM SQLERROR
            END-EVALUATE.

            MOVE 0 TO WS-TELLER.
            .

"""

    def _build_700_select_dz01rstv(self) -> str:
        """Build 700-SELECT-DZ01RSTV paragraph."""
        return """        700-SELECT-DZ01RSTV.
            EXEC SQL
              SELECT  NM_ID_RS_PROGRAM
              , NB_ID_RS_PHASE
              , DA_CR_RS
              , CO_ID_RS
              , NB_DAY_RS
              , TE_CH_RS_DATA
              INTO  :DCLDZ01RSTV.NM-ID-RS-PROGRAM
              , :DCLDZ01RSTV.NB-ID-RS-PHASE
              , :DCLDZ01RSTV.DA-CR-RS
              , :DCLDZ01RSTV.CO-ID-RS
              , :DCLDZ01RSTV.NB-DAY-RS
              , :DCLDZ01RSTV.TE-CH-RS-DATA
              FROM  DZ01RSTV
              WHERE NM_ID_RS_PROGRAM = :DCLDZ01RSTV.NM-ID-RS-PROGRAM
              AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE
              AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS
              QUERYNO 376
            END-EXEC

            EVALUATE SQLCODE
              WHEN 0
                   SET RESTART-FOUND TO TRUE
              WHEN 100
                   SET RESTART-NOT-FOUND TO TRUE
              WHEN OTHER
                   PERFORM SQLERROR
            END-EVALUATE
            .

"""

    def _build_700_update_dz01rstv(self) -> str:
        """Build 700-UPDATE-DZ01RSTV paragraph."""
        return """        700-UPDATE-DZ01RSTV.
            EXEC SQL
              UPDATE DZ01RSTV
              SET TE_CH_RS_DATA = :DCLDZ01RSTV.TE-CH-RS-DATA
              , CO_ID_RS = :DCLDZ01RSTV.CO-ID-RS
              WHERE NM_ID_RS_PROGRAM = :DCLDZ01RSTV.NM-ID-RS-PROGRAM
              AND NB_ID_RS_PHASE = :DCLDZ01RSTV.NB-ID-RS-PHASE
              AND DA_CR_RS = :DCLDZ01RSTV.DA-CR-RS
              QUERYNO 398
            END-EXEC

            EVALUATE SQLCODE
              WHEN 0
                   CONTINUE
              WHEN OTHER
                   PERFORM SQLERROR
            END-EVALUATE
            .

"""

    def _build_700_insert_dz01rstv(self) -> str:
        """Build 700-INSERT-DZ01RSTV paragraph."""
        return """        700-INSERT-DZ01RSTV.
            EXEC SQL
              INSERT INTO DZ01RSTV
              (NM_ID_RS_PROGRAM
              ,NB_ID_RS_PHASE
              ,DA_CR_RS
              ,CO_ID_RS
              ,NB_DAY_RS
              ,TE_CH_RS_DATA)
              VALUES
              (:DCLDZ01RSTV.NM-ID-RS-PROGRAM
              ,:DCLDZ01RSTV.NB-ID-RS-PHASE
              ,:DCLDZ01RSTV.DA-CR-RS
              ,:DCLDZ01RSTV.CO-ID-RS
              ,:DCLDZ01RSTV.NB-DAY-RS
              ,:DCLDZ01RSTV.TE-CH-RS-DATA)
              QUERYNO 442
            END-EXEC

            EVALUATE SQLCODE
              WHEN 0
                   CONTINUE
              WHEN OTHER
                   PERFORM SQLERROR
            END-EVALUATE
            .

"""

    # ========== PHASE 4: HANDLER PARAGRAPHS ==========

    def _ensure_handler_paragraphs(self, text: str, program_id: str) -> str:
        """Generate handler paragraphs for restart logic."""
        missing = []

        if not self.JOB_IS_RESTART_PATTERN.search(text):
            missing.append("810-JOB-IS-RESTART")
        if not re.search(r"^\s*(?:\d{6}\s+)?820-WRITE-RESTART-REC\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("820-WRITE-RESTART-REC")
        if not re.search(r"^\s*(?:\d{6}\s+)?800-PROCESS-COMMIT\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("800-PROCESS-COMMIT")
        if not re.search(r"^\s*(?:\d{6}\s+)?600-GET-TIMESTAMP\.", text, re.MULTILINE | re.IGNORECASE):
            missing.append("600-GET-TIMESTAMP")

        if not missing:
            return text

        insert_pos = self._find_stop_run(text)
        if insert_pos == -1:
            self.messages.append(f"{program_id}: STOP RUN not found")
            return text

        paragraphs = []
        for para in missing:
            if para == "810-JOB-IS-RESTART":
                paragraphs.append(self._build_810_job_is_restart())
            elif para == "820-WRITE-RESTART-REC":
                paragraphs.append(self._build_820_write_restart_rec())
            elif para == "800-PROCESS-COMMIT":
                paragraphs.append(self._build_800_process_commit())
            elif para == "600-GET-TIMESTAMP":
                paragraphs.append(self._build_600_get_timestamp())

        new_content = "\n".join(paragraphs)
        text = text[:insert_pos] + new_content + text[insert_pos:]

        for para in missing:
            self.messages.append(f"Added {para} handler paragraph")

        return text

    def _build_810_job_is_restart(self) -> str:
        """Build 810-JOB-IS-RESTART paragraph."""
        return """        810-JOB-IS-RESTART.
            MOVE TE-CH-RS-DATA OF DCLDZ01RSTV TO WS-RESTART-REC.

            IF CO-ID-RS OF DCLDZ01RSTV = '1'
            THEN DISPLAY 'PREVIOUS RUN COMPLETE'
                 CONTINUE
            ELSE DISPLAY 'RESUMING FROM CHECKPOINT: '
                 MOVE NB-READ OF WS-RESTART-REC TO WS-NB-INPUT-REC
            END-IF.
            .

"""

    def _build_820_write_restart_rec(self) -> str:
        """Build 820-WRITE-RESTART-REC paragraph."""
        return """        820-WRITE-RESTART-REC.
            MOVE '0'                TO CO-ID-RS OF DCLDZ01RSTV.
            MOVE 7                  TO NB-DAY-RS OF DCLDZ01RSTV.
            MOVE 1215               TO NB-READ OF WS-RESTART-REC.
            MOVE ZERO               TO WS-NB-INPUT-REC.
            MOVE WS-RESTART-REC     TO TE-CH-RS-DATA OF DCLDZ01RSTV.

            PERFORM 700-INSERT-DZ01RSTV.

            DISPLAY 'STARTING NEW RUN - RESTART RECORD CREATED'.
            .

"""

    def _build_800_process_commit(self) -> str:
        """Build 800-PROCESS-COMMIT paragraph."""
        return """        800-PROCESS-COMMIT.
            IF SW-EOF = 'Y'
            THEN MOVE '1'           TO CO-ID-RS OF DCLDZ01RSTV
            ELSE MOVE '0'           TO CO-ID-RS OF DCLDZ01RSTV
            END-IF.

            MOVE WS-RESTART-REC     TO TE-CH-RS-DATA OF DCLDZ01RSTV.

            PERFORM 700-UPDATE-DZ01RSTV.

            EXEC SQL
              COMMIT
            END-EXEC.

            EVALUATE SQLCODE
              WHEN 0
                   ADD 1 TO WS-COMMIT-COUNTER
              WHEN OTHER
                   PERFORM SQLERROR
            END-EVALUATE.
            .

"""

    def _build_600_get_timestamp(self) -> str:
        """Build 600-GET-TIMESTAMP paragraph."""
        return """        600-GET-TIMESTAMP.
            MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.
            MOVE CC OF TS-SYSTEM TO CC OF TS-TIMESTAMP.
            MOVE YY OF TS-SYSTEM TO YY OF TS-TIMESTAMP.
            MOVE MM OF TS-SYSTEM TO MM OF TS-TIMESTAMP.
            MOVE DD OF TS-SYSTEM TO DD OF TS-TIMESTAMP.
            MOVE HH OF TS-SYSTEM TO HH OF TS-TIMESTAMP.
            MOVE MI OF TS-SYSTEM TO MI OF TS-TIMESTAMP.
            MOVE SS OF TS-SYSTEM TO SS OF TS-TIMESTAMP.
            MOVE TT OF TS-SYSTEM TO TT OF TS-TIMESTAMP.
            .

"""

    # ========== PHASE 4.5: AUDIT FIELD MOVES IN VERWERKING ==========

    def _add_audit_field_moves_in_verwerking(self, text: str, program_id: str) -> str:
        """Add MOVE statements for audit fields within VERWERKING field initialization.
        
        HARD-CODED LOGIC: For UPDATE programs (VMDZ1526, VMDZ1567), ALWAYS add audit field MOVEs
        before the *DB2: Converted MODIFY comment. The DCLGEN field names come from sheet mapping.
        """
        # Check if already present (idempotent)
        if 'MOVE TS-TIMESTAMP TO TS-UPDATE-479BFAR' in text:
            return text
        
        # Hard-coded: Find "*DB2: Converted MODIFY" and insert before it
        marker = '*DB2: Converted MODIFY for'
        
        if marker not in text:
            return text
        
        # Split into lines
        lines = text.split('\n')
        modified = False
        
        # Find and replace the marker line
        for i in range(len(lines)):
            if marker in lines[i]:
                # Get indentation from the marker line
                indent = ''
                for ch in lines[i]:
                    if ch == ' ' or ch == '\t':
                        indent += ch
                    else:
                        break
                
                # Create two new lines with audit MOVEs
                line1 = indent + 'MOVE TS-TIMESTAMP TO TS-UPDATE-479BFAR OF DCLDZBFARTV.'
                line2 = indent + 'MOVE CS-PROGRAM TO ID-USERID-479BFAR OF DCLDZBFARTV.'
                
                # Insert before the marker
                lines.insert(i, line2)
                lines.insert(i, line1)
                modified = True
                break
        
        if modified:
            self.messages.append("Added audit field MOVEs")
        
        return '\n'.join(lines)


    # ========== PHASE 5: PROCEDURE DIVISION ==========

    def _fix_procedure_division(self, text: str, program_id: str) -> str:
        """Fix procedure division flow and integration."""
        # Ensure 600-GET-TIMESTAMP is called early
        proc_div_pos = self._find_procedure_division_start(text)
        if proc_div_pos == -1:
            return text

        # Check if GET-TIMESTAMP is already called
        if re.search(
            r"PERFORM\s+600-GET-TIMESTAMP",
            text[proc_div_pos:],
            flags=re.IGNORECASE,
        ):
            return text

        # Find first substantial statement after PROCEDURE DIVISION
        first_stmt = re.search(
            r"PROCEDURE\s+DIVISION\b.*?\n\s*(?:\d{6}\s+)?(PERFORM|MOVE|INITIALIZE|OPEN|SET)",
            text[proc_div_pos:],
            flags=re.IGNORECASE | re.MULTILINE,
        )

        if first_stmt:
            insert_pos = proc_div_pos + first_stmt.start(1)
            timestamp_call = "        PERFORM 600-GET-TIMESTAMP.\n"
            text = text[:insert_pos] + timestamp_call + text[insert_pos:]
            self.messages.append("Integrated timestamp initialization")

        return text

"""
Abstract base class for restart logic generation.

This module defines the interface that all restart logic generators must implement.
Subclasses can override methods to customize restart behavior for different programs
or COBOL dialects without affecting core framework logic.

Design Pattern: Template Method
- Base class defines overall structure (generate_all_paragraphs)
- Subclasses override individual paragraph generators
- Pipeline layer orchestrates injection into COBOL source
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from idms_db2_phase2.postprocess.restart_config import RestartConfig


class RestartLogicGenerator(ABC):
    """
    Abstract base class for generating restart-aware UPDATE program logic.
    
    This generator is responsible for creating COBOL paragraphs that:
    1. Control program restart from checkpoints
    2. Query and manage restart table records
    3. Save checkpoint state during processing
    4. Handle restart found/not found conditions
    5. Manage commit frequency and program completion
    
    This generator does NOT:
    - Modify business update logic
    - Touch retrieval (SELECT cursor) logic
    - Change DCLGEN include declarations
    - Alter field reference mappings
    
    Thread Safety: Not required (COBOL generation is single-threaded)
    
    Subclass Requirements:
    - Override all @abstractmethod methods
    - Preserve paragraph naming conventions from RestartConfig
    - Generate valid COBOL with proper indentation
    - Include embedded SQL where required
    - Maintain QUERYNO consistency
    """
    
    def __init__(self, config: RestartConfig) -> None:
        """
        Initialize generator with restart configuration.
        
        Args:
            config: RestartConfig instance with all restart metadata
        
        Raises:
            ValueError: If required config fields are missing or invalid
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate that config has all required fields."""
        required_fields = [
            "restart_table_name",
            "restart_dclgen_name",
            "commit_frequency",
        ]
        for field in required_fields:
            if not getattr(self.config, field, None):
                raise ValueError(f"RestartConfig missing required field: {field}")
    
    @abstractmethod
    def generate_restart_control_paragraph(self) -> str:
        """
        Generate 700-RESTART-CONTROL paragraph.
        
        Entry point for restart logic. This paragraph:
        1. Sets up initial state (switches, counters)
        2. Calls SELECT to check if restart record exists
        3. Routes to 710-JOB-IS-RESTART if found (SQLCODE=0)
        4. Routes to 720-WRITE-RESTART-REC if not found (SQLCODE=100)
        5. Handles SQL errors appropriately
        
        Return:
            COBOL paragraph starting with "700-RESTART-CONTROL."
                and ending with paragraph boundary (next paragraph or END PROGRAM)
        
        Example Structure:
            700-RESTART-CONTROL.
                MOVE CS-PROGRAM TO NM-ID-RS-PROGRAM OF DCLDZ01RSTV.
                MOVE DA-DD-MM-CCYY TO DA-CR-RS OF DCLDZ01RSTV.
                MOVE 1 TO NB-ID-RS-PHASE OF DCLDZ01RSTV.
                PERFORM 700-SELECT-DZ01RSTV.
                EVALUATE SQLCODE
                    WHEN 0
                        PERFORM 710-JOB-IS-RESTART
                    WHEN 100
                        PERFORM 720-WRITE-RESTART-REC
                    WHEN OTHER
                        PERFORM SQLERROR
                END-EVALUATE.
        """
        pass
    
    @abstractmethod
    def generate_select_paragraph(self) -> str:
        """
        Generate 700-SELECT-DZ01RSTV paragraph.
        
        Queries restart table for existing checkpoint. Used by:
        - 700-RESTART-CONTROL (first call)
        - 800-PROCESS-COMMIT (periodic checkpoint update)
        
        SQLCODE routing:
        - 0: Record found (SQLCODE must be checked by caller)
        - 100: Record not found (SQLCODE must be checked by caller)
        - Other: SQL error (route to SQLERROR)
        
        WHERE Clause:
        - Program ID must match
        - Phase must match
        - Date must match
        
        Return:
            COBOL paragraph starting with "700-SELECT-DZ01RSTV."
                with embedded EXEC SQL...END-EXEC
        
        Constraints:
        - Must use QUERYNO 376
        - Must NOT modify source record
        - Must populate DCLDZ01RSTV structure
        - Must preserve SQLCODE for caller evaluation
        """
        pass
    
    @abstractmethod
    def generate_restart_found_paragraph(self) -> str:
        """
        Generate 710-JOB-IS-RESTART paragraph.
        
        Handles case where restart checkpoint record already exists.
        Determines if previous run completed or needs restart.
        
        Logic:
        1. Extract checkpoint data from TE-CH-RS-DATA into WS-RESTART-REC
        2. Check CO-ID-RS (status flag):
            - If '1' (complete): Previous run finished → call USERABEN to end gracefully
            - If '0' (incomplete): Previous run failed → skip to checkpoint, resume processing
        3. Set up for resume: Skip NB-READ records, start from checkpoint key
        
        Return:
            COBOL paragraph starting with "710-JOB-IS-RESTART."
        
        Example:
            710-JOB-IS-RESTART.
                MOVE TE-CH-RS-DATA OF DCLDZ01RSTV
                    TO WS-RESTART-REC.
                IF CO-ID-RS OF DCLDZ01RSTV = '1'
                    THEN
                        DISPLAY ' PREVIOUS RUN COMPLETE '
                        PERFORM 810000-CALL-USERABEN
                    ELSE
                        PERFORM NB-READ OF WS-RESTART-REC TIMES
                            PERFORM READ-FLAT-FILE
                        END-PERFORM
                        MOVE NB-READ OF WS-RESTART-REC
                            TO WS-NB-INPUT-UPD-I
                END-IF.
        """
        pass
    
    @abstractmethod
    def generate_write_restart_paragraph(self) -> str:
        """
        Generate 720-WRITE-RESTART-REC paragraph.
        
        Creates new checkpoint record on first run.
        Called when SELECT returns SQLCODE=100 (record not found).
        
        Logic:
        1. Initialize checkpoint status to '0' (incomplete)
        2. Set retention days
        3. Initialize checkpoint data (NB-READ=0, KY-RESTART=spaces)
        4. Set checkpoint data length
        5. Populate restart DCLGEN structure
        6. Call 700-INSERT-DZ01RSTV to insert new record
        
        Return:
            COBOL paragraph starting with "720-WRITE-RESTART-REC."
        
        Example:
            720-WRITE-RESTART-REC.
                MOVE '0' TO CO-ID-RS OF DCLDZ01RSTV.
                MOVE 7 TO NB-DAY-RS OF DCLDZ01RSTV.
                MOVE 0 TO WS-NB-INPUT-UPD-I.
                MOVE WS-NB-INPUT-UPD-I TO NB-READ OF WS-RESTART-REC.
                INITIALIZE KY-RESTART.
                MOVE 1215 TO TE-CH-RS-DATA-LEN OF DCLDZ01RSTV.
                MOVE WS-RESTART-REC TO TE-CH-RS-DATA-TEXT OF DCLDZ01RSTV.
                PERFORM 700-INSERT-DZ01RSTV.
        """
        pass
    
    @abstractmethod
    def generate_commit_paragraph(self) -> str:
        """
        Generate 800-PROCESS-COMMIT paragraph.
        
        Periodic checkpoint save during main processing loop.
        Called from main business processing when commit_frequency
        records have been processed (e.g., every 99 records).
        
        Logic:
        1. Reset commit counter
        2. Move current state to restart record:
           - NB-READ: Records processed so far
           - KY-RESTART: Last successfully processed record key
        3. Check EOF flag:
           - If at EOF: Set status to '1' (complete)
           - If not EOF: Set status to '0' (incomplete)
        4. Set data length
        5. Call 700-UPDATE-DZ01RSTV to update checkpoint
        6. COMMIT transaction
        7. Check SQLCODE and handle errors
        
        Return:
            COBOL paragraph starting with "800-PROCESS-COMMIT."
        
        Constraints:
        - Must COMMIT after checkpoint update
        - Must check SQLCODE and route errors to SQLERROR
        - Must preserve business logic execution
        """
        pass
    
    @abstractmethod
    def generate_update_paragraph(self) -> str:
        """
        Generate 700-UPDATE-DZ01RSTV paragraph.
        
        Updates existing checkpoint record with current state.
        Called by 800-PROCESS-COMMIT during processing.
        
        Logic:
        1. Execute UPDATE SQL on restart table
        2. Set columns:
           - TE_CH_RS_DATA: Checkpoint state from WS-RESTART-REC
           - CO_ID_RS: Status flag (complete/incomplete)
        3. WHERE clause must include:
           - Program ID
           - Phase
           - Date (composite key)
        4. Use QUERYNO 398
        
        Return:
            COBOL paragraph starting with "700-UPDATE-DZ01RSTV."
                with embedded EXEC SQL...END-EXEC
        
        Constraints:
        - Must use QUERYNO 398
        - Must preserve checkpoint structure
        - Must NOT modify other columns
        - Must set TE_CH_RS_DATA (payload) and CO_ID_RS (status)
        """
        pass
    
    @abstractmethod
    def generate_insert_paragraph(self) -> str:
        """
        Generate 700-INSERT-DZ01RSTV paragraph.
        
        Inserts new checkpoint record on first run.
        Called by 720-WRITE-RESTART-REC only.
        
        Logic:
        1. Execute INSERT SQL to create new checkpoint record
        2. Populate all columns from DCLDZ01RSTV:
           - Program ID, Phase, Date (composite key)
           - Status, Retention, Payload
        3. Use QUERYNO 413
        4. Handle SQLCODE (0=success, other=error)
        
        Return:
            COBOL paragraph starting with "700-INSERT-DZ01RSTV."
                with embedded EXEC SQL...END-EXEC
        
        Constraints:
        - Must use QUERYNO 413
        - Must include all checkpoint columns
        - Must route SQLCODE errors to SQLERROR
        """
        pass
    
    @abstractmethod
    def generate_abend_paragraph(self) -> str:
        """
        Generate 810000-CALL-USERABEN paragraph.
        
        Called when previous run completed successfully
        (CO-ID-RS = '1' in 710-JOB-IS-RESTART).
        
        Purpose:
        - Mark job as complete
        - Terminate program gracefully
        - No further processing needed
        
        Return:
            COBOL paragraph starting with "810000-CALL-USERABEN."
        
        Example:
            810000-CALL-USERABEN.
                CALL USERABEN.
        """
        pass
    
    def generate_all_paragraphs(self) -> dict[str, str]:
        """
        Generate all restart paragraphs.
        
        Invokes all abstract methods and returns dictionary of
        paragraph names to COBOL code.
        
        Return:
            Dictionary with keys:
            - "restart_control" → 700-RESTART-CONTROL code
            - "select" → 700-SELECT-DZ01RSTV code
            - "restart_found" → 710-JOB-IS-RESTART code
            - "write_restart" → 720-WRITE-RESTART-REC code
            - "commit" → 800-PROCESS-COMMIT code
            - "update" → 700-UPDATE-DZ01RSTV code
            - "insert" → 700-INSERT-DZ01RSTV code
            - "abend" → 810000-CALL-USERABEN code
        
        Raises:
            RuntimeError: If any subclass method raises unexpected exception
        """
        return {
            "restart_control": self.generate_restart_control_paragraph(),
            "select": self.generate_select_paragraph(),
            "restart_found": self.generate_restart_found_paragraph(),
            "write_restart": self.generate_write_restart_paragraph(),
            "commit": self.generate_commit_paragraph(),
            "update": self.generate_update_paragraph(),
            "insert": self.generate_insert_paragraph(),
            "abend": self.generate_abend_paragraph(),
        }
    
    def get_paragraph_names(self) -> dict[str, str]:
        """
        Get mapping of paragraph logical names to actual paragraph names.
        
        Return:
            Dictionary mapping:
            - "restart_control" → "700-RESTART-CONTROL"
            - "select" → "700-SELECT-DZ01RSTV"
            - etc.
        """
        return {
            "restart_control": self.config.para_restart_control,
            "select": self.config.para_select,
            "restart_found": self.config.para_job_is_restart,
            "write_restart": self.config.para_write_restart,
            "commit": self.config.para_commit,
            "update": self.config.para_update,
            "insert": self.config.para_insert,
            "abend": self.config.para_abend,
        }

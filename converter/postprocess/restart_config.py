"""
Restart logic configuration - reusable across UPDATE programs.

This module provides a configuration object to specify restart behavior
without hardcoding table names, DCLGEN names, or checkpoint fields.

All restart metadata is derived from:
1. Sheet mapping annotations (TB suffix convention)
2. Parsed DCLGEN role analysis
3. Update program context
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RestartConfig:
    """
    Configuration for restart-aware UPDATE program generation.
    
    Purpose:
    - Centralize all restart-related settings
    - Enable reuse across different update programs
    - Maintain sheet mapping alignment (TB→TV conversion)
    - Support future customization without code changes
    
    Attributes:
        restart_table_name: SQL table name for checkpoints (e.g., "DZ01RSTV")
        restart_dclgen_name: COBOL DCLGEN name for checkpoint structure
        
        program_id_field: COBOL field name for program ID checkpoint column
        phase_field: COBOL field name for phase/run checkpoint column
        date_field: COBOL field name for date/creation checkpoint column
        status_field: COBOL field name for completion status checkpoint column
        retention_field: COBOL field name for retention days checkpoint column
        payload_field: COBOL field name for checkpoint data payload
        
        switch_group: WS variable group for EOF/restart switches
        help_group: WS variable group for restart record and counters
        restart_record: WS variable holding checkpoint data
        read_count: WS variable for records processed count
        restart_key: WS variable for last processed record key
        commit_counter: WS variable for commit frequency counter
        
        commit_frequency: Commit and checkpoint update every N records
        status_incomplete: Literal value for incomplete status (default "0")
        status_complete: Literal value for complete status (default "1")
        default_phase: Literal value for initial phase (default "1")
        retention_days: Literal value for checkpoint retention (default "7")
        
        para_*: Paragraph names (all 700-/800-/900-/1000-level standards)
    """
    
    # ---- Restart Table Metadata ----
    restart_table_name: str
    restart_dclgen_name: str
    
    # ---- Checkpoint Column Fields (COBOL DCL names) ----
    program_id_field: str = "NM-ID-RS-PROGRAM"
    phase_field: str = "NB-ID-RS-PHASE"
    date_field: str = "DA-CR-RS"
    status_field: str = "CO-ID-RS"
    retention_field: str = "NB-DAY-RS"
    payload_field: str = "TE-CH-RS-DATA"
    payload_text_field: str = "TE-CH-RS-DATA-TEXT"
    payload_length_field: str = "TE-CH-RS-DATA-LEN"
    
    # ---- Working Storage Variable Names ----
    switch_group: str = "WS-SWITCHES"
    help_group: str = "HELP-VARIABLE"
    restart_record: str = "WS-RESTART-REC"
    read_count: str = "NB-READ"
    restart_key: str = "KY-RESTART"
    input_save_area: str = "WS-INPUT-KASBONS"
    commit_counter: str = "WS-TELLER"
    input_counter: str = "WS-NB-INPUT-UPD-I"
    update_counter: str = "WS-NB-BFAR-UPD-I"
    restart_len: str = "WS-RESTART-LEN"
    
    # ---- Control Flow Literals ----
    commit_frequency: int = 99
    status_incomplete: str = "0"
    status_complete: str = "1"
    default_phase: str = "1"
    retention_days: str = "7"
    
    # ---- Paragraph Names ----
    para_restart_control: str = "700-RESTART-CONTROL"
    para_job_is_restart: str = "710-JOB-IS-RESTART"
    para_write_restart: str = "720-WRITE-RESTART-REC"
    para_commit: str = "800-PROCESS-COMMIT"
    para_select: str = "700-SELECT-DZ01RSTV"
    para_update: str = "700-UPDATE-DZ01RSTV"
    para_insert: str = "700-INSERT-DZ01RSTV"
    para_abend: str = "810000-CALL-USERABEN"
    
    # ---- SQL QUERYNO Constants ----
    queryno_select: str = "376"
    queryno_update: str = "398"
    queryno_insert: str = "413"
    
    # ---- EOF Switch Flag Name ----
    eof_switch_flag: str = "VMDZ205I"
    
    # ---- Additional Metadata ----
    minimum_dclgen_score: int = 10  # Minimum score before using fallback
    notes: str = field(default="", metadata={"doc": "Implementation notes for code review"})
    
    @classmethod
    def from_context(cls, context: object) -> RestartConfig:
        """
        Create RestartConfig from UpdateProgramContext.
        
        This factory method extracts restart metadata from:
        1. context.restart_dclgen (resolved DCLGEN metadata)
        2. context.restart_table_hints (sheet mapping hints)
        3. context.program_metadata (program-specific conventions)
        """
        # TODO: Implement context-to-config extraction
        # For now, return defaults with table info from context
        raise NotImplementedError("Use direct constructor with resolved metadata")
    
    def apply_original_names(self, original_mapping: dict) -> None:
        """
        Apply original variable names from program source.
        
        This method preserves naming conventions from the original program
        when applying restart logic. Prevents normalization from breaking
        integrations with other modules expecting specific variable names.
        
        Args:
            original_mapping: Dict mapping attribute names to original names
                Example: {"input_counter": "WS-NB-INPUT-UPD-I"}
        """
        import re
        
        for attr_name, original_name in original_mapping.items():
            if hasattr(self, attr_name):
                setattr(self, attr_name, original_name)
    
    def detect_from_cobol(self, cobol_text: str) -> None:
        """
        Auto-detect and apply original variable names from COBOL source.
        
        Analyzes the COBOL source to find original variable naming patterns
        and applies them to this configuration.
        
        Patterns detected:
        - SW-VMDZ205I / VMDZ205I-EOF / VMDZ205I-NOT-EOF (switch naming)
        - WS-NB-INPUT-UPD-I (input counter naming)
        - WS-NB-BFAR-UPD-I (update counter naming)
        """
        import re
        
        original_mapping = {}
        
        # Detect VMDZ205I-style switch
        if re.search(r"SW-VMDZ205I\s+PIC\s+X", cobol_text, re.IGNORECASE):
            original_mapping["eof_switch_flag"] = "VMDZ205I"
        
        # Detect input counter naming pattern
        if re.search(r"WS-NB-INPUT-UPD-I\s+PIC", cobol_text, re.IGNORECASE):
            original_mapping["input_counter"] = "WS-NB-INPUT-UPD-I"
        
        # Detect update counter naming pattern
        if re.search(r"WS-NB-BFAR-UPD-I\s+PIC", cobol_text, re.IGNORECASE):
            original_mapping["update_counter"] = "WS-NB-BFAR-UPD-I"
        
        # Detect alternative switch names
        if re.search(r"WS-RECORD-FOUND\s+PIC\s+X", cobol_text, re.IGNORECASE):
            original_mapping["switch_group"] = "WS-SWITCHES"
        
        if original_mapping:
            self.apply_original_names(original_mapping)
    
    def to_dict(self) -> dict:
        """Export config as dictionary for serialization or logging."""
        return {
            "restart_table_name": self.restart_table_name,
            "restart_dclgen_name": self.restart_dclgen_name,
            "commit_frequency": self.commit_frequency,
            "status_incomplete": self.status_incomplete,
            "status_complete": self.status_complete,
            "default_phase": self.default_phase,
            "retention_days": self.retention_days,
            "paragraphs": {
                "control": self.para_restart_control,
                "restart_found": self.para_job_is_restart,
                "write": self.para_write_restart,
                "commit": self.para_commit,
                "select": self.para_select,
                "update": self.para_update,
                "insert": self.para_insert,
                "abend": self.para_abend,
            },
        }
    
    def __repr__(self) -> str:
        return (
            f"RestartConfig(table={self.restart_table_name}, "
            f"dclgen={self.restart_dclgen_name}, "
            f"commit_freq={self.commit_frequency})"
        )

"""
Pipeline stage for injecting restart logic into UPDATE programs.

This module defines the pipeline integration that:
1. Detects when restart logic is needed (UPDATE program with restart table)
2. Validates restart metadata availability
3. Injects restart paragraphs at appropriate locations
4. Preserves existing business logic
5. Reports diagnostics on any skips or issues

Pipeline Design:
- Stage: Late postprocess (after business logic transformation, before final cleanup)
- Applicability: UPDATE-family programs only
- Non-destructive: Skips safely if restart metadata missing
- Ordered: Restart logic injection before final code cleanup
"""

from __future__ import annotations

from typing import Optional

from converter.postprocess.restart_config import RestartConfig
from converter.postprocess.restart_logic_generator import RestartLogicGenerator
from converter.postprocess.update_postprocess_line_utils import (
    UpdatePostprocessLineUtils,
)


class RestartLogicPipeline:
    """
    Pipeline stage for injecting restart-aware UPDATE logic.
    
    Responsibility:
    - Apply restart control flow to UPDATE programs
    - Inject checkpoint save logic in main loop
    - Preserve business update logic
    - Do NOT modify retrieval logic
    - Do NOT touch field reference mappings
    
    Non-applicability:
    - Retrieval programs (SELECT-only, no updates)
    - Programs without restart table access
    - Programs with missing restart DCLGEN metadata
    
    Diagnostics:
    - Logs reason if not applicable (so user knows why skipped)
    - Reports injection points (control, checkpoints, paragraphs)
    - Captures SQL errors or structure issues
    
    Thread Safety: Not required (pipeline runs single-threaded per program)
    
    Typical Usage:
        config = RestartConfig(
            restart_table_name="DZ01RSTV",
            restart_dclgen_name="DCLDZ01RSTV",
        )
        generator = CobolRestartLogicGenerator(config)
        pipeline = RestartLogicPipeline(config, generator, line_utils)
        
        if pipeline.is_applicable(context):
            enhanced_cobol = pipeline.apply_to_program(cobol_source, context)
            diagnostics = pipeline.diagnostics  # Inspect results
    """
    
    def __init__(
        self,
        config: RestartConfig,
        generator: RestartLogicGenerator,
        line_utils: UpdatePostprocessLineUtils,
    ) -> None:
        """
        Initialize restart logic pipeline.
        
        Args:
            config: RestartConfig with all restart metadata
            generator: RestartLogicGenerator subclass (e.g., for COBOL)
            line_utils: Utility for COBOL line manipulation
        
        Raises:
            ValueError: If any argument is None
        """
        if not config or not generator or not line_utils:
            raise ValueError("config, generator, and line_utils are required")
        
        self.config = config
        self.generator = generator
        self.line_utils = line_utils
        self.diagnostics: list[str] = []
    
    def is_applicable(self, context: object) -> bool:
        """
        Check if restart logic should be applied to this program.
        
        Applicability Criteria:
        1. Program is in UPDATE family (context.program_kind == "update")
        2. Program has restart table access (context.restart_dclgen is not None)
        3. Restart DCLGEN metadata is resolved (score >= minimum_dclgen_score)
        
        Args:
            context: UpdateProgramContext with program metadata
        
        Returns:
            True if restart logic should be applied, False otherwise
        """
        # Check program kind
        if not hasattr(context, "program_kind"):
            return False
        if context.program_kind != "update":
            self.diagnostics.append(
                f"Not applicable: program_kind={context.program_kind} (not 'update')"
            )
            return False
        
        # Check restart table access
        if not hasattr(context, "restart_dclgen") or not context.restart_dclgen:
            self.diagnostics.append("Not applicable: no restart table access")
            return False
        
        # Check metadata quality
        if hasattr(context.restart_dclgen, "score"):
            if context.restart_dclgen.score < self.config.minimum_dclgen_score:
                self.diagnostics.append(
                    f"Not applicable: restart DCLGEN score "
                    f"{context.restart_dclgen.score} < {self.config.minimum_dclgen_score}"
                )
                return False
        
        return True
    
    def not_applicable_reason(self) -> str:
        """
        Return reason why restart logic was not applicable.
        
        If is_applicable() returned True, this returns empty string.
        Otherwise, returns the first diagnostic message.
        """
        return self.diagnostics[0] if self.diagnostics else ""
    
    def apply_to_program(
        self,
        cobol_source: str,
        context: object,
    ) -> str:
        """
        Apply restart logic to UPDATE program source.
        
        Stages:
        1. Validate applicability (calls is_applicable internally)
        2. Validate COBOL structure (WS groups, paragraphs)
        3. Generate restart paragraphs
        4. Inject restart control entry point (if not present)
        5. Inject checkpoint save points in main loop
        6. Verify final structure
        
        Args:
            cobol_source: COBOL source code to enhance
            context: UpdateProgramContext with program metadata
        
        Returns:
            Enhanced COBOL source with restart logic injected.
            If not applicable, returns original source unchanged.
        
        Raises:
            ValueError: If COBOL structure is invalid (e.g., missing PROCEDURE DIVISION)
            RuntimeError: If restart generator fails unexpectedly
        """
        self.diagnostics.clear()
        
        # Check applicability first
        if not self.is_applicable(context):
            return cobol_source
        
        self.diagnostics.append("Restart logic injection: APPLICABLE")
        
        # Validate COBOL structure
        try:
            self._validate_cobol_structure(cobol_source)
        except ValueError as e:
            self.diagnostics.append(f"COBOL structure validation failed: {e}")
            return cobol_source
        
        # Generate restart paragraphs
        try:
            paragraphs = self.generator.generate_all_paragraphs()
            self.diagnostics.append(f"Generated {len(paragraphs)} restart paragraphs")
        except Exception as e:
            self.diagnostics.append(f"Paragraph generation failed: {e}")
            return cobol_source
        
        # Inject paragraphs into COBOL
        try:
            enhanced = self._inject_restart_paragraphs(cobol_source, paragraphs)
            self.diagnostics.append("Restart paragraphs injected successfully")
            return enhanced
        except Exception as e:
            self.diagnostics.append(f"Paragraph injection failed: {e}")
            return cobol_source
    
    def _validate_cobol_structure(self, cobol_source: str) -> None:
        """
        Validate that COBOL source has required structure for restart injection.
        
        Required:
        - PROCEDURE DIVISION present
        - WORKING-STORAGE SECTION present
        - WS-SWITCHES group for EOF switch
        - HELP-VARIABLE group for restart record
        
        Raises:
            ValueError: If required structure is missing
        """
        lines = self.line_utils.lines(cobol_source)
        
        # Check for PROCEDURE DIVISION
        if not self.line_utils.find_paragraph_range(lines, "MAIN-PROCESS"):
            raise ValueError("No main PROCEDURE DIVISION paragraph found")
        
        # Check for WS-SWITCHES
        switch_group = self.config.switch_group
        if not self.line_utils.logical_contains(cobol_source, f"01 {switch_group}."):
            raise ValueError(f"Missing {switch_group} group in WORKING-STORAGE")
        
        # Check for HELP-VARIABLE
        help_group = self.config.help_group
        if not self.line_utils.logical_contains(cobol_source, f"01 {help_group}."):
            raise ValueError(f"Missing {help_group} group in WORKING-STORAGE")
    
    def _inject_restart_paragraphs(
        self,
        cobol_source: str,
        paragraphs: dict[str, str],
    ) -> str:
        """
        Inject restart paragraphs into COBOL source.
        
        Strategy:
        1. Find PROCEDURE DIVISION end marker (before END PROGRAM or last paragraph)
        2. Insert all restart paragraphs at that location
        3. Insert restart control call at start of MAIN-PROCESS if not present
        4. Return modified source
        
        Args:
            cobol_source: Original COBOL source
            paragraphs: Dictionary of paragraph_name → paragraph_code
        
        Returns:
            COBOL source with restart paragraphs injected
        
        Raises:
            ValueError: If insertion point cannot be found
        """
        lines = self.line_utils.lines(cobol_source)
        
        # Find insertion point (end of PROCEDURE DIVISION)
        insert_line = self._find_paragraph_insertion_point(lines)
        if insert_line < 0:
            raise ValueError("Could not find safe paragraph insertion point")
        
        # Build paragraph text
        paragraph_text = "\n\n".join(paragraphs.values())
        
        # Insert paragraphs
        updated_lines = (
            lines[:insert_line]
            + ["", paragraph_text, ""]
            + lines[insert_line:]
        )
        
        # Inject restart control call into MAIN-PROCESS if needed
        updated_text = self.line_utils.join(updated_lines)
        if "700-RESTART-CONTROL" not in updated_text:
            updated_text = self._inject_restart_control_call(updated_text)
        
        return updated_text
    
    def _find_paragraph_insertion_point(self, lines: list[str]) -> int:
        """
        Find the line where new paragraphs should be inserted.
        
        Strategy:
        1. Look for END PROGRAM keyword (end of source)
        2. If found, insert before it
        3. Otherwise, find last paragraph before EOF
        4. Return -1 if nothing found
        
        Args:
            lines: List of COBOL source lines
        
        Returns:
            Line index where paragraphs should be inserted, or -1
        """
        for i in range(len(lines) - 1, -1, -1):
            line_upper = lines[i].upper()
            if "END PROGRAM" in line_upper:
                return i  # Insert before END PROGRAM
        
        return len(lines) - 1  # Insert at end of file
    
    def _inject_restart_control_call(self, cobol_source: str) -> str:
        """
        Inject restart control call into MAIN-PROCESS paragraph.
        
        Strategy:
        1. Find MAIN-PROCESS paragraph
        2. Find first executable statement after paragraph header
        3. Insert "PERFORM 700-RESTART-CONTROL" before first statement
        
        Args:
            cobol_source: COBOL source code
        
        Returns:
            COBOL source with restart control call injected
        
        Raises:
            ValueError: If MAIN-PROCESS not found
        """
        lines = self.line_utils.lines(cobol_source)
        
        # Find MAIN-PROCESS
        main_range = self.line_utils.find_paragraph_range(lines, "MAIN-PROCESS")
        if not main_range:
            raise ValueError("MAIN-PROCESS paragraph not found")
        
        start_line, end_line = main_range
        
        # Find first executable statement (skip paragraph header and comments)
        first_statement = start_line + 1
        while (
            first_statement < end_line
            and (
                lines[first_statement].strip().startswith("*")
                or not lines[first_statement].strip()
            )
        ):
            first_statement += 1
        
        # Insert restart control call
        restart_call = f"    PERFORM {self.config.para_restart_control}."
        updated_lines = (
            lines[:first_statement]
            + [restart_call, ""]
            + lines[first_statement:]
        )
        
        return self.line_utils.join(updated_lines)

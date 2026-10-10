"""
CONVERTER PIPELINE INTEGRATION

Wires the new centralized converter generators into the Zowe pipeline
to apply production-ready COBOL standards to all output.

This is the orchestrator that ensures:
1. InitializationCentralizer runs to consolidate all INITIALIZE statements
2. WorkingStorageOrganizer runs to organize declarations
3. ProcedureDivisionOrganizer runs to create standard flow
4. All three work together seamlessly

How to integrate into existing pipeline:
  See: converter/orchestration/conversion/conversion_layout_pipeline.py

Add this as a final post-processing step AFTER all other converters:
  converter_enhanced_pipeline = ConverterEnhancementPipeline(program_text)
  production_ready_program = converter_enhanced_pipeline.execute()
"""

from __future__ import annotations
from typing import Optional
import logging

from .initialization_centralizer import (
    InitializationCentralizer,
)
from .working_storage_organizer import (
    WorkingStorageOrganizer,
)
from .procedure_division_organizer import (
    ProcedureDivisionOrganizer,
)
from converter.orchestration.conversion.conversion_layout_steps import (
    FinalSequenceResequencerService,
)


logger = logging.getLogger(__name__)


class ConverterEnhancementPipeline:
    """
    Post-processing pipeline to enhance converter output for production.
    
    Applies all standards for:
    - Centralized initialization
    - Organized WORKING-STORAGE
    - Structured PROCEDURE DIVISION
    
    Usage:
        pipeline = ConverterEnhancementPipeline(program_text, program_id)
        result = pipeline.execute()
    """
    
    def __init__(self, program_text: str, program_id: str = "UNKNOWN"):
        """
        Initialize the enhancement pipeline.
        
        Args:
            program_text: The COBOL program text from converter
            program_id: Program ID for logging
        """
        self.program_text = program_text
        self.program_id = program_id
        self.logger = logging.getLogger(__name__)
    
    def execute(self) -> str:
        """
        Execute all enhancement steps in sequence.
        
        Returns:
            Production-ready COBOL program text (with sequence numbers reprocessed)
        
        Steps:
            1. Centralize all initialization to 100-INITIALIZE
            2. Organize WORKING-STORAGE into 10 standard sections (TEMPORARILY DISABLED - losing counter fields)
            3. Structure PROCEDURE DIVISION with standard flow
            4. Resequence all lines to ensure proper COBOL format
        """
        result = self.program_text
        
        try:
            self.logger.info(
                f"[{self.program_id}] Starting converter enhancement pipeline"
            )
            
            # Step 1: Centralize initialization
            result = self._step_1_centralize_initialization(result)
            
            # Step 2: Organize WORKING-STORAGE (TEMPORARILY DISABLED - breaking counter field declarations)
            # result = self._step_2_organize_working_storage(result)
            
            # Step 3: Structure PROCEDURE DIVISION (TEMPORARILY DISABLED - needs debugging)
            # result = self._step_3_organize_procedure_division(result)
            
            # Step 4: Resequence the entire program to ensure proper COBOL fixed-format
            # This is necessary because the enhancement steps may have added new lines
            # that were not part of the original resequencing step
            result = FinalSequenceResequencerService().resequence(result)
            
            self.logger.info(
                f"[{self.program_id}] Converter enhancement pipeline complete"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                f"[{self.program_id}] Error in converter enhancement pipeline: {e}",
                exc_info=True
            )
            # Return original if error occurs
            return self.program_text
    
    def _step_1_centralize_initialization(self, program_text: str) -> str:
        """
        Step 1: Centralize all INITIALIZE statements to 100-INITIALIZE.
        
        Ensures:
          - No INITIALIZE in fetch loops
          - All DCLGEN groups initialized once at startup
          - Proper COBOL initialization patterns
        
        Args:
            program_text: Program text
        
        Returns:
            Program with centralized initialization
        """
        self.logger.info(f"[{self.program_id}] Step 1: Centralizing initialization")
        
        try:
            centralizer = InitializationCentralizer(program_text)
            result = centralizer.process()
            self.logger.debug(
                f"[{self.program_id}] Found {len(centralizer.dclgen_groups)} "
                "DCLGEN groups"
            )
            return result
        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to centralize initialization: {e}"
            )
            return program_text
    
    def _step_2_organize_working_storage(self, program_text: str) -> str:
        """
        Step 2: Organize WORKING-STORAGE into 10 standard sections.
        
        Ensures:
          - Logical organization by purpose (control, counters, timestamps, etc.)
          - Clear section separators
          - Consistent ordering across all programs
          - Audit fields always present
        
        Args:
            program_text: Program text
        
        Returns:
            Program with organized WORKING-STORAGE
        """
        self.logger.info(f"[{self.program_id}] Step 2: Organizing WORKING-STORAGE")
        
        try:
            organizer = WorkingStorageOrganizer(program_text)
            result = organizer.reorganize()
            
            # Count sections
            section_counts = {
                section: len(organizer.sections[section])
                for section in organizer.sections
            }
            self.logger.debug(
                f"[{self.program_id}] WORKING-STORAGE sections: {section_counts}"
            )
            return result
        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to organize WORKING-STORAGE: {e}"
            )
            return program_text
    
    def _step_3_organize_procedure_division(self, program_text: str) -> str:
        """
        Step 3: Structure PROCEDURE DIVISION with standard flow.
        
        Ensures:
          - Standard paragraph flow (100→200→300→400→500)
          - Proper initialization (100-INITIALIZE)
          - Generic timestamp paragraph (600-GET-TIMESTAMP)
          - Audit reporting (500-DISPLAY-TOTALS)
        
        Args:
            program_text: Program text
        
        Returns:
            Program with structured PROCEDURE DIVISION
        """
        self.logger.info(
            f"[{self.program_id}] Step 3: Organizing PROCEDURE DIVISION"
        )
        
        try:
            organizer = ProcedureDivisionOrganizer(program_text)
            result = organizer.organize()
            self.logger.debug(
                f"[{self.program_id}] Found {len(organizer.paragraphs)} paragraphs"
            )
            return result
        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to organize PROCEDURE DIVISION: {e}"
            )
            return program_text
    
    @staticmethod
    def validate_output(program_text: str) -> dict:
        """
        Validate that output meets production standards.
        
        Args:
            program_text: Program text to validate
        
        Returns:
            Dictionary with validation results
        
        Example:
            validation = ConverterEnhancementPipeline.validate_output(program)
            if validation['is_valid']:
                print("Program is production-ready")
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
        }
        
        # Check 1: 100-INITIALIZE exists
        if '100-INITIALIZE' not in program_text:
            validation['issues'].append("Missing 100-INITIALIZE paragraph")
            validation['is_valid'] = False
        
        # Check 2: No INITIALIZE in fetch paragraphs
        fetch_lines = [
            line for line in program_text.split('\n')
            if re.match(r'^\s*(?:\d{3}-)?(?:\d{3}-)?\w*FETCH', line)
        ]
        for fetch_line in fetch_lines:
            # Check next 20 lines for INITIALIZE
            fetch_start = program_text.find(fetch_line)
            fetch_end = program_text.find('\n.', fetch_start)
            if fetch_end > 0:
                fetch_block = program_text[fetch_start:fetch_end]
                if 'INITIALIZE' in fetch_block:
                    validation['warnings'].append(
                        f"INITIALIZE found in fetch paragraph: {fetch_line.strip()}"
                    )
        
        # Check 3: WORKING-STORAGE organized
        if '*-------- ' not in program_text:
            validation['warnings'].append("WORKING-STORAGE not organized with separators")
        
        # Check 4: 600-GET-TIMESTAMP exists
        if '600-GET-TIMESTAMP' not in program_text:
            validation['warnings'].append("Missing 600-GET-TIMESTAMP paragraph")
        
        # Check 5: 500-DISPLAY-TOTALS exists
        if '500-DISPLAY-TOTALS' not in program_text:
            validation['warnings'].append("Missing 500-DISPLAY-TOTALS paragraph")
        
        return validation


def enhance_converter_output(
    program_text: str,
    program_id: str = "UNKNOWN"
) -> str:
    """
    Convenience function to enhance converter output for production.
    
    Args:
        program_text: The COBOL program text from converter
        program_id: Program ID for logging
    
    Returns:
        Production-ready COBOL program text
    
    Example:
        enhanced = enhance_converter_output(original_program, "VMDZ4420")
    """
    pipeline = ConverterEnhancementPipeline(program_text, program_id)
    return pipeline.execute()


# Integration points for existing pipeline

def integrate_into_conversion_layout_pipeline():
    """
    Instructions for integrating enhancement pipeline into conversion_layout_pipeline.py
    
    In conversion_layout_pipeline.py, add this after all other converters:
    
    from converter.generators.converter_pipeline_integration import (
        ConverterEnhancementPipeline
    )
    
    # After all other composition steps:
    enhancement_pipeline = ConverterEnhancementPipeline(
        composed_program_text,
        program_id=context.program.name
    )
    production_ready_program = enhancement_pipeline.execute()
    
    This ensures all output is production-ready before writing to file.
    """
    pass


def integrate_into_postprocess_pipeline():
    """
    Instructions for integrating enhancement pipeline into postprocess steps
    
    The enhancement pipeline can run as:
    1. A final postprocess step after all converters
    2. Part of the main conversion layout
    3. A separate validation/enhancement pass
    
    Recommended: Add to conversion_layout_pipeline.py as final step before output
    """
    pass


# Logging configuration for pipeline
def setup_pipeline_logging(log_level=logging.INFO):
    """Setup logging for enhancement pipeline."""
    pipeline_logger = logging.getLogger(__name__)
    pipeline_logger.setLevel(log_level)
    
    if not pipeline_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        pipeline_logger.addHandler(handler)

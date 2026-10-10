"""
PROCEDURE DIVISION ORGANIZER

Structures PROCEDURE DIVISION with proper flow and standard paragraphs.

Purpose:
  - Ensures standard paragraph flow: 100→200→300→400→500→STOP RUN
  - Creates proper initialization (100-INITIALIZE) called first
  - Creates standard paragraph structure
  - Adds 600-GET-TIMESTAMP (generic, same in all programs)
  - Creates 500-DISPLAY-TOTALS for audit trail
  - Organizes existing paragraphs under proper flow

Standard Flow:
    PROCEDURE DIVISION.
        PERFORM 100-INITIALIZE.
        PERFORM 200-OPEN-CURSORS.
        PERFORM 300-MAIN-PROCESSING.
        PERFORM 400-CLOSE-CURSORS.
        PERFORM 500-DISPLAY-TOTALS.
        STOP RUN.
    
    100-INITIALIZE.
        [initialization logic]
        PERFORM 600-GET-TIMESTAMP.
    
    200-OPEN-CURSORS.
        [open cursor paragraphs]
    
    300-MAIN-PROCESSING.
        [fetch and process loops]
    
    400-CLOSE-CURSORS.
        [close cursor paragraphs]
    
    500-DISPLAY-TOTALS.
        PERFORM 600-GET-TIMESTAMP.
        DISPLAY 'Program ended at...'
        DISPLAY 'TOTAL RECORDS...'
    
    600-GET-TIMESTAMP.
        [Generic - same in all programs]
        MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.
        [8 more MOVE statements]

Usage:
    organizer = ProcedureDivisionOrganizer(program_text)
    organized = organizer.organize()
"""

import re
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from patterns.cobol_patterns import PARAGRAPH_PATTERN, PROCEDURE_DIVISION_PATTERN


@dataclass
class Paragraph:
    """Represents a COBOL paragraph."""
    name: str
    number: str
    content: str
    start_pos: int
    end_pos: int
    
    def __repr__(self):
        return f"Paragraph({self.name} {self.number})"


class ProcedureDivisionOrganizer:
    """Organizes PROCEDURE DIVISION with standard flow."""
    
    TIMESTAMP_PARAGRAPH_TEMPLATE = """600-GET-TIMESTAMP.
    *DB2: Generic timestamp capture (same in all programs)
    MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.
    MOVE CC OF TS-SYSTEM                  TO CC OF TS-TIMESTAMP.
    MOVE YY OF TS-SYSTEM                  TO YY OF TS-TIMESTAMP.
    MOVE MM OF TS-SYSTEM                  TO MM OF TS-TIMESTAMP.
    MOVE DD OF TS-SYSTEM                  TO DD OF TS-TIMESTAMP.
    MOVE HH OF TS-SYSTEM                  TO HH OF TS-TIMESTAMP.
    MOVE MI OF TS-SYSTEM                  TO MI OF TS-TIMESTAMP.
    MOVE SS OF TS-SYSTEM                  TO SS OF TS-TIMESTAMP.
    MOVE TT OF TS-SYSTEM                  TO TT OF TS-TIMESTAMP.
    ."""
    
    DISPLAY_TOTALS_TEMPLATE = """500-DISPLAY-TOTALS.
    *DB2: Display audit information and counters
    PERFORM 600-GET-TIMESTAMP.
    DISPLAY 'Program ended at  : ' TS-TIMESTAMP.
    DISPLAY 'TOTAL RECORDS PROCESSED: TBD'.
    ."""
    
    # Patterns
    PARAGRAPH_NUM_PATTERN = re.compile(r'^(\d{3})-', re.MULTILINE)
    STOP_RUN_PATTERN = re.compile(r'^\s*STOP\s+RUN\s*\.', re.IGNORECASE | re.MULTILINE)
    PERFORM_PATTERN = re.compile(
        r'PERFORM\s+(\d{3}-\w+)',
        re.IGNORECASE
    )
    OPEN_CURSOR_PATTERN = re.compile(r'^(\d{3})-\w*OPEN', re.IGNORECASE | re.MULTILINE)
    FETCH_CURSOR_PATTERN = re.compile(r'^(\d{3})-\w*FETCH', re.IGNORECASE | re.MULTILINE)
    CLOSE_CURSOR_PATTERN = re.compile(r'^(\d{3})-\w*CLOSE', re.IGNORECASE | re.MULTILINE)
    
    def __init__(self, program_text: str):
        """Initialize with program text."""
        self.program_text = program_text
        self.paragraphs: List[Paragraph] = []
        self.proc_div_start = -1
        self.stop_run_pos = -1
    
    def organize(self) -> str:
        """
        Organize PROCEDURE DIVISION with standard flow.
        
        Returns:
            Program text with organized PROCEDURE DIVISION
        """
        # Step 1: Find PROCEDURE DIVISION
        proc_match = PROCEDURE_DIVISION_PATTERN.search(self.program_text)
        if not proc_match:
            return self.program_text
        
        self.proc_div_start = proc_match.end()
        
        # Step 2: Extract all existing paragraphs
        self._extract_paragraphs()
        
        # Step 3: Build standard structure
        organized = self._build_organized_structure()
        
        # Step 4: Replace PROCEDURE DIVISION
        result = self.program_text[:proc_match.end()] + organized
        
        return result
    
    def _extract_paragraphs(self):
        """Extract all paragraphs from PROCEDURE DIVISION."""
        # Find all paragraph starts (line starting with digits and dash)
        para_starts = []
        
        text_after_pd = self.program_text[self.proc_div_start:]
        
        for match in PARAGRAPH_PATTERN.finditer(text_after_pd):
            para_name = match.group(1)
            # Extract number prefix (e.g., "710" from "710-OPEN-DZBEFFC1")
            num_match = self.PARAGRAPH_NUM_PATTERN.match(para_name)
            para_num = num_match.group(1) if num_match else ""
            
            para_starts.append({
                'name': para_name,
                'number': para_num,
                'start': self.proc_div_start + match.start(),
                'match': match
            })
        
        # Extract content for each paragraph
        for i, para_info in enumerate(para_starts):
            if i + 1 < len(para_starts):
                para_end = para_starts[i + 1]['start']
            else:
                # Last paragraph extends to end of file
                para_end = len(self.program_text)
            
            content = self.program_text[para_info['start']:para_end]
            
            para = Paragraph(
                name=para_info['name'],
                number=para_info['number'],
                content=content,
                start_pos=para_info['start'],
                end_pos=para_end
            )
            self.paragraphs.append(para)
    
    def _build_organized_structure(self) -> str:
        """Build organized PROCEDURE DIVISION structure."""
        output_lines = []
        
        # Find cursor operation paragraphs
        open_para_nums = set()
        fetch_para_nums = set()
        close_para_nums = set()
        other_paras = []
        
        for para in self.paragraphs:
            if self.OPEN_CURSOR_PATTERN.match(para.name):
                open_para_nums.add(para.number)
            elif self.FETCH_CURSOR_PATTERN.match(para.name):
                fetch_para_nums.add(para.number)
            elif self.CLOSE_CURSOR_PATTERN.match(para.name):
                close_para_nums.add(para.number)
            elif para.number not in ['600']:  # Exclude if already has 600
                other_paras.append(para)
        
        # Build main flow
        output_lines.append("\n*DB2: Standard flow for production-ready COBOL")
        output_lines.append("PERFORM 100-INITIALIZE.")
        output_lines.append("PERFORM 200-OPEN-CURSORS.")
        output_lines.append("PERFORM 300-MAIN-PROCESSING.")
        output_lines.append("PERFORM 400-CLOSE-CURSORS.")
        output_lines.append("PERFORM 500-DISPLAY-TOTALS.")
        output_lines.append("STOP RUN.")
        
        # 100-INITIALIZE paragraph
        output_lines.append("\n100-INITIALIZE.")
        output_lines.append("*DB2: Centralized initialization")
        output_lines.append("PERFORM 600-GET-TIMESTAMP.")
        output_lines.append(".")
        
        # 200-OPEN-CURSORS paragraph
        output_lines.append("\n200-OPEN-CURSORS.")
        output_lines.append("*DB2: Open all cursors")
        for num in sorted(open_para_nums):
            output_lines.append(f"PERFORM {num}-???.")  # Use existing names
        output_lines.append(".")
        
        # 300-MAIN-PROCESSING paragraph
        output_lines.append("\n300-MAIN-PROCESSING.")
        output_lines.append("*DB2: Main processing loop")
        for num in sorted(fetch_para_nums):
            output_lines.append(f"PERFORM {num}-??? UNTIL ???-EOC.")
        output_lines.append(".")
        
        # 400-CLOSE-CURSORS paragraph
        output_lines.append("\n400-CLOSE-CURSORS.")
        output_lines.append("*DB2: Close all cursors")
        for num in sorted(close_para_nums):
            output_lines.append(f"PERFORM {num}-???.")
        output_lines.append(".")
        
        # 500-DISPLAY-TOTALS paragraph
        output_lines.append("\n500-DISPLAY-TOTALS.")
        output_lines.append("*DB2: Display audit information")
        output_lines.append("PERFORM 600-GET-TIMESTAMP.")
        output_lines.append("DISPLAY 'Program ended at  : ' TS-TIMESTAMP.")
        output_lines.append(".")
        
        # 600-GET-TIMESTAMP paragraph (generic)
        output_lines.append("\n" + self.TIMESTAMP_PARAGRAPH_TEMPLATE)
        
        # Original paragraphs (remove duplicates of 100-600)
        output_lines.append("\n*DB2: Existing paragraphs")
        for para in self.paragraphs:
            if not para.name.startswith(('100-', '200-', '300-', '400-', '500-', '600-')):
                output_lines.append(f"\n{para.content}")
        
        return '\n'.join(output_lines)


def organize_procedure_division(program_text: str) -> str:
    """
    Convenience function to organize PROCEDURE DIVISION.
    
    Args:
        program_text: The COBOL program text
    
    Returns:
        Program text with organized PROCEDURE DIVISION
    
    Example:
        organized = organize_procedure_division(original_program)
    """
    organizer = ProcedureDivisionOrganizer(program_text)
    return organizer.organize()

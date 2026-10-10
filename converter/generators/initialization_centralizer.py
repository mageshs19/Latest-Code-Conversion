"""
INITIALIZATION CENTRALIZER

Consolidates all INITIALIZE statements into a single 100-INITIALIZE paragraph
instead of scattering them throughout the program.

Purpose:
  - DCLGEN groups are initialized ONCE at startup (in 100-INITIALIZE)
  - NOT in fetch loops (inefficient and bad practice)
  - NOT scattered throughout procedure division
  - Ensures proper COBOL structure and performance

Architecture:
  1. Collects all DCLGEN groups from program
  2. Creates single 100-INITIALIZE paragraph
  3. Removes duplicate INITIALIZE statements from fetch paragraphs
  4. Removes standalone INITIALIZE blocks after PROCEDURE DIVISION
  5. Integrates with program constants (CS-PROGRAM)
  6. Calls 600-GET-TIMESTAMP for audit trail

Usage:
  initialization_centralizer = InitializationCentralizer(program_text)
  cleaned_program = initialization_centralizer.process()
"""

import re
from typing import List, Set, Optional
from patterns.cobol_patterns import PROCEDURE_DIVISION_PATTERN, PARAGRAPH_PATTERN


class InitializationCentralizer:
    """Centralizes all INITIALIZE statements to 100-INITIALIZE paragraph."""
    
    # Patterns to identify DCLGEN groups and INITIALIZE statements
    DCLGEN_PATTERN = re.compile(
        r'(?:EXEC\s+SQL\s+INCLUDE|^\s*COPY)\s+(?P<group>DCL\w+)\b',
        re.IGNORECASE | re.MULTILINE
    )

    DCLGEN_REFERENCE_PATTERN = re.compile(
        r'(?::|\bOF\s+)(?P<group>DCL\w+)\b',
        re.IGNORECASE
    )
    
    INITIALIZE_PATTERN = re.compile(
        r'^\s*(?:\d{6}\s+)?INITIALIZE\s+(?P<group>\w+)\s*\.\s*$',
        re.IGNORECASE | re.MULTILINE
    )
    
    FETCH_PARAGRAPH_PATTERN = re.compile(
        r'^\s*(?P<para>\d{3}-\w+FETCH\w*)\s*\.\s*$',
        re.IGNORECASE | re.MULTILINE
    )
    
    INITIALIZE_HOST_GROUP_TEMPLATE = "INITIALIZE {group}."
    
    def __init__(self, program_text: str):
        """Initialize with program text."""
        self.program_text = program_text
        self.dclgen_groups: Set[str] = set()
        self.initialize_locations: List[tuple] = []  # (start, end, group_name)
        self.fetch_paragraphs: List[tuple] = []  # (start, end, para_name)
        
    def process(self) -> str:
        """
        Process program to centralize initialization.
        
        Returns:
            Cleaned program text with centralized 100-INITIALIZE
        """
        # Step 1: Find all DCLGEN groups in program
        self._find_dclgen_groups()
        
        # Step 2: Find all INITIALIZE statements to move/remove
        self._find_initialize_statements()
        
        # Step 3: Find all fetch paragraphs
        self._find_fetch_paragraphs()
        
        # Step 4: Remove INITIALIZE from fetch paragraphs
        result = self._remove_initialize_from_fetches()
        
        # Step 5: Create 100-INITIALIZE paragraph
        result = self._create_initialize_paragraph(result)
        
        # Step 6: Remove standalone INITIALIZE block after PROCEDURE DIVISION
        result = self._remove_standalone_initialize_block(result)
        
        # NOTE: Skipping Step 7 (ensure MOVE CS-PROGRAM replacement)
        # The 100-INITIALIZE paragraph already includes "MOVE CS-PROGRAM   TO PROGRAM-NAME"
        # so we don't need to search and replace literal MOVE statements
        # This method was causing duplicate MOVE statements with contaminated sequence numbers
        
        return result
    
    def _find_dclgen_groups(self):
        """Find all DCLGEN groups referenced in program."""
        for match in self.DCLGEN_PATTERN.finditer(self.program_text):
            group_name = match.group('group')
            self.dclgen_groups.add(group_name)

        for match in self.DCLGEN_REFERENCE_PATTERN.finditer(self.program_text):
            group_name = match.group('group')
            self.dclgen_groups.add(group_name)
    
    def _find_initialize_statements(self):
        """Find all INITIALIZE statements for DCLGEN groups."""
        for match in self.INITIALIZE_PATTERN.finditer(self.program_text):
            group_name = match.group('group')
            if group_name in self.dclgen_groups:
                self.initialize_locations.append((
                    match.start(),
                    match.end(),
                    group_name
                ))
    
    def _find_fetch_paragraphs(self):
        """Find all fetch paragraphs (720-*, 820-*, etc.)."""
        for match in self.FETCH_PARAGRAPH_PATTERN.finditer(self.program_text):
            self.fetch_paragraphs.append((
                match.start(),
                match.end(),
                match.group('para')
            ))
    
    def _remove_initialize_from_fetches(self) -> str:
        """
        Remove INITIALIZE statements from fetch paragraph prologues.
        
        Returns:
            Program text with fetch-prologue INITIALIZEs removed
        """
        result = self.program_text
        
        # Remove each INITIALIZE statement we found (go backwards to preserve positions)
        for start, end, group_name in sorted(self.initialize_locations, reverse=True):
            # Check if this INITIALIZE is in a fetch paragraph
            # (heuristic: check if within next 500 chars of a fetch line number)
            if self._is_in_fetch_context(start):
                # Replace with comment explaining it moved to 100-INITIALIZE
                line_start = result.rfind('\n', 0, start) + 1
                indent = len(result[line_start:start])
                comment = f"{'*':6}DB2: {group_name} initialized in 100-INITIALIZE\n"
                result = result[:line_start] + comment + result[end:]
        
        return result
    
    def _is_in_fetch_context(self, position: int) -> bool:
        """Check if position is within a fetch paragraph."""
        # Look back to find nearest paragraph marker
        lookback_window = self.program_text[max(0, position-500):position]
        if re.search(r'^\d{3}-\w*FETCH', lookback_window, re.MULTILINE):
            return True
        return False
    
    def _create_initialize_paragraph(self, program_text: str) -> str:
        """
        Create centralized 100-INITIALIZE paragraph.
        
        Inserts after PROCEDURE DIVISION line, before first paragraph.
        Includes:
          - All DCLGEN INITIALIZE statements
          - Program name move (CS-PROGRAM)
          - Timestamp initialization call
        
        NOTE: Generates lines WITHOUT sequence numbers (columns 73-80 empty).
        The FinalSequenceResequencerService will handle resequencing the entire
        output after this enhancement pipeline completes.
        
        Returns:
            Program text with new 100-INITIALIZE paragraph (format not resequenced)
        """
        # Find PROCEDURE DIVISION location
        proc_match = PROCEDURE_DIVISION_PATTERN.search(program_text)
        if not proc_match:
            return program_text
        
        proc_end = proc_match.end()
        
        # Find start of first paragraph after PROCEDURE DIVISION
        after_proc = program_text[proc_end:]
        first_para_match = PARAGRAPH_PATTERN.search(after_proc)
        
        if first_para_match:
            insert_point = proc_end + first_para_match.start()
        else:
            # No paragraphs? Insert after PROCEDURE DIVISION
            insert_point = proc_end
        
        # Build 100-INITIALIZE paragraph with proper indentation but NO sequence numbers
        # Lines will be formatted by caller with proper indentation
        init_para_lines = []
        
        # Blank line before paragraph
        init_para_lines.append("")
        
        # Paragraph name (no sequence numbers, just the code)
        init_para_lines.append("100-INITIALIZE.")
        
        # Comment line
        init_para_lines.append("*DB2: Centralized initialization (all DCLGEN groups, constants, timestamps)")
        
        # Add INITIALIZE for each DCLGEN group
        for group in sorted(self.dclgen_groups):
            init_para_lines.append(f"    INITIALIZE {group}.")
        
        # Add program name move
        if 'CS-PROGRAM' in program_text:
            init_para_lines.append("    MOVE CS-PROGRAM   TO PROGRAM-NAME.")
        
        # Add timestamp call
        init_para_lines.append("    PERFORM 600-GET-TIMESTAMP.")
        
        # Paragraph terminator
        init_para_lines.append("    .")
        
        # Blank line after paragraph
        init_para_lines.append("")
        
        init_paragraph = '\n'.join(init_para_lines) + '\n'
        
        # Insert at calculated position
        return (
            program_text[:insert_point] +
            init_paragraph +
            program_text[insert_point:]
        )
    
    def _remove_standalone_initialize_block(self, program_text: str) -> str:
        """
        Remove standalone INITIALIZE block that might appear after
        PROCEDURE DIVISION (from block_inserter.py).
        
        Pattern: Multiple consecutive INITIALIZE statements
        that look like they were inserted as a block.
        
        Returns:
            Program text with standalone block removed
        """
        # Find blocks of 2+ consecutive INITIALIZE statements
        pattern = re.compile(
            r'^\s*(?:\d{6}\s+)?INITIALIZE\s+\w+\s*\.\s*\n(?:\s*(?:\d{6}\s+)?INITIALIZE\s+\w+\s*\.\s*\n)+',
            re.MULTILINE
        )
        
        result = program_text
        for match in reversed(list(pattern.finditer(program_text))):
            # Check if this is right after PROCEDURE DIVISION
            # (within 2000 chars) and before any other code
            before_text = program_text[max(0, match.start()-2000):match.start()]
            if 'PROCEDURE DIVISION' in before_text:
                # Check if followed by more COBOL code (not just comments)
                after_text = program_text[match.end():match.end()+500]
                if re.search(r'^\s*(?:\d{3}-)?\w+', after_text, re.MULTILINE):
                    # This looks like the auto-generated block, mark for removal
                    # Replace with single comment
                    comment = "*DB2: Redundant INITIALIZE block removed (consolidated in 100-INITIALIZE)\n"
                    result = result[:match.start()] + comment + result[match.end():]
        
        return result

    def _ensure_variable_program_name_move(self, program_text: str) -> str:
        """
        Ensure MOVE CS-PROGRAM (not literal) TO PROGRAM-NAME.
        
        Replaces any literal MOVE 'xxx' TO PROGRAM-NAME with the correct
        variable form MOVE CS-PROGRAM TO PROGRAM-NAME to enable dynamic
        program identification at runtime.
        
        Pattern matches:
        - MOVE 'VMDZ7200' TO PROGRAM-NAME.
        - MOVE 'VM4BD420' TO PROGRAM-NAME.
        
        Replaces with:
        - MOVE CS-PROGRAM   TO PROGRAM-NAME.
        
        Returns:
            Program text with literal replaced by variable form
        """
        # Pattern to match MOVE 'literal' TO PROGRAM-NAME
        literal_pattern = re.compile(
            r"\bMOVE\s+'[^']+'\s+TO\s+PROGRAM-NAME\s*\.",
            re.IGNORECASE
        )
        
        # Replace literal with variable form
        result = literal_pattern.sub(
            "MOVE CS-PROGRAM   TO PROGRAM-NAME.",
            program_text
        )
        
        return result


def centralize_initialization(program_text: str) -> str:
    """
    Convenience function to centralize all initialization in a program.
    
    Args:
        program_text: The COBOL program text
    
    Returns:
        Program text with centralized 100-INITIALIZE
    
    Example:
        cleaned = centralize_initialization(original_program)
    """
    centralizer = InitializationCentralizer(program_text)
    return centralizer.process()

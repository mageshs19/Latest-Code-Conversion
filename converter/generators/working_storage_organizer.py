"""
WORKING-STORAGE ORGANIZER

Organizes all WORKING-STORAGE declarations into 10 standard sections
with clear separators and proper ordering.

Purpose:
  - All declarations organized logically by purpose
  - Clear section separators for readability
  - Consistent ordering across all programs
  - Audit fields (counters, timestamps) always present
  - Production-ready code organization

Standard 10-Section Organization:
  1. CONTROL-FIELDS      (CS-PROGRAM, program ID, etc.)
  2. COUNTER-FIELDS      (WS-NB-*-COUNT for audit)
  3. TIMESTAMP-FIELDS    (TS-SYSTEM, TS-TIMESTAMP)
  4. DATUMVELDEN         (Date work fields)
  5. DATE-CONVERSION-HELPERS (HELP-* fields)
  6. FLAGS               (Status flags, switches)
  7. WORK-FIELDS         (Temporary work variables)
  8. PARAMETER-DATA      (Parameter/external data)
  9. IMPORTED-SECTIONS   (COPY statements)
  10. DCLGEN-GROUPS      (SQL INCLUDE statements)

Usage:
  organizer = WorkingStorageOrganizer(program_text)
  organized = organizer.reorganize()
"""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SectionType(Enum):
    """Types of WORKING-STORAGE sections."""
    CONTROL_FIELDS = 1
    COUNTER_FIELDS = 2
    TIMESTAMP_FIELDS = 3
    DATUMVELDEN = 4
    DATE_HELPERS = 5
    FLAGS = 6
    WORK_FIELDS = 7
    PARAMETERS = 8
    IMPORTS = 9
    DCLGEN = 10


@dataclass
class Declaration:
    """Represents a WORKING-STORAGE declaration."""
    type: SectionType
    content: str  # Full text including line numbers
    level: int    # COBOL level (01, 05, 10, etc.)
    name: str     # Field name
    
    def __repr__(self):
        return f"Declaration({self.type.name}, {self.name})"


class WorkingStorageOrganizer:
    """Reorganizes WORKING-STORAGE into standard sections."""
    
    SECTION_HEADERS = {
        SectionType.CONTROL_FIELDS: "*-------- 1. CONTROL FIELDS --------*",
        SectionType.COUNTER_FIELDS: "*-------- 2. COUNTER FIELDS (Audit) --------*",
        SectionType.TIMESTAMP_FIELDS: "*-------- 3. TIMESTAMP FIELDS --------*",
        SectionType.DATUMVELDEN: "*-------- 4. DATE CONVERSION WORK FIELDS --------*",
        SectionType.DATE_HELPERS: "*-------- 5. DATE CONVERSION HELPERS --------*",
        SectionType.FLAGS: "*-------- 6. STATUS FLAGS --------*",
        SectionType.WORK_FIELDS: "*-------- 7. TEMPORARY WORK FIELDS --------*",
        SectionType.PARAMETERS: "*-------- 8. PARAMETER DATA --------*",
        SectionType.IMPORTS: "*-------- 9. IMPORTED SECTIONS --------*",
        SectionType.DCLGEN: "*-------- 10. DCLGEN GROUPS --------*",
    }
    
    SECTION_ORDER = [
        SectionType.CONTROL_FIELDS,
        SectionType.COUNTER_FIELDS,
        SectionType.TIMESTAMP_FIELDS,
        SectionType.DATUMVELDEN,
        SectionType.DATE_HELPERS,
        SectionType.FLAGS,
        SectionType.WORK_FIELDS,
        SectionType.PARAMETERS,
        SectionType.IMPORTS,
        SectionType.DCLGEN,
    ]
    
    # Patterns to identify sections
    WORKING_STORAGE_SECTION = re.compile(
        r'WORKING-STORAGE\s+SECTION\s*\.',
        re.IGNORECASE
    )
    
    PROCEDURE_DIVISION_PATTERN = re.compile(
        r'PROCEDURE\s+DIVISION\s*(?:USING.*?)?\.', 
        re.IGNORECASE | re.DOTALL
    )
    
    LEVEL_01_PATTERN = re.compile(
        r'^\s*(?:001\s+)?01\s+(?P<name>\w+)',
        re.IGNORECASE | re.MULTILINE
    )
    
    COPY_PATTERN = re.compile(
        r'^\s*COPY\s+\w+',
        re.IGNORECASE | re.MULTILINE
    )
    
    EXEC_SQL_INCLUDE_PATTERN = re.compile(
        r'EXEC\s+SQL\s+INCLUDE\s+\w+\s+END-EXEC',
        re.IGNORECASE
    )
    
    def __init__(self, program_text: str):
        """Initialize with program text."""
        self.program_text = program_text
        self.sections: Dict[SectionType, List[str]] = {s: [] for s in SectionType}
    
    def reorganize(self) -> str:
        """
        Reorganize WORKING-STORAGE into standard sections.
        
        Returns:
            Program text with reorganized WORKING-STORAGE
        """
        # Step 1: Extract WORKING-STORAGE content
        ws_content = self._extract_working_storage()
        if not ws_content:
            return self.program_text
        
        # Step 2: Parse declarations and categorize them
        self._categorize_declarations(ws_content)
        
        # Step 3: Generate organized WORKING-STORAGE
        organized_ws = self._generate_organized_sections()
        
        # Step 4: Replace original WORKING-STORAGE with organized version
        result = self._replace_working_storage(organized_ws)
        
        return result
    
    def _extract_working_storage(self) -> Optional[str]:
        """Extract WORKING-STORAGE section content."""
        ws_match = self.WORKING_STORAGE_SECTION.search(self.program_text)
        if not ws_match:
            return None
        
        ws_start = ws_match.end()
        
        # Find end (PROCEDURE DIVISION or FILE SECTION following, etc.)
        proc_match = self.PROCEDURE_DIVISION_PATTERN.search(
            self.program_text[ws_start:]
        )
        
        if proc_match:
            ws_end = ws_start + proc_match.start()
        else:
            ws_end = len(self.program_text)
        
        return self.program_text[ws_start:ws_end]
    
    def _categorize_declarations(self, ws_content: str):
        """
        Parse and categorize all declarations in WORKING-STORAGE.
        
        Uses pattern matching and heuristics to determine section type.
        Handles both 01-level groups and standalone level declarations (like counter fields).
        """
        lines = ws_content.split('\n')
        current_group = []
        standalone_fields = []  # For 10-level counter fields that appear standalone
        
        for line in lines:
            # Skip empty lines and comments
            if not line.strip() or line.strip().startswith('*'):
                if current_group:
                    current_group.append(line)
                elif standalone_fields:
                    standalone_fields.append(line)
                continue
                
            # Check if this starts a new top-level (01) group
            if re.match(r'\s*01\s+', line):
                if current_group:
                    self._categorize_group(current_group)
                if standalone_fields:
                    self._categorize_standalone_fields(standalone_fields)
                current_group = [line]
                standalone_fields = []
            # Check if this is a standalone level declaration (05, 10, etc.) outside a 01 group
            elif re.match(r'\s*(05|10|15|20|25|30)\s+', line) and not current_group:
                standalone_fields.append(line)
            else:
                if current_group:
                    current_group.append(line)
                elif standalone_fields:
                    standalone_fields.append(line)
        
        # Process last group
        if current_group:
            self._categorize_group(current_group)
        if standalone_fields:
            self._categorize_standalone_fields(standalone_fields)
        
        # Handle standalone COPY and EXEC SQL statements
        for line in lines:
            if self.COPY_PATTERN.match(line):
                self.sections[SectionType.IMPORTS].append(line)
            elif self.EXEC_SQL_INCLUDE_PATTERN.search(line):
                self.sections[SectionType.DCLGEN].append(line)
    
    def _categorize_group(self, group_lines: List[str]):
        """
        Categorize a group based on its structure and field names.
        
        Heuristics:
          - If contains 'COUNTER' or 'COUNT' → COUNTER-FIELDS
          - If contains 'TIMESTAMP' or 'TS-' → TIMESTAMP-FIELDS
          - If contains 'DATUM' or 'DATE' → DATUMVELDEN or DATE-HELPERS
          - If contains 'CS-PROGRAM' → CONTROL-FIELDS
          - If contains 'STATUS' or 'FLAG' → FLAGS
          - If name starts with 'ZONE-' → PARAMETERS
          - Default → WORK-FIELDS
        """
        if not group_lines:
            return
        
        # Get the 01-level name
        first_line = group_lines[0]
        name_match = re.search(r'01\s+(\w+)', first_line)
        if not name_match:
            return
        
        group_name = name_match.group(1).upper()
        group_content = '\n'.join(group_lines)
        
        # Determine section type
        if any(kw in group_name for kw in ['COUNTER', 'COUNT']):
            section_type = SectionType.COUNTER_FIELDS
        elif any(kw in group_name for kw in ['TIMESTAMP', 'TS-']):
            section_type = SectionType.TIMESTAMP_FIELDS
        elif 'DATUM' in group_name:
            section_type = SectionType.DATUMVELDEN
        elif 'HELPER' in group_name or 'HELP-' in group_name:
            section_type = SectionType.DATE_HELPERS
        elif 'CS-PROGRAM' in group_content:
            section_type = SectionType.CONTROL_FIELDS
        elif any(kw in group_name for kw in ['STATUS', 'FLAG', 'SWITCH']):
            section_type = SectionType.FLAGS
        elif 'ZONE-' in group_name or 'PARM' in group_name or 'PARAM' in group_name:
            section_type = SectionType.PARAMETERS
        else:
            section_type = SectionType.WORK_FIELDS
        
        # Add to appropriate section
        self.sections[section_type].append(group_content)
    
    def _categorize_standalone_fields(self, field_lines: List[str]):
        """
        Categorize standalone level declarations (not in a 01 group).
        
        Handles counter fields (10-level WS-NB-*-COUNT declarations) that appear
        outside of a 01 group. These are added by CounterDeclarationComposer.
        
        Args:
            field_lines: List of lines forming the standalone field declaration
        """
        if not field_lines:
            return
        
        # Join all lines
        field_content = '\n'.join(field_lines)
        
        # Determine section type based on field names and content
        if any(kw in field_content for kw in ['COUNTER', 'COUNT', 'WS-NB', 'TOTAL']):
            section_type = SectionType.COUNTER_FIELDS
        elif any(kw in field_content for kw in ['TIMESTAMP', 'TS-']):
            section_type = SectionType.TIMESTAMP_FIELDS
        elif any(kw in field_content for kw in ['DATUM', 'DATE']):
            section_type = SectionType.DATUMVELDEN
        elif any(kw in field_content for kw in ['STATUS', 'FLAG', 'SWITCH']):
            section_type = SectionType.FLAGS
        else:
            section_type = SectionType.WORK_FIELDS
        
        # Add to appropriate section
        self.sections[section_type].append(field_content)
    
    def _generate_organized_sections(self) -> str:
        """Generate reorganized WORKING-STORAGE section."""
        output_lines = ["WORKING-STORAGE SECTION."]
        
        for section_type in self.SECTION_ORDER:
            if self.sections[section_type]:
                # Add section header
                output_lines.append("")
                output_lines.append(self.SECTION_HEADERS[section_type])
                
                # Add declarations in this section
                for declaration in self.sections[section_type]:
                    output_lines.append(declaration)
        
        # Ensure blank line at end
        output_lines.append("")
        
        return '\n'.join(output_lines)
    
    def _replace_working_storage(self, organized_ws: str) -> str:
        """Replace original WORKING-STORAGE with organized version."""
        ws_match = self.WORKING_STORAGE_SECTION.search(self.program_text)
        if not ws_match:
            return self.program_text
        
        ws_start = ws_match.start()
        
        # Find end of WORKING-STORAGE (start of next section)
        after_ws = self.program_text[ws_start:]
        
        # Look for PROCEDURE DIVISION or FILE SECTION
        end_match = self.PROCEDURE_DIVISION_PATTERN.search(after_ws)
        if end_match:
            ws_end = ws_start + end_match.start()
        else:
            ws_end = len(self.program_text)
        
        # Replace
        return (
            self.program_text[:ws_start] +
            organized_ws + '\n' +
            self.program_text[ws_end:]
        )


def organize_working_storage(program_text: str) -> str:
    """
    Convenience function to organize WORKING-STORAGE into standard sections.
    
    Args:
        program_text: The COBOL program text
    
    Returns:
        Program text with organized WORKING-STORAGE
    
    Example:
        organized = organize_working_storage(original_program)
    """
    organizer = WorkingStorageOrganizer(program_text)
    return organizer.reorganize()

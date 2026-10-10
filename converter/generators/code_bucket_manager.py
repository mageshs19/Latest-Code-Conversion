"""
CODE BUCKET MANAGER

Organizes code generation into logical buckets (paragraphs/sections) that are
combined at the end to create well-formatted, organized output.

Architecture:
  - Each type of code (declarations, initializations, moves, writes) goes to its own bucket
  - Buckets are stored separately during generation
  - At the end, all buckets combine in a defined order
  - Produces clean, well-organized COBOL with proper separators

Benefits:
  - No scattered MOVE statements throughout the code
  - All declarations together
  - All initializations together
  - All field movements organized
  - All writes together
  - Easy to reorder or modify bucket order
  - Easy to add/remove entire buckets
  - Better for code review and maintenance

Bucket Types:
  1. WORKING_STORAGE_DECLARATIONS - All 01 and subordinate level declarations
  2. CONTROL_FIELDS - Program control fields (CS-PROGRAM, etc.)
  3. COUNTER_FIELDS - Audit counters (WS-NB-*-COUNT)
  4. TIMESTAMP_FIELDS - Date/time fields (TS-SYSTEM, TS-TIMESTAMP)
  5. STATUS_FLAGS - Condition flags (88 levels)
  6. WORK_FIELDS - Temporary work storage
  7. PARAMETER_DATA - Parameters and external data
  8. INITIALIZE_STATEMENTS - INITIALIZE paragraph statements
  9. FIELD_MOVES - MOVE statements for data transfer
 10. WRITE_STATEMENTS - WRITE statements for records
 11. FETCH_LOGIC - SELECT/FETCH cursor operations
 12. ERROR_HANDLING - Error checks and recovery
 13. PROCEDURE_PARAGRAPH - Main paragraphs of procedure division
 14. FINALIZATION - STOP RUN, cleanup

Usage:
  bucket_mgr = CodeBucketManager()
  
  # During generation, add to buckets
  bucket_mgr.add_to_bucket(BucketType.WORKING_STORAGE_DECLARATIONS, ws_decl_line)
  bucket_mgr.add_to_bucket(BucketType.FIELD_MOVES, move_statement)
  bucket_mgr.add_to_bucket(BucketType.WRITE_STATEMENTS, write_statement)
  
  # At the end, combine all buckets in order
  final_code = bucket_mgr.combine()
  
  # Or get specific bucket for insertion at exact location
  moves = bucket_mgr.get_bucket(BucketType.FIELD_MOVES)
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class BucketType(Enum):
    """Types of code buckets."""
    WORKING_STORAGE_DECLARATIONS = 1
    CONTROL_FIELDS = 2
    COUNTER_FIELDS = 3
    TIMESTAMP_FIELDS = 4
    STATUS_FLAGS = 5
    WORK_FIELDS = 6
    PARAMETER_DATA = 7
    INITIALIZE_STATEMENTS = 8
    FIELD_MOVES = 9
    WRITE_STATEMENTS = 10
    FETCH_LOGIC = 11
    ERROR_HANDLING = 12
    PROCEDURE_PARAGRAPH = 13
    FINALIZATION = 14


@dataclass
class BucketConfig:
    """Configuration for a bucket."""
    bucket_type: BucketType
    section_name: str  # Human-readable name
    separator: str = ""  # Optional separator line
    indent: int = 0  # Indentation for lines in this bucket
    skip_duplicates: bool = True  # Skip duplicate lines
    sort_lines: bool = False  # Sort lines alphabetically
    
    
class CodeBucketManager:
    """
    Manages code generation through logical buckets.
    
    This allows decoupled generation where different parts of code are
    written to buckets, then combined in a specific order at the end.
    """
    
    # Default bucket configuration and order
    DEFAULT_BUCKET_ORDER = [
        BucketType.WORKING_STORAGE_DECLARATIONS,
        BucketType.CONTROL_FIELDS,
        BucketType.COUNTER_FIELDS,
        BucketType.TIMESTAMP_FIELDS,
        BucketType.STATUS_FLAGS,
        BucketType.WORK_FIELDS,
        BucketType.PARAMETER_DATA,
        BucketType.INITIALIZE_STATEMENTS,
        BucketType.FIELD_MOVES,
        BucketType.WRITE_STATEMENTS,
        BucketType.FETCH_LOGIC,
        BucketType.ERROR_HANDLING,
        BucketType.PROCEDURE_PARAGRAPH,
        BucketType.FINALIZATION,
    ]
    
    DEFAULT_BUCKET_CONFIGS = {
        BucketType.WORKING_STORAGE_DECLARATIONS: BucketConfig(
            bucket_type=BucketType.WORKING_STORAGE_DECLARATIONS,
            section_name="WORKING-STORAGE DECLARATIONS",
            separator="*" + "-" * 60 + "*",
            skip_duplicates=True,
        ),
        BucketType.CONTROL_FIELDS: BucketConfig(
            bucket_type=BucketType.CONTROL_FIELDS,
            section_name="CONTROL FIELDS",
            separator="*-------- CONTROL FIELDS --------*",
            skip_duplicates=True,
        ),
        BucketType.COUNTER_FIELDS: BucketConfig(
            bucket_type=BucketType.COUNTER_FIELDS,
            section_name="COUNTER FIELDS (Audit)",
            separator="*-------- COUNTER FIELDS --------*",
            skip_duplicates=True,
        ),
        BucketType.TIMESTAMP_FIELDS: BucketConfig(
            bucket_type=BucketType.TIMESTAMP_FIELDS,
            section_name="TIMESTAMP FIELDS",
            separator="*-------- TIMESTAMP FIELDS --------*",
            skip_duplicates=True,
        ),
        BucketType.STATUS_FLAGS: BucketConfig(
            bucket_type=BucketType.STATUS_FLAGS,
            section_name="STATUS FLAGS",
            separator="*-------- STATUS FLAGS --------*",
            skip_duplicates=True,
        ),
        BucketType.WORK_FIELDS: BucketConfig(
            bucket_type=BucketType.WORK_FIELDS,
            section_name="WORK FIELDS",
            separator="*-------- WORK FIELDS --------*",
            skip_duplicates=True,
        ),
        BucketType.PARAMETER_DATA: BucketConfig(
            bucket_type=BucketType.PARAMETER_DATA,
            section_name="PARAMETER DATA",
            separator="*-------- PARAMETER DATA --------*",
            skip_duplicates=True,
        ),
        BucketType.INITIALIZE_STATEMENTS: BucketConfig(
            bucket_type=BucketType.INITIALIZE_STATEMENTS,
            section_name="100-INITIALIZE",
            separator="100-INITIALIZE.",
            skip_duplicates=True,
        ),
        BucketType.FIELD_MOVES: BucketConfig(
            bucket_type=BucketType.FIELD_MOVES,
            section_name="FIELD MOVE OPERATIONS",
            separator="*-------- FIELD MOVES --------*",
            skip_duplicates=True,
        ),
        BucketType.WRITE_STATEMENTS: BucketConfig(
            bucket_type=BucketType.WRITE_STATEMENTS,
            section_name="WRITE OPERATIONS",
            separator="*-------- WRITE STATEMENTS --------*",
            skip_duplicates=True,
        ),
        BucketType.FETCH_LOGIC: BucketConfig(
            bucket_type=BucketType.FETCH_LOGIC,
            section_name="FETCH CURSOR OPERATIONS",
            separator="*-------- FETCH LOGIC --------*",
            skip_duplicates=False,
        ),
        BucketType.ERROR_HANDLING: BucketConfig(
            bucket_type=BucketType.ERROR_HANDLING,
            section_name="ERROR HANDLING",
            separator="*-------- ERROR HANDLING --------*",
            skip_duplicates=True,
        ),
        BucketType.PROCEDURE_PARAGRAPH: BucketConfig(
            bucket_type=BucketType.PROCEDURE_PARAGRAPH,
            section_name="PROCEDURE DIVISION PARAGRAPHS",
            separator="*-------- PROCEDURE PARAGRAPHS --------*",
            skip_duplicates=False,
        ),
        BucketType.FINALIZATION: BucketConfig(
            bucket_type=BucketType.FINALIZATION,
            section_name="FINALIZATION",
            separator="*-------- FINALIZATION --------*",
            skip_duplicates=True,
        ),
    }
    
    def __init__(self, 
                 bucket_order: Optional[List[BucketType]] = None,
                 bucket_configs: Optional[Dict[BucketType, BucketConfig]] = None):
        """
        Initialize bucket manager.
        
        Args:
            bucket_order: Order to combine buckets (default: DEFAULT_BUCKET_ORDER)
            bucket_configs: Config for each bucket type (default: DEFAULT_BUCKET_CONFIGS)
        """
        self.bucket_order = bucket_order or self.DEFAULT_BUCKET_ORDER
        self.bucket_configs = bucket_configs or self.DEFAULT_BUCKET_CONFIGS
        
        # Initialize empty buckets
        self.buckets: Dict[BucketType, List[str]] = {
            bucket_type: [] 
            for bucket_type in BucketType
        }
        
    def add_to_bucket(self, bucket_type: BucketType, line: str) -> None:
        """
        Add a line to a specific bucket.
        
        Args:
            bucket_type: Which bucket to add to
            line: The line of code to add
        """
        if not line or not line.strip():
            return
            
        bucket = self.buckets[bucket_type]
        config = self.bucket_configs.get(bucket_type)
        
        # Skip duplicates if configured
        if config and config.skip_duplicates:
            if line in bucket:
                return
        
        bucket.append(line)
    
    def add_lines_to_bucket(self, bucket_type: BucketType, lines: List[str]) -> None:
        """
        Add multiple lines to a bucket.
        
        Args:
            bucket_type: Which bucket to add to
            lines: List of lines to add
        """
        for line in lines:
            self.add_to_bucket(bucket_type, line)
    
    def get_bucket(self, bucket_type: BucketType) -> List[str]:
        """
        Get all lines in a bucket without combining.
        
        Args:
            bucket_type: Which bucket to retrieve
            
        Returns:
            List of lines in the bucket
        """
        return self.buckets[bucket_type].copy()
    
    def clear_bucket(self, bucket_type: BucketType) -> None:
        """Clear all lines from a bucket."""
        self.buckets[bucket_type] = []
    
    def get_bucket_size(self, bucket_type: BucketType) -> int:
        """Get number of lines in a bucket."""
        return len(self.buckets[bucket_type])
    
    def is_bucket_empty(self, bucket_type: BucketType) -> bool:
        """Check if bucket has any lines."""
        return len(self.buckets[bucket_type]) == 0
    
    def combine(self, include_empty: bool = False, 
                line_separator: str = "\n") -> str:
        """
        Combine all buckets in order, with separators.
        
        Args:
            include_empty: Include sections even if bucket is empty
            line_separator: String to join lines (default: newline)
            
        Returns:
            Combined code as a single string
        """
        result_parts = []
        
        for bucket_type in self.bucket_order:
            bucket = self.buckets[bucket_type]
            
            # Skip empty buckets unless include_empty is True
            if not bucket and not include_empty:
                continue
            
            # Add section separator
            config = self.bucket_configs.get(bucket_type)
            if config and config.separator:
                result_parts.append(config.separator)
            
            # Add bucket lines
            if config and config.sort_lines:
                bucket = sorted(bucket)
            
            result_parts.extend(bucket)
            
            # Add blank line between sections
            if bucket:  # Only if bucket has content
                result_parts.append("")  # Blank line separator
        
        # Join with proper separator
        return line_separator.join(result_parts)
    
    def combine_to_section(self, section_name: str) -> str:
        """
        Combine all buckets and format for a COBOL section.
        
        Args:
            section_name: Name of section (e.g., "WORKING-STORAGE SECTION")
            
        Returns:
            Formatted section with combined buckets
        """
        section_header = f"{section_name}."
        combined = self.combine(include_empty=False)
        
        if not combined.strip():
            return section_header
        
        return f"{section_header}\n{combined}"
    
    def get_bucket_status(self) -> Dict[str, int]:
        """
        Get status of all buckets.
        
        Returns:
            Dictionary with bucket names and line counts
        """
        status = {}
        for bucket_type in BucketType:
            count = self.get_bucket_size(bucket_type)
            if count > 0:
                status[bucket_type.name] = count
        return status
    
    def reset(self) -> None:
        """Clear all buckets."""
        for bucket_type in BucketType:
            self.clear_bucket(bucket_type)
    
    def print_status(self) -> str:
        """
        Get a human-readable status report.
        
        Returns:
            Status report as string
        """
        status = self.get_bucket_status()
        if not status:
            return "All buckets are empty."
        
        lines = ["Code Bucket Status:"]
        total = 0
        for bucket_name, count in status.items():
            lines.append(f"  {bucket_name}: {count} lines")
            total += count
        lines.append(f"  TOTAL: {total} lines")
        
        return "\n".join(lines)


class CodeBucketBuilder:
    """
    Fluent interface for building code with buckets.
    
    Usage:
        builder = CodeBucketBuilder()
        builder.declare("01  WS-FIELD PIC X(10).") \\
               .initialize("INITIALIZE WS-REC.") \\
               .move("MOVE FIELD1 TO FIELD2.") \\
               .write("WRITE OUTPUT-RECORD.") \\
               .paragraph("400-PROCESS-DATA.")
        
        code = builder.build()
    """
    
    def __init__(self, manager: Optional[CodeBucketManager] = None):
        """Initialize builder with manager."""
        self.manager = manager or CodeBucketManager()
    
    def declare(self, line: str) -> "CodeBucketBuilder":
        """Add to WORKING_STORAGE_DECLARATIONS bucket."""
        self.manager.add_to_bucket(BucketType.WORKING_STORAGE_DECLARATIONS, line)
        return self
    
    def control_field(self, line: str) -> "CodeBucketBuilder":
        """Add to CONTROL_FIELDS bucket."""
        self.manager.add_to_bucket(BucketType.CONTROL_FIELDS, line)
        return self
    
    def counter(self, line: str) -> "CodeBucketBuilder":
        """Add to COUNTER_FIELDS bucket."""
        self.manager.add_to_bucket(BucketType.COUNTER_FIELDS, line)
        return self
    
    def timestamp_field(self, line: str) -> "CodeBucketBuilder":
        """Add to TIMESTAMP_FIELDS bucket."""
        self.manager.add_to_bucket(BucketType.TIMESTAMP_FIELDS, line)
        return self
    
    def flag(self, line: str) -> "CodeBucketBuilder":
        """Add to STATUS_FLAGS bucket."""
        self.manager.add_to_bucket(BucketType.STATUS_FLAGS, line)
        return self
    
    def work_field(self, line: str) -> "CodeBucketBuilder":
        """Add to WORK_FIELDS bucket."""
        self.manager.add_to_bucket(BucketType.WORK_FIELDS, line)
        return self
    
    def initialize(self, line: str) -> "CodeBucketBuilder":
        """Add to INITIALIZE_STATEMENTS bucket."""
        self.manager.add_to_bucket(BucketType.INITIALIZE_STATEMENTS, line)
        return self
    
    def move(self, line: str) -> "CodeBucketBuilder":
        """Add to FIELD_MOVES bucket."""
        self.manager.add_to_bucket(BucketType.FIELD_MOVES, line)
        return self
    
    def write(self, line: str) -> "CodeBucketBuilder":
        """Add to WRITE_STATEMENTS bucket."""
        self.manager.add_to_bucket(BucketType.WRITE_STATEMENTS, line)
        return self
    
    def fetch(self, line: str) -> "CodeBucketBuilder":
        """Add to FETCH_LOGIC bucket."""
        self.manager.add_to_bucket(BucketType.FETCH_LOGIC, line)
        return self
    
    def error(self, line: str) -> "CodeBucketBuilder":
        """Add to ERROR_HANDLING bucket."""
        self.manager.add_to_bucket(BucketType.ERROR_HANDLING, line)
        return self
    
    def paragraph(self, line: str) -> "CodeBucketBuilder":
        """Add to PROCEDURE_PARAGRAPH bucket."""
        self.manager.add_to_bucket(BucketType.PROCEDURE_PARAGRAPH, line)
        return self
    
    def finalize(self, line: str) -> "CodeBucketBuilder":
        """Add to FINALIZATION bucket."""
        self.manager.add_to_bucket(BucketType.FINALIZATION, line)
        return self
    
    def build(self) -> str:
        """Combine all buckets and return final code."""
        return self.manager.combine()
    
    def get_manager(self) -> CodeBucketManager:
        """Get the underlying bucket manager."""
        return self.manager

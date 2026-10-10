"""
CODE BUCKET MANAGER - INTEGRATION GUIDE

This guide shows how to refactor existing generators to use CodeBucketManager
to organize working storage, initializations, moves, and writes into logical buckets
that combine beautifully at the end.

QUICK EXAMPLE: Timestamp Generator Refactor
"""

from idms_db2_phase2.generators.code_bucket_manager import (
    CodeBucketManager, CodeBucketBuilder, BucketType
)


# ============================================================================
# EXAMPLE 1: SIMPLE FLUENT INTERFACE USAGE
# ============================================================================

def example_fluent_builder():
    """Simple example using fluent interface."""
    
    builder = CodeBucketBuilder()
    
    # Build code piece by piece, adding to appropriate buckets
    builder \
        .control_field("10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.") \
        .counter("01  WS-DZBFFSC1-FLAG             PIC X.") \
        .flag("    88  DZBEFFC1-NOT-EOC         VALUE 'N'.") \
        .flag("    88  DZBEFFC1-EOC             VALUE 'Y'.") \
        .timestamp_field("01  WS-TIMESTAMP-FIELDS.") \
        .timestamp_field("    05 TS-SYSTEM.") \
        .timestamp_field("        10  DA-SYS.") \
        .initialize("INITIALIZE DZBEFFTV.") \
        .initialize("INITIALIZE DCLDZBEFFTV.") \
        .move("MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK") \
        .move("MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID") \
        .write("WRITE UITRECORD")
    
    # Get final code with all buckets organized and combined
    final_code = builder.build()
    
    return final_code


# ============================================================================
# EXAMPLE 2: MANAGER INTERFACE FOR FINE-GRAINED CONTROL
# ============================================================================

def example_manager_interface():
    """Example using manager directly for more control."""
    
    manager = CodeBucketManager()
    
    # Add control fields
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, 
                         "10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.")
    
    # Add all counter/flag declarations as a group
    counter_lines = [
        "01  WS-DZBFFSC1-FLAG             PIC X.",
        "    88  DZBEFFC1-NOT-EOC         VALUE 'N'.",
        "    88  DZBEFFC1-EOC             VALUE 'Y'.",
    ]
    manager.add_lines_to_bucket(BucketType.STATUS_FLAGS, counter_lines)
    
    # Add timestamp fields
    timestamp_lines = [
        "01  WS-TIMESTAMP-FIELDS.",
        "    05 TS-SYSTEM.",
        "        10  DA-SYS.",
        "            15  DA-SYS-CCYY.",
        "                20  CC            PIC X(2).",
        "                20  YY            PIC X(2).",
    ]
    manager.add_lines_to_bucket(BucketType.TIMESTAMP_FIELDS, timestamp_lines)
    
    # Add initialization statements
    init_lines = [
        "INITIALIZE DZBEFFTV.",
        "INITIALIZE DCLDZBEFFTV.",
        "MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE",
    ]
    manager.add_lines_to_bucket(BucketType.INITIALIZE_STATEMENTS, init_lines)
    
    # Add move statements (grouped by logical operation)
    move_lines = [
        "MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK",
        "MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CND-STOCK",
        "MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID",
        "MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV TO UIT-NS-SEQ",
        "MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO UIT-DA-UBSEC",
        "MOVE NR-IDSTOCK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ST",
    ]
    manager.add_lines_to_bucket(BucketType.FIELD_MOVES, move_lines)
    
    # Add write statements
    manager.add_to_bucket(BucketType.WRITE_STATEMENTS, "WRITE UITRECORD")
    
    # Check status before combining
    print(manager.print_status())
    
    # Combine with proper formatting
    final_code = manager.combine()
    
    return final_code


# ============================================================================
# EXAMPLE 3: REFACTORING TIMESTAMP GENERATOR
# ============================================================================

class TimestampGeneratorRefactored:
    """
    Refactored TimestampGenerator using CodeBucketManager.
    
    BEFORE: Generated WORKING-STORAGE and paragraph code inline, scattered through methods
    AFTER: Uses buckets to organize code, combines at the end
    """
    
    def __init__(self):
        self.bucket_manager = CodeBucketManager()
    
    def generate_working_storage_timestamp_fields(self, program_id: str):
        """
        Generate timestamp working storage declarations.
        
        BEFORE: Returned a big string
        AFTER: Adds to appropriate buckets
        """
        # Control field with program ID
        self.bucket_manager.add_to_bucket(
            BucketType.CONTROL_FIELDS,
            f"10  CS-PROGRAM               PIC X(8)    VALUE '{program_id}'."
        )
        
        # Timestamp-related work fields
        ts_fields = [
            "01  WS-TIMESTAMP-FIELDS.",
            "    05 TS-SYSTEM.",
            "        10  DA-SYS.",
            "            15  DA-SYS-CCYY.",
            "                20  CC            PIC X(2).",
            "                20  YY            PIC X(2).",
            "            15  MM                PIC X(2).",
            "            15  DD                PIC X(2).",
            "        10  HR-SYS.",
            "            15  HH                PIC X(2).",
            "            15  MI                PIC X(2).",
            "            15  SS                PIC X(2).",
            "            15  TT                PIC X(2).",
            "    05 TS-TIMESTAMP.",
            "        10  CC                    PIC X(2).",
            "        10  YY                    PIC X(2).",
            "        10  TE-MARKER1            PIC X             VALUE '-'.",
            "        10  MM                    PIC X(2).",
            "        10  TE-MARKER2            PIC X             VALUE '-'.",
            "        10  DD                    PIC X(2).",
            "        10  TE-MARKER3            PIC X             VALUE '-'.",
            "        10  HH                    PIC X(2).",
            "        10  TE-MARKER4            PIC X             VALUE '.'.",
            "        10  MI                    PIC X(2).",
            "        10  TE-MARKER5            PIC X             VALUE '.'.",
            "        10  SS                    PIC X(2).",
            "        10  TE-MARKER6            PIC X             VALUE '.'.",
            "        10  TT                    PIC X(2).",
            "        10  NNNN                  PIC 9(04)         VALUE 0.",
        ]
        
        self.bucket_manager.add_lines_to_bucket(
            BucketType.TIMESTAMP_FIELDS,
            ts_fields
        )
    
    def generate_initialize_paragraph(self):
        """Generate 100-INITIALIZE paragraph statements."""
        init_statements = [
            "INITIALIZE DCLDZBEFFTV.",
            "INITIALIZE DZBEFFTV.",
            "PERFORM 600-GET-TIMESTAMP.",
        ]
        
        self.bucket_manager.add_lines_to_bucket(
            BucketType.INITIALIZE_STATEMENTS,
            init_statements
        )
    
    def generate_timestamp_paragraph(self):
        """Generate 600-GET-TIMESTAMP paragraph."""
        para_lines = [
            "600-GET-TIMESTAMP.",
            "    ACCEPT TS-SYSTEM FROM DATE YYYYMMDD.",
            "    ACCEPT HR-SYS FROM TIME.",
            "    STRING CC DELIMITED BY SIZE",
            "            '-' DELIMITED BY SIZE",
            "            MM DELIMITED BY SIZE",
            "            '-' DELIMITED BY SIZE",
            "            DD DELIMITED BY SIZE",
            "            '-' DELIMITED BY SIZE",
            "            HH DELIMITED BY SIZE",
            "            '.' DELIMITED BY SIZE",
            "            MI DELIMITED BY SIZE",
            "            '.' DELIMITED BY SIZE",
            "            SS DELIMITED BY SIZE",
            "            '.' DELIMITED BY SIZE",
            "            TT DELIMITED BY SIZE",
            "        INTO TS-TIMESTAMP.",
            "600-GET-TIMESTAMP-EXIT.",
            "    EXIT.",
        ]
        
        self.bucket_manager.add_lines_to_bucket(
            BucketType.PROCEDURE_PARAGRAPH,
            para_lines
        )
    
    def get_working_storage_section(self) -> str:
        """
        Get organized WORKING-STORAGE section.
        
        Combines all buckets in logical order:
        - Control fields
        - Counters (audit)
        - Timestamps
        - Status flags
        - Work fields
        """
        # Include only WORKING-STORAGE related buckets
        ws_buckets = [
            BucketType.CONTROL_FIELDS,
            BucketType.COUNTER_FIELDS,
            BucketType.TIMESTAMP_FIELDS,
            BucketType.STATUS_FLAGS,
            BucketType.WORK_FIELDS,
        ]
        
        # Create temporary manager with only WS buckets
        ws_manager = CodeBucketManager(bucket_order=ws_buckets)
        
        # Copy relevant buckets
        for bucket_type in ws_buckets:
            lines = self.bucket_manager.get_bucket(bucket_type)
            ws_manager.add_lines_to_bucket(bucket_type, lines)
        
        return ws_manager.combine_to_section("WORKING-STORAGE SECTION")
    
    def get_procedure_division_code(self) -> str:
        """Get organized PROCEDURE DIVISION code."""
        proc_buckets = [
            BucketType.INITIALIZE_STATEMENTS,
            BucketType.FETCH_LOGIC,
            BucketType.FIELD_MOVES,
            BucketType.WRITE_STATEMENTS,
            BucketType.ERROR_HANDLING,
            BucketType.PROCEDURE_PARAGRAPH,
        ]
        
        proc_manager = CodeBucketManager(bucket_order=proc_buckets)
        
        for bucket_type in proc_buckets:
            lines = self.bucket_manager.get_bucket(bucket_type)
            proc_manager.add_lines_to_bucket(bucket_type, lines)
        
        return proc_manager.combine()


# ============================================================================
# EXAMPLE 4: WORKING STORAGE ORGANIZER REFACTOR
# ============================================================================

class WorkingStorageOrganizerRefactored:
    """
    Refactored WorkingStorageOrganizer using CodeBucketManager.
    
    Original: Manually parses and reorganizes existing WS section
    Refactored: Can be used during generation to organize from the start
    """
    
    def __init__(self, program_text: str = ""):
        self.bucket_manager = CodeBucketManager()
        self.program_text = program_text
    
    def parse_and_organize_working_storage(self) -> str:
        """
        Parse existing WORKING-STORAGE and reorganize into buckets.
        
        Then combine for a clean, organized output.
        """
        # This would parse the program_text and extract declarations
        # Then add each to the appropriate bucket based on content
        
        # For example:
        # - Fields starting with CS- -> CONTROL_FIELDS
        # - Fields starting with WS-NB-*-COUNT -> COUNTER_FIELDS
        # - Fields starting with TS- -> TIMESTAMP_FIELDS
        # - Fields ending with -FLAG -> STATUS_FLAGS
        # etc.
        
        pass
    
    def add_control_field(self, line: str):
        """Add a control field line."""
        self.bucket_manager.add_to_bucket(BucketType.CONTROL_FIELDS, line)
    
    def add_counter_field(self, line: str):
        """Add a counter/audit field line."""
        self.bucket_manager.add_to_bucket(BucketType.COUNTER_FIELDS, line)
    
    def add_timestamp_field(self, line: str):
        """Add a timestamp field line."""
        self.bucket_manager.add_to_bucket(BucketType.TIMESTAMP_FIELDS, line)
    
    def add_status_flag(self, line: str):
        """Add a status flag line."""
        self.bucket_manager.add_to_bucket(BucketType.STATUS_FLAGS, line)
    
    def get_organized_section(self) -> str:
        """Get organized WORKING-STORAGE SECTION."""
        return self.bucket_manager.combine_to_section("WORKING-STORAGE SECTION")


# ============================================================================
# EXAMPLE 5: CURSOR PARAGRAPH GENERATOR REFACTOR
# ============================================================================

class CursorParagraphGeneratorRefactored:
    """
    Refactored CursorParagraphGenerator using CodeBucketManager.
    
    Separates cursor declarations, initializations, fetch logic, moves,
    and write statements into separate buckets that combine intelligently.
    """
    
    def __init__(self):
        self.bucket_manager = CodeBucketManager()
    
    def generate_cursor_declaration(self, cursor_name: str, select_stmt: str):
        """Add cursor declaration to appropriate bucket."""
        decl = f"EXEC SQL DECLARE {cursor_name} CURSOR FOR {select_stmt} END-EXEC."
        self.bucket_manager.add_to_bucket(
            BucketType.WORKING_STORAGE_DECLARATIONS,
            decl
        )
    
    def generate_fetch_loop(self, cursor_name: str, record_names: list):
        """Add fetch loop logic."""
        fetch_lines = [
            f"FETCH {cursor_name} INTO {', '.join(record_names)}",
            f"    EVALUATE SQLCODE",
            f"        WHEN 0",
            f"            PERFORM 200-PROCESS-ROW",
            f"        WHEN 100",
            f"            SET {cursor_name}-EOF TO TRUE",
            f"        WHEN OTHER",
            f"            PERFORM 900-ERROR-HANDLER",
            f"    END-EVALUATE",
        ]
        
        self.bucket_manager.add_lines_to_bucket(
            BucketType.FETCH_LOGIC,
            fetch_lines
        )
    
    def generate_field_moves_for_record(self, moves: list):
        """Add field move statements."""
        self.bucket_manager.add_lines_to_bucket(
            BucketType.FIELD_MOVES,
            moves
        )
    
    def generate_write_statements(self, writes: list):
        """Add write statements."""
        self.bucket_manager.add_lines_to_bucket(
            BucketType.WRITE_STATEMENTS,
            writes
        )
    
    def get_final_code(self) -> str:
        """Get all cursor-related code organized by bucket."""
        return self.bucket_manager.combine()
    
    def get_status(self) -> str:
        """Get status report."""
        return self.bucket_manager.print_status()


# ============================================================================
# USAGE PATTERN: INTEGRATION IN CONVERSION PIPELINE
# ============================================================================

def example_integration_in_pipeline():
    """
    Shows how to use CodeBucketManager in the conversion pipeline.
    
    This would replace the current scattered approach of generating code
    in different methods and having to carefully order and combine them.
    """
    
    # 1. Create main bucket manager for the program
    program_manager = CodeBucketManager()
    
    # 2. Timestamp generator adds to buckets
    ts_gen = TimestampGeneratorRefactored()
    ts_gen.generate_working_storage_timestamp_fields("VMDZ4420")
    ts_gen.generate_initialize_paragraph()
    ts_gen.generate_timestamp_paragraph()
    
    # Copy timestamp buckets to program manager
    for bucket_type in BucketType:
        lines = ts_gen.bucket_manager.get_bucket(bucket_type)
        program_manager.add_lines_to_bucket(bucket_type, lines)
    
    # 3. Cursor paragraph generator adds to buckets
    cursor_gen = CursorParagraphGeneratorRefactored()
    cursor_gen.generate_cursor_declaration("CURS-ITEMS", "SELECT * FROM ITEMS")
    cursor_gen.generate_fetch_loop("CURS-ITEMS", ["ITEM-REC"])
    cursor_gen.generate_field_moves_for_record([
        "MOVE ITEM-ID TO OUTPUT-ID",
        "MOVE ITEM-NAME TO OUTPUT-NAME",
    ])
    cursor_gen.generate_write_statements(["WRITE OUTPUT-RECORD"])
    
    # Copy cursor buckets to program manager
    for bucket_type in BucketType:
        lines = cursor_gen.bucket_manager.get_bucket(bucket_type)
        program_manager.add_lines_to_bucket(bucket_type, lines)
    
    # 4. At the end, combine everything in logical order
    final_working_storage = program_manager.combine_to_section("WORKING-STORAGE SECTION")
    final_procedure_division = program_manager.combine()
    
    print("WORKING-STORAGE organized:")
    print(final_working_storage)
    print("\nFull program code organized:")
    print(final_procedure_division)
    
    print("\nProgram Status:")
    print(program_manager.print_status())


# ============================================================================
# KEY BENEFITS OF THIS REFACTORING
# ============================================================================

"""
1. ORGANIZATION:
   - All declarations grouped together
   - All initializations together
   - All moves together
   - All writes together
   - No scattered code across methods

2. MAINTAINABILITY:
   - Easy to find which generator creates what
   - Easy to reorder sections
   - Easy to add new code types

3. FLEXIBILITY:
   - Can get subsets of code (just WS, just moves, etc.)
   - Can customize bucket order per generator
   - Can skip empty buckets or include them

4. DEBUGGING:
   - See bucket status to understand what was generated
   - Easy to trace where specific code comes from
   - Easy to identify missing pieces

5. BEAUTIFUL OUTPUT:
   - Proper separators between sections
   - No mixed code types
   - Consistent formatting
   - Blank line separation

REFACTORING ROADMAP:
1. Start with TimestampGenerator (simplest)
2. Move to WorkingStorageOrganizer (higher leverage)
3. Integrate into CursorParagraphGenerator (complex)
4. Update InitializationCentralizer (integrate with buckets)
5. Update conversion pipeline to use bucket managers
"""

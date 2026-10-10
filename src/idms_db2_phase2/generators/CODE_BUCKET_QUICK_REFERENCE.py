"""
CODE BUCKET MANAGER - QUICK REFERENCE GUIDE

A one-page reference for using CodeBucketManager in your generators.
"""

# ============================================================================
# IMPORT
# ============================================================================

from idms_db2_phase2.generators.code_bucket_manager import (
    CodeBucketManager, 
    CodeBucketBuilder, 
    BucketType
)


# ============================================================================
# QUICK START: THREE WAYS TO USE
# ============================================================================

# WAY 1: FLUENT BUILDER (SIMPLEST)
# ============================================================================
def way1_fluent_builder():
    """Use fluent interface for simple code generation."""
    
    builder = CodeBucketBuilder()
    
    builder.control_field("10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'.")
    builder.counter("01  WS-COUNT  PIC 9(9)  VALUE 0.")
    builder.flag("88  EOF-FLAG  VALUE 'Y'.")
    builder.initialize("INITIALIZE DCLDZBEFFTV.")
    builder.move("MOVE FIELD1 TO FIELD2.")
    builder.write("WRITE OUTPUT-REC.")
    
    # Get organized code
    code = builder.build()
    
    return code


# WAY 2: METHOD CHAINING (READABLE)
# ============================================================================
def way2_method_chaining():
    """Chain methods for compact, readable code."""
    
    code = CodeBucketBuilder() \
        .control_field("10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'.") \
        .counter("01  WS-COUNT  PIC 9(9).") \
        .flag("88  EOF  VALUE 'Y'.") \
        .initialize("INITIALIZE DCLDZBEFFTV.") \
        .move("MOVE FIELD1 TO FIELD2.") \
        .write("WRITE RECORD.") \
        .build()
    
    return code


# WAY 3: MANAGER WITH LISTS (FOR BULK ADD)
# ============================================================================
def way3_manager_with_lists():
    """Use manager for adding multiple lines at once."""
    
    manager = CodeBucketManager()
    
    # Add multiple lines at once
    control_fields = [
        "10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'.",
        "10  CS-VERSION  PIC X(5)  VALUE '1.0'.",
    ]
    manager.add_lines_to_bucket(BucketType.CONTROL_FIELDS, control_fields)
    
    timestamp_fields = [
        "01  WS-TIMESTAMP-FIELDS.",
        "    05 TS-SYSTEM.",
        "        10  DA-SYS  PIC 9(8).",
    ]
    manager.add_lines_to_bucket(BucketType.TIMESTAMP_FIELDS, timestamp_fields)
    
    init_stmts = [
        "INITIALIZE DZBEFFTV.",
        "INITIALIZE DCLDZBEFFTV.",
    ]
    manager.add_lines_to_bucket(BucketType.INITIALIZE_STATEMENTS, init_stmts)
    
    # Get organized code
    code = manager.combine()
    
    return code


# ============================================================================
# ALL FLUENT METHODS (QUICK REFERENCE)
# ============================================================================

def all_fluent_methods():
    """All available fluent methods on CodeBucketBuilder."""
    
    builder = CodeBucketBuilder()
    
    # WORKING-STORAGE declarations
    builder.declare("01  WS-FIELD  PIC X(10).")           # Generic declaration
    builder.control_field("10  CS-PROGRAM  PIC X(8).")    # Control field
    builder.counter("01  WS-COUNT  PIC 9(9).")            # Counter/audit
    builder.timestamp_field("01  TS-FIELDS.")             # Timestamp
    builder.flag("88  EOF  VALUE 'Y'.")                   # Status flag
    builder.work_field("01  WS-TEMP  PIC X(100).")        # Work field
    
    # PROCEDURE DIVISION code
    builder.initialize("INITIALIZE DZBEFFTV.")            # Initialize statements
    builder.fetch("FETCH CURS-ITEMS INTO REC.")           # Fetch logic
    builder.move("MOVE FIELD1 TO FIELD2.")                # Move statements
    builder.write("WRITE OUTPUT-REC.")                    # Write statements
    builder.error("IF SQLCODE NOT = 0...")                # Error handling
    builder.paragraph("200-PROCESS-DATA.")                # Paragraphs
    builder.finalize("STOP RUN.")                         # Finalization
    
    code = builder.build()
    return code


# ============================================================================
# WORKING WITH BUCKETS
# ============================================================================

def working_with_buckets():
    """Operations on buckets."""
    
    manager = CodeBucketManager()
    
    # Add single line
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, 
                         "10  CS-PROGRAM  PIC X(8).")
    
    # Add multiple lines
    lines = ["01  WS-FIELD1  PIC X(10).", "01  WS-FIELD2  PIC X(20)."]
    manager.add_lines_to_bucket(BucketType.WORK_FIELDS, lines)
    
    # Get lines from bucket (without combining)
    moves = manager.get_bucket(BucketType.FIELD_MOVES)
    print(f"Number of move statements: {len(moves)}")
    
    # Check bucket status
    size = manager.get_bucket_size(BucketType.CONTROL_FIELDS)
    is_empty = manager.is_bucket_empty(BucketType.INITIALIZE_STATEMENTS)
    
    # Clear a bucket
    if len(manager.get_bucket(BucketType.FIELD_MOVES)) > 10:
        manager.clear_bucket(BucketType.FIELD_MOVES)
    
    # Get status report
    print(manager.print_status())
    print(manager.get_bucket_status())


# ============================================================================
# COMBINING CODE
# ============================================================================

def combining_code():
    """Different ways to combine buckets into final code."""
    
    manager = CodeBucketManager()
    
    # Add some code to buckets
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, "10  CS-PROGRAM  PIC X(8).")
    manager.add_to_bucket(BucketType.INITIALIZE_STATEMENTS, "INITIALIZE DZBEFFTV.")
    manager.add_to_bucket(BucketType.FIELD_MOVES, "MOVE FIELD1 TO FIELD2.")
    
    # Option 1: Combine all buckets
    full_code = manager.combine()
    
    # Option 2: Combine with specific line separator
    code_with_separator = manager.combine(line_separator="\n")
    
    # Option 3: Format as COBOL section
    ws_section = manager.combine_to_section("WORKING-STORAGE SECTION")
    # Output: "WORKING-STORAGE SECTION.\n[combined buckets]"
    
    # Option 4: Get specific bucket only
    just_moves = manager.get_bucket(BucketType.FIELD_MOVES)
    
    return full_code


# ============================================================================
# REAL EXAMPLE: INTEGRATING WITH A GENERATOR
# ============================================================================

class MyGenerator:
    """Example of how to use CodeBucketManager in your generator."""
    
    def __init__(self):
        self.builder = CodeBucketBuilder()
    
    def generate(self):
        """Generate code by adding to buckets."""
        
        # Add control fields
        self.builder.control_field("10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'.")
        
        # Add working storage declarations
        self.builder.timestamp_field("01  WS-TIMESTAMP-FIELDS.")
        self.builder.timestamp_field("    05 TS-SYSTEM  PIC 9(8).")
        
        # Add initialization
        self.builder.initialize("INITIALIZE DZBEFFTV.")
        self.builder.initialize("PERFORM 600-GET-TIMESTAMP.")
        
        # Add field moves (group related ones)
        self.builder.move("MOVE FIELD1 TO FIELD2.")
        self.builder.move("MOVE FIELD3 TO FIELD4.")
        self.builder.move("MOVE FIELD5 TO FIELD6.")
        
        # Add write statement
        self.builder.write("WRITE OUTPUT-RECORD.")
        
        # Get organized code
        return self.builder.build()


# ============================================================================
# ADVANCED: CUSTOM BUCKET ORDER
# ============================================================================

def custom_bucket_order():
    """Use custom order for combining buckets."""
    
    # Default order: CONTROL -> COUNTER -> TIMESTAMP -> FLAGS -> ...
    # Custom order: Put TIMESTAMP first, then CONTROL, then everything else
    
    custom_order = [
        BucketType.TIMESTAMP_FIELDS,      # First
        BucketType.CONTROL_FIELDS,        # Second
        BucketType.COUNTER_FIELDS,        # Third
        BucketType.STATUS_FLAGS,
        BucketType.WORK_FIELDS,
        BucketType.INITIALIZE_STATEMENTS,
        BucketType.FIELD_MOVES,
        BucketType.WRITE_STATEMENTS,
    ]
    
    manager = CodeBucketManager(bucket_order=custom_order)
    
    # Add code as normal
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, "10  CS-PROGRAM...")
    manager.add_to_bucket(BucketType.TIMESTAMP_FIELDS, "01  TS-FIELDS...")
    
    # Will combine in custom_order sequence
    code = manager.combine()
    
    return code


# ============================================================================
# DEBUGGING: CHECK WHAT WAS GENERATED
# ============================================================================

def debugging_example():
    """How to debug/inspect bucket contents."""
    
    manager = CodeBucketManager()
    
    # Add some code
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, "10  CS-PROGRAM...")
    manager.add_to_bucket(BucketType.INITIALIZE_STATEMENTS, "INITIALIZE REC1.")
    manager.add_to_bucket(BucketType.INITIALIZE_STATEMENTS, "INITIALIZE REC2.")
    manager.add_to_bucket(BucketType.FIELD_MOVES, "MOVE F1 TO F2.")
    
    # Check what's in each bucket
    print("=== BUCKET STATUS ===")
    print(manager.print_status())
    
    print("\n=== BUCKET DETAILS ===")
    print(f"Control fields: {manager.get_bucket_size(BucketType.CONTROL_FIELDS)}")
    print(f"Init statements: {manager.get_bucket_size(BucketType.INITIALIZE_STATEMENTS)}")
    print(f"Field moves: {manager.get_bucket_size(BucketType.FIELD_MOVES)}")
    
    print("\n=== SPECIFIC BUCKET CONTENT ===")
    moves = manager.get_bucket(BucketType.FIELD_MOVES)
    for move in moves:
        print(f"  - {move}")
    
    print("\n=== COMBINED CODE ===")
    print(manager.combine())


# ============================================================================
# TIPS & BEST PRACTICES
# ============================================================================

"""
1. CHOOSE THE RIGHT METHOD:
   - Fluent builder for simple, linear code generation
   - Manager for complex scenarios with bulk operations
   - Builder is easier to read, Manager is more flexible

2. AVOID DUPLICATES:
   - Buckets skip duplicates by default
   - Set skip_duplicates=False in BucketConfig if you need duplicates

3. ORGANIZE BY PURPOSE:
   - Group related moves together
   - Add declares before initializes
   - Writes after moves

4. USE get_bucket() TO VERIFY:
   - Before combining, check what was generated
   - Use print_status() to see overall structure
   - Get individual bucket to debug issues

5. SEPARATE BY SECTION:
   - Create separate managers for WS and PROCEDURE
   - Combine appropriate buckets for each section
   - Use combine_to_section() for COBOL sections

6. INTEGRATE STEP BY STEP:
   - Start with one generator (e.g., TimestampGenerator)
   - Verify output matches original
   - Move to next generator
   - Don't try to refactor everything at once

7. TESTING:
   - Compare bucket-generated output with original
   - Test bucket status before combining
   - Verify separators and formatting
   - Check for missing declarations or statements
"""


# ============================================================================
# BUCKET TYPE REFERENCE
# ============================================================================

"""
BUCKET TYPES AND THEIR USE:

1. WORKING_STORAGE_DECLARATIONS
   Use: Generic 01-level declarations
   Default separator: "* - - - WORKING-STORAGE..."
   Example: "01  WS-FIELD  PIC X(10)."

2. CONTROL_FIELDS
   Use: Control/metadata fields (CS-PROGRAM, etc.)
   Example: "10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'."

3. COUNTER_FIELDS
   Use: Audit counters (WS-NB-*-COUNT)
   Example: "01  WS-NB-READS-COUNT  PIC 9(9)."

4. TIMESTAMP_FIELDS
   Use: Date and time related fields
   Example: "01  TS-SYSTEM  PIC 9(8)."

5. STATUS_FLAGS
   Use: Boolean flags and condition fields (88 levels)
   Example: "88  EOF  VALUE 'Y'."

6. WORK_FIELDS
   Use: Temporary working storage
   Example: "01  WS-TEMP-BUFFER  PIC X(1000)."

7. PARAMETER_DATA
   Use: Parameters and external data
   Example: "01  EXTERNAL-DATA  PIC X(50)."

8. INITIALIZE_STATEMENTS
   Use: All INITIALIZE statements (100-INITIALIZE paragraph)
   Example: "INITIALIZE DZBEFFTV."

9. FIELD_MOVES
   Use: All MOVE statements
   Example: "MOVE FIELD1 OF REC1 TO FIELD2 OF REC2."

10. WRITE_STATEMENTS
    Use: All WRITE statements
    Example: "WRITE OUTPUT-RECORD."

11. FETCH_LOGIC
    Use: SELECT/FETCH cursor operations
    Example: "FETCH CURSOR-NAME INTO HOST-REC."

12. ERROR_HANDLING
    Use: Error checking and recovery
    Example: "IF SQLCODE NOT = 0..."

13. PROCEDURE_PARAGRAPH
    Use: Main paragraphs of procedure division
    Example: "200-PROCESS-DATA."

14. FINALIZATION
    Use: Program termination (STOP RUN, etc.)
    Example: "STOP RUN."
"""


# ============================================================================
# COMMON PATTERNS
# ============================================================================

def pattern_separate_working_storage_from_procedure():
    """Generate WS section and PROCEDURE separately."""
    
    manager = CodeBucketManager()
    
    # Add code to various buckets
    manager.add_to_bucket(BucketType.CONTROL_FIELDS, "10  CS-PROGRAM...")
    manager.add_to_bucket(BucketType.INITIALIZE_STATEMENTS, "INITIALIZE REC.")
    manager.add_to_bucket(BucketType.FIELD_MOVES, "MOVE F1 TO F2.")
    
    # Working storage buckets
    ws_buckets = [
        BucketType.CONTROL_FIELDS,
        BucketType.TIMESTAMP_FIELDS,
        BucketType.STATUS_FLAGS,
    ]
    
    ws_manager = CodeBucketManager(bucket_order=ws_buckets)
    for bucket_type in ws_buckets:
        lines = manager.get_bucket(bucket_type)
        ws_manager.add_lines_to_bucket(bucket_type, lines)
    
    ws_code = ws_manager.combine_to_section("WORKING-STORAGE SECTION")
    
    # Procedure buckets
    proc_buckets = [
        BucketType.INITIALIZE_STATEMENTS,
        BucketType.FIELD_MOVES,
        BucketType.WRITE_STATEMENTS,
    ]
    
    proc_manager = CodeBucketManager(bucket_order=proc_buckets)
    for bucket_type in proc_buckets:
        lines = manager.get_bucket(bucket_type)
        proc_manager.add_lines_to_bucket(bucket_type, lines)
    
    proc_code = proc_manager.combine()
    
    return ws_code, proc_code

"""
COBOL Standard Initialization and Validation Rules (Issue #5).

Standards for applying COBOL best practices across all converted programs,
including counters, timestamps, and declarative validation sections.

This covers what the manual reference program includes that should be
standardized across all programs.

ISSUE #5 BREAKDOWN:
===================

5a) Processing Counters (D-2 in DEFERRED_DECISIONS)
    - Every program that processes records should have counters
    - Counters track rows read, rows written, errors
    - Counters are displayed at end-of-run (before STOP RUN)
    
    Status: AUTOMATE (approved by COBOL team)
    
    Counters declared:
        10  WS-NB-<TOKEN>-COUNT    PIC 9(7) COMP-3 VALUE ZEROES.
    
    where <TOKEN> is derived from:
    - Cursor/table name (middle part, distinctive)
    - "OUTPUT" for the output file counter
    
    Example:
        10  WS-NB-BEFF-COUNT       PIC 9(7) COMP-3 VALUE ZEROES.
        10  WS-NB-OUTPUT-COUNT     PIC 9(7) COMP-3 VALUE ZEROES.

5b) Timestamp Audit Fields
    - Programs should record start/end timestamps
    - Tracks when program executed and how long it ran
    - Stored in WORKING-STORAGE for end-of-run display
    
    Status: AUTOMATE (already in rules)
    
    Fields declared:
        01  WS-TIMESTAMPS.
            05  WS-EXEC-START-TIME   PIC 9(8) VALUE ZEROES.
            05  WS-EXEC-START-DATE   PIC 9(8) VALUE ZEROES.
            05  WS-EXEC-END-TIME     PIC 9(8) VALUE ZEROES.
            05  WS-EXEC-END-DATE     PIC 9(8) VALUE ZEROES.

5c) Program-Name Constant (D-4 in DEFERRED_DECISIONS)
    - Replace hardcoded MOVE 'VMDZ4420' TO PROGRAM-NAME
    - Use constant declared in WORKING-STORAGE
    
    Status: AUTOMATE (approved by COBOL team)
    
    Declared:
        10  CS-PROGRAM             PIC X(8)  VALUE 'VMDZ4420'.
    
    Used:
        MOVE CS-PROGRAM TO PROGRAM-NAME.

5d) DCLGEN Initialization (Issue #3)
    - Initialize all DCLGEN groups before processing
    - One-time initialization in dedicated paragraph (100-INITIALIZE)
    - NOT immediately after PROCEDURE DIVISION
    
    Status: ENFORCE (corrects placement issue)
    
    Declared:
        PROCEDURE DIVISION.
            PERFORM 100-INITIALIZE.
            PERFORM 200-OPEN-CURSORS.
        
        100-INITIALIZE.
            INITIALIZE DCLDZBEFFTV.
            INITIALIZE DCLDZEVEFTV.
            INITIALIZE DCLDZBEFF (if used).

5e) Counter Increment Logic
    - Every cursor FETCH loop should increment its counter
    - Output loop should increment output counter
    - Placement: immediately after successful operation
    
    Example:
        FETCH CURSOR-NAME
            MOVE DB2-FETCH-STATUS TO SQLCODE
            IF SQLCODE = 0
                ADD 1 TO WS-NB-BEFF-COUNT
                <-- Process record
            END-IF.

5f) End-of-Run Totals Display
    - Before STOP RUN, display all counters
    - Format: DISPLAY '<label> : ' <counter>
    - Labels should be descriptive and aligned
    
    Example:
        DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT
        DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT
        STOP RUN.

5g) Validation Display (Optional)
    - Can include validation counts (errors, warnings, skipped)
    - Helps verify conversion correctness
    - Status: OPTIONAL (pending COBOL team review)
    
    Examples:
        DISPLAY 'VALIDATION: errors encountered'
        DISPLAY 'VALIDATION: records skipped (missing key)'
        DISPLAY 'VALIDATION: date conversions applied'


STANDARD COBOL CHECKLIST FOR CONVERTED PROGRAMS:
=================================================
After conversion, every program should have:

WORKING-STORAGE additions:
- [ ] Program-name constant (CS-PROGRAM)
- [ ] Processing counters (WS-NB-<TOKEN>-COUNT) for each cursor
- [ ] Output file counter (WS-NB-OUTPUT-COUNT)
- [ ] Timestamp fields (WS-EXEC-START-TIME, etc.)
- [ ] DCLGEN initialization in dedicated paragraph (100-INITIALIZE)

PROCEDURE DIVISION structure:
- [ ] PERFORM 100-INITIALIZE before any processing
- [ ] Counter increment after each successful FETCH
- [ ] Counter increment after each successful output write
- [ ] End-of-run totals display before STOP RUN

VALIDATION:
- [ ] No hardcoded program names (use CS-PROGRAM)
- [ ] No hardcoded DCLGEN group names (use qualified OF references)
- [ ] All counters initialized to ZEROES
- [ ] All counters incremented correctly
- [ ] Timestamp fields populated (if used)
- [ ] DCLGEN groups initialized in 100-INITIALIZE paragraph


INTEGRATION WITH EXISTING RULES:
=================================
This standard depends on and integrates with:
- counter_rules.py (counter declaration and display)
- timestamp_audit_rules.py (timestamp field generation)
- initialization_placement_rules.py (DCLGEN initialization timing)
- field_mapping_standards.py (no hardcoded field names)
- db2_date_conversion_standards.py (date field conversion)


DECISION MATRIX (for COBOL team):
==================================
Feature              | Automate? | Status   | Owner | Date
---------------------|-----------|----------|-------|----------
Processing Counters  | YES       | APPROVED | Team  | [Date]
Timestamps           | YES       | APPROVED | Team  | [Date]
Program Constant     | YES       | APPROVED | Team  | [Date]
DCLGEN Init Placement| YES       | ENFORCE  | Team  | [Date]
Counter Increment    | YES       | AUTOMATE | Team  | [Date]
End-of-run Display   | YES       | AUTOMATE | Team  | [Date]
Validation Display   | OPTIONAL  | REVIEW   | Team  | [Date]
"""

from __future__ import annotations

# =====================================================================
# Master control switches
# =====================================================================
ENFORCE_COBOL_STANDARD_INITIALIZATION = True
EMIT_PROCESSING_COUNTERS = True
EMIT_TIMESTAMP_FIELDS = True
EMIT_PROGRAM_NAME_CONSTANT = True
EMIT_COUNTER_TOTALS_DISPLAY = True

# =====================================================================
# Section 5a: Processing Counters
# =====================================================================
COUNTER_DECLARATION_PARENT = "01  WS-CONTROL-FIELDS."
COUNTER_DECLARATION_LEVEL = "10"
COUNTER_NAME_TEMPLATE = "WS-NB-{token}-COUNT"
COUNTER_PICTURE = "PIC 9(7)    COMP-3 VALUE ZEROES."
OUTPUT_COUNTER_NAME = "WS-NB-OUTPUT-COUNT"
OUTPUT_COUNTER_LABEL = "TOTAL OUTPUT RECORDS"

# =====================================================================
# Section 5b: Timestamp Audit Fields
# =====================================================================
TIMESTAMP_SECTION_TEMPLATE = (
    "01  WS-TIMESTAMPS.\n"
    "    05  WS-EXEC-START-TIME   PIC 9(8) VALUE ZEROES.\n"
    "    05  WS-EXEC-START-DATE   PIC 9(8) VALUE ZEROES.\n"
    "    05  WS-EXEC-END-TIME     PIC 9(8) VALUE ZEROES.\n"
    "    05  WS-EXEC-END-DATE     PIC 9(8) VALUE ZEROES."
)

TIMESTAMP_CAPTURE_TIMING = {
    "start": "Before first PERFORM of main processing",
    "end": "Just before STOP RUN",
}

# =====================================================================
# Section 5c: Program-Name Constant
# =====================================================================
PROGRAM_CONSTANT_NAME = "CS-PROGRAM"
PROGRAM_CONSTANT_PICTURE = "PIC X(8)"
PROGRAM_CONSTANT_TEMPLATE = (
    "10  {name:<24} {picture}  VALUE '{program_id}'."
)
PROGRAM_NAME_MOVE_TEMPLATE = "MOVE {constant} TO PROGRAM-NAME"

# =====================================================================
# Section 5d: DCLGEN Initialization
# =====================================================================
INITIALIZATION_PARAGRAPH_NAME = "100-INITIALIZE"
INITIALIZATION_PARAGRAPH_RULE = (
    "All DCLGEN groups must be initialized in dedicated 100-INITIALIZE paragraph, "
    "called immediately after PROCEDURE DIVISION, before any processing"
)

# =====================================================================
# Section 5e: Counter Increment Logic
# =====================================================================
COUNTER_INCREMENT_TEMPLATE = "ADD 1 TO {counter_name}"
COUNTER_INCREMENT_PLACEMENT = "Immediately after successful FETCH or output write"

# =====================================================================
# Section 5f: End-of-Run Totals Display
# =====================================================================
COUNTER_DISPLAY_TEMPLATE = "DISPLAY '{label:<20} : ' {counter_name}"
TOTALS_DISPLAY_ANCHOR = "STOP RUN"
TOTALS_DISPLAY_INDENT = "    "

# =====================================================================
# Section 5g: Validation Display (Optional)
# =====================================================================
VALIDATION_DISPLAY_OPTIONS = [
    "DISPLAY 'VALIDATION: errors encountered'",
    "DISPLAY 'VALIDATION: records skipped'",
    "DISPLAY 'VALIDATION: date conversions applied'",
    "DISPLAY 'VALIDATION: timestamp fields populated'",
]

VALIDATION_DISPLAY_STATUS = "OPTIONAL (pending team review)"

# =====================================================================
# Standard checklist items
# =====================================================================
COBOL_STANDARD_CHECKLIST = {
    "working_storage_additions": [
        "Program-name constant (CS-PROGRAM)",
        "Processing counters (WS-NB-<TOKEN>-COUNT) for each cursor",
        "Output file counter (WS-NB-OUTPUT-COUNT)",
        "Timestamp fields (WS-EXEC-START-TIME, WS-EXEC-END-TIME)",
        "DCLGEN initialization in dedicated paragraph",
    ],
    "procedure_division_structure": [
        "PERFORM 100-INITIALIZE before any processing",
        "Counter increment after each successful FETCH",
        "Counter increment after each successful output write",
        "End-of-run totals display before STOP RUN",
    ],
    "validation_items": [
        "No hardcoded program names (use CS-PROGRAM)",
        "No hardcoded DCLGEN group names (use qualified OF)",
        "All counters initialized to ZEROES",
        "All counters incremented correctly",
        "Timestamp fields populated (if used)",
        "DCLGEN groups initialized in 100-INITIALIZE",
    ],
}

# =====================================================================
# Diagnostics
# =====================================================================
COBOL_STANDARD_MESSAGES = {
    "counter_declared": (
        "COBOL Standard: declared counter {name} for {token}."
    ),
    "timestamp_declared": (
        "COBOL Standard: declared timestamp fields."
    ),
    "program_constant_declared": (
        "COBOL Standard: declared program constant {name} = '{program_id}'."
    ),
    "init_paragraph_created": (
        "COBOL Standard: created {paragraph} for DCLGEN initialization."
    ),
    "counter_increment_added": (
        "COBOL Standard: added counter increment {counter_name} in {paragraph}."
    ),
    "totals_display_added": (
        "COBOL Standard: added {count} end-of-run total display line(s)."
    ),
    "hardcoded_name_detected": (
        "COBOL Standard: hardcoded program name on line {line}; "
        "should use {constant} instead."
    ),
}

# =====================================================================
# Integration dependencies
# =====================================================================
DEPENDS_ON_RULES = [
    "counter_rules.py",
    "timestamp_audit_rules.py",
    "initialization_placement_rules.py",
    "field_mapping_standards.py",
    "db2_date_conversion_standards.py",
]

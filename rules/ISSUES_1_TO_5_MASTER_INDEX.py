"""
IDMS-DB2 COBOL Conversion Standards — Master Index (All Issues Addressed).

This document consolidates Issues #1-#5 and references the corresponding
rules and standards files. Use this as the primary guide when converting
or validating converted COBOL programs.

QUICK START GUIDE:
==================
1. Read this file (ISSUES_1_TO_5_MASTER_INDEX.py) ← You are here
2. Read ISSUES_1_TO_5_CHANGES_1_2.py for Change 1 & 2 details
3. Read ISSUES_1_TO_5_PRACTICAL_EXAMPLE.py to see real code
4. Reference specific rules files for each issue

================================================================================
ISSUE #1: Date Conversion Standards (DA_* fields)
================================================================================

PROBLEM:
Date conversion logic was ad-hoc, sometimes placed incorrectly, sometimes
missing edge case handling.

SOLUTION:
All date conversions follow the STANDARD SEQUENCE documented in:
  - rules/db2_date_conversion_rules.py (templates)
  - rules/db2_date_conversion_standards.py (standards and checklist)
  - rules/db2_output_date_conversion_rules.py (output-specific rules)

KEY RULES:
1. Date conversion MUST happen BEFORE writing to output (not inside loop)
2. Edge cases MUST be handled explicitly:
   - '01.01.0001' (DB2 min) → '00000000' (COBOL zero)
   - '31.12.9999' (DB2 max) → '99999999' (COBOL high)
   - All others → realign from DD.MM.CCYY to CCYYMMDD

STANDARD SEQUENCE:
  PROCEDURE DIVISION.
      PERFORM 100-INITIALIZE.
  
  100-INITIALIZE.
      MOVE ZEROES TO DA-CCYYMMDD.
      MOVE ZEROES TO HELP-<field>.
  
  200-PROCESS-RECORD.
      MOVE <source-date> OF <DCLGEN-group> TO DA-DD-MM-CCYY.
      EVALUATE TRUE
          WHEN DA-DD-MM-CCYY = '01.01.0001'
              MOVE ZEROES TO DA-CCYYMMDD-R
          WHEN DA-DD-MM-CCYY = '31.12.9999'
              MOVE '99999999' TO DA-CCYYMMDD-R
          WHEN OTHER
              MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R
              MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R
              MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R
      END-EVALUATE.
      MOVE DA-CCYYMMDD-R TO <output-field>.

VALIDATION CHECKLIST:
  [ ] Date conversion before write, not in initialization
  [ ] Edge cases (01.01.0001, 31.12.9999) explicitly handled
  [ ] Helper fields initialized once at startup
  [ ] No hardcoded DCLGEN group names
  [ ] All DATE-type columns have conversion

FILES:
  - rules/db2_date_conversion_standards.py (read this first)
  - rules/db2_date_conversion_rules.py
  - rules/db2_output_date_conversion_rules.py
  - patterns/db2_date_patterns.py

================================================================================
ISSUE #2: Field Mapping Standards (MOVE statements)
================================================================================

PROBLEM:
MOVE statements from DCLGEN to output were sometimes unqualified, sometimes
hardcoded group names, sometimes mapped to wrong output fields.

SOLUTION:
All MOVE statements follow the QUALIFIED REFERENCE pattern documented in:
  - rules/field_mapping_standards.py
  - rules/field_mapping_rules.py

KEY RULES:
1. PREFERRED: Qualified reference
   MOVE <source-field> OF <DCLGEN-group> TO <output-field>
   Example: MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK

2. NOT RECOMMENDED: Unqualified reference
   MOVE <source-field> TO <output-field>
   Problem: Loses DCLGEN group context; unmaintainable

3. SPECIAL: Date fields require conversion (see Issue #1)
   MOVE <date-field> OF <group> TO DA-DD-MM-CCYY
   <-- (conversion sequence)
   MOVE DA-CCYYMMDD-R TO <output-field>

STANDARD PATTERN:
  INITIALIZE UIT-RECORD    <-- If needed
  MOVE AM-CNSTK OF DCLGEN-GROUP TO UIT-AM-CN-STOCK
  MOVE DA-UBSEC OF DCLGEN-GROUP TO DA-DD-MM-CCYY
  <-- (date conversion if DA is DATE type)
  MOVE DA-CCYYMMDD-R TO UIT-DA-UBSEC

VALIDATION CHECKLIST:
  [ ] All MOVE statements use qualified reference (OF <group>)
  [ ] Source field names match Sheet Mapping SOURCE exactly
  [ ] Target field names match Sheet Mapping TARGET exactly
  [ ] Date fields converted before MOVE
  [ ] No hardcoded DCLGEN group names
  [ ] Output record initialized if needed

FILES:
  - rules/field_mapping_standards.py (read this first)
  - rules/field_mapping_rules.py
  - catalogs/sheet_mapping_schema.py

================================================================================
ISSUE #3: DCLGEN Initialization Placement (Structure lifecycle)
================================================================================

PROBLEM:
INITIALIZE DCLGEN statements were appearing immediately after PROCEDURE DIVISION,
instead of in a dedicated initialization paragraph called before cursor open.

SOLUTION:
DCLGEN initialization follows CORRECT PLACEMENT documented in:
  - rules/initialization_placement_rules.py
  - rules/cobol_standard_initialization_rules.py

KEY RULES:
1. DCLGEN initialization MUST be in dedicated paragraph (100-INITIALIZE)
2. Called IMMEDIATELY after PROCEDURE DIVISION, BEFORE cursor open
3. Happens exactly ONCE at program startup
4. NOT inside fetch loop
5. NOT immediately after PROCEDURE DIVISION (the statement)

CORRECT STRUCTURE:
  PROCEDURE DIVISION.
      PERFORM 100-INITIALIZE.
      PERFORM 200-OPEN-CURSORS.
      PERFORM 300-MAIN-PROCESSING.
      PERFORM 400-CLOSE-CURSORS.
      STOP RUN.
  
  100-INITIALIZE.
      MOVE ZEROES TO DA-CCYYMMDD.
      INITIALIZE DCLDZBEFFTV.
      INITIALIZE DCLDZEVEFTV.
      <-- DCLGEN group initializations

  200-OPEN-CURSORS.
      OPEN CURSOR-NAME.

  300-MAIN-PROCESSING.
      <-- Fetch loop and processing

WRONG PATTERN (VIOLATION):
  PROCEDURE DIVISION.
      INITIALIZE DCLDZBEFFTV.    <-- WRONG: immediate after PROCEDURE DIVISION
      OPEN CURSOR-NAME.
      <-- This is illegal placement

VALIDATION CHECKLIST:
  [ ] DCLGEN initializations in 100-INITIALIZE paragraph
  [ ] 100-INITIALIZE called before any cursor operations
  [ ] No initializations immediately after PROCEDURE DIVISION
  [ ] No initializations inside fetch loop
  [ ] Initialization sequence: dedicated paragraph → open cursors → process

FILES:
  - rules/initialization_placement_rules.py (read this first)
  - rules/cobol_standard_initialization_rules.py

================================================================================
ISSUE #4: Program-Name Constant Replacement
================================================================================

PROBLEM:
Hardcoded program names like MOVE 'VMDZ4420' TO PROGRAM-NAME made programs
difficult to maintain and appeared in multiple places.

SOLUTION:
Program name is declared as a constant in WORKING-STORAGE, documented in:
  - rules/counter_rules.py (PROGRAM_CONSTANT_NAME, PROGRAM_CONSTANT_TEMPLATE)
  - rules/cobol_standard_initialization_rules.py

KEY RULES:
1. Program name stored in CS-PROGRAM constant (PIC X(8))
2. Declared once in WORKING-STORAGE
3. Used via MOVE CS-PROGRAM TO PROGRAM-NAME
4. No hardcoded program IDs in MOVE statements

CORRECT PATTERN:
  WORKING-STORAGE SECTION.
  01  WS-CONTROL-FIELDS.
      10  CS-PROGRAM             PIC X(8)  VALUE 'VMDZ4420'.
  
  PROCEDURE DIVISION.
      MOVE CS-PROGRAM TO PROGRAM-NAME.
      <-- Uses the constant, not hardcoded string

WRONG PATTERN (VIOLATION):
  PROCEDURE DIVISION.
      MOVE 'VMDZ4420' TO PROGRAM-NAME.
      <-- Hardcoded; cannot be changed without editing multiple lines

VALIDATION CHECKLIST:
  [ ] CS-PROGRAM constant declared in WORKING-STORAGE
  [ ] Program name equals constant at startup
  [ ] No hardcoded 'VMDZ####' strings in MOVE statements
  [ ] PROGRAM-NAME field always uses CS-PROGRAM constant

FILES:
  - rules/counter_rules.py (see PROGRAM_CONSTANT_* constants)
  - rules/cobol_standard_initialization_rules.py

================================================================================
ISSUE #5: COBOL Standard Initialization and Validation
================================================================================

PROBLEM:
Converted programs were missing standard COBOL audit fields (counters,
timestamps) that provide operational visibility and traceability. Also,
programs weren't following consistent COBOL standards.

SOLUTION:
All converted programs include standard COBOL initialization and validation,
documented in:
  - rules/cobol_standard_initialization_rules.py (master guide)
  - rules/counter_rules.py (counters specifically)
  - rules/counter_declaration_rules.py (counter declaration templates)

KEY RULES:
1. Every program must have processing counters
2. Every program must have end-of-run totals display
3. Program constants and timestamp fields standard
4. DCLGEN initialization in dedicated paragraph (100-INITIALIZE)
5. Counter increments after each successful operation

5a) PROCESSING COUNTERS
  One counter per cursor (rows fetched) + one for output file
  
  WORKING-STORAGE:
    10  WS-NB-BEFF-COUNT        PIC 9(7) COMP-3 VALUE ZEROES.
    10  WS-NB-OUTPUT-COUNT      PIC 9(7) COMP-3 VALUE ZEROES.
  
  Procedure:
    FETCH CURSOR-BEFF
        IF SQLCODE = 0
            ADD 1 TO WS-NB-BEFF-COUNT
            <-- Process and write output
            ADD 1 TO WS-NB-OUTPUT-COUNT
        END-IF.

5b) TIMESTAMP AUDIT FIELDS
  Track program execution start/end times
  
  WORKING-STORAGE:
    01  WS-TIMESTAMPS.
        05  WS-EXEC-START-TIME   PIC 9(8) VALUE ZEROES.
        05  WS-EXEC-START-DATE   PIC 9(8) VALUE ZEROES.
        05  WS-EXEC-END-TIME     PIC 9(8) VALUE ZEROES.
        05  WS-EXEC-END-DATE     PIC 9(8) VALUE ZEROES.
  
  Procedure:
    ACCEPT WS-EXEC-START-TIME FROM TIME.
    ACCEPT WS-EXEC-START-DATE FROM DATE.
    <-- Main processing
    ACCEPT WS-EXEC-END-TIME FROM TIME.
    ACCEPT WS-EXEC-END-DATE FROM DATE.

5c) PROGRAM-NAME CONSTANT (see Issue #4)
  WORKING-STORAGE:
    10  CS-PROGRAM             PIC X(8) VALUE 'VMDZ4420'.

5d) END-OF-RUN TOTALS DISPLAY
  Before STOP RUN, display all counters
  
  PROCEDURE DIVISION closing:
    DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT
    DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT
    DISPLAY 'PROGRAM RUN TIME  : ' WS-EXEC-END-TIME
    STOP RUN.

STANDARD WORKING-STORAGE SECTION (combined):
  01  WS-CONTROL-FIELDS.
      10  CS-PROGRAM                PIC X(8)  VALUE 'VMDZ4420'.
      10  WS-NB-BEFF-COUNT          PIC 9(7) COMP-3 VALUE ZEROES.
      10  WS-NB-OUTPUT-COUNT        PIC 9(7) COMP-3 VALUE ZEROES.
  
  01  WS-TIMESTAMPS.
      05  WS-EXEC-START-TIME        PIC 9(8) VALUE ZEROES.
      05  WS-EXEC-START-DATE        PIC 9(8) VALUE ZEROES.
      05  WS-EXEC-END-TIME          PIC 9(8) VALUE ZEROES.
      05  WS-EXEC-END-DATE          PIC 9(8) VALUE ZEROES.
  
  01  WS-DATUMVELDEN.               <-- From Issue #1 (date conversion)
      03  DA-CCYYMMDD.
          05  CC                    PIC 99       VALUE ZERO.
          05  YY                    PIC 99       VALUE ZERO.
          05  MM                    PIC 99       VALUE ZERO.
          05  DD                    PIC 99       VALUE ZERO.
      03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.
          05  CCYY                  PIC 9999.
          05  MM                    PIC 99.
          05  DD                    PIC 99.
      03  DA-DD-MM-CCYY.
          05  DD                    PIC 9(02).
          05  TE-MARKER5            PIC X        VALUE '.'.
          05  MM                    PIC 9(02).
          05  TE-MARKER6            PIC X        VALUE '.'.
          05  CCYY                  PIC 9(04).

PROCEDURE DIVISION STRUCTURE:
  PROCEDURE DIVISION.
      PERFORM 100-INITIALIZE.
      PERFORM 200-OPEN-CURSORS.
      PERFORM 300-MAIN-PROCESSING.
      PERFORM 400-CLOSE-CURSORS.
      PERFORM 500-DISPLAY-TOTALS.
      STOP RUN.
  
  100-INITIALIZE.
      MOVE ZEROES TO DA-CCYYMMDD.
      INITIALIZE DCLDZBEFFTV.
      ACCEPT WS-EXEC-START-TIME FROM TIME.
      ACCEPT WS-EXEC-START-DATE FROM DATE.
  
  300-MAIN-PROCESSING.
      FETCH CURSOR-NAME
          IF SQLCODE = 0
              ADD 1 TO WS-NB-BEFF-COUNT
              <-- Process fields
              ADD 1 TO WS-NB-OUTPUT-COUNT
          END-IF.
  
  500-DISPLAY-TOTALS.
      ACCEPT WS-EXEC-END-TIME FROM TIME.
      ACCEPT WS-EXEC-END-DATE FROM DATE.
      DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT
      DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT.

VALIDATION CHECKLIST:
  [ ] Processing counters declared for each cursor
  [ ] Output file counter declared
  [ ] Timestamp fields declared
  [ ] Program constant CS-PROGRAM declared
  [ ] DCLGEN initialization in 100-INITIALIZE
  [ ] Counter increment after each FETCH
  [ ] Counter increment after each output write
  [ ] End-of-run totals display before STOP RUN
  [ ] No hardcoded program names
  [ ] All counters initialized to ZEROES

FILES:
  - rules/cobol_standard_initialization_rules.py (read this first)
  - rules/counter_rules.py
  - rules/counter_declaration_rules.py
  - rules/initialization_placement_rules.py

================================================================================
QUICK START: Apply All 5 Issues to a Program
================================================================================

1. READ THE STANDARDS
   - rules/db2_date_conversion_standards.py
   - rules/field_mapping_standards.py
   - rules/initialization_placement_rules.py
   - rules/cobol_standard_initialization_rules.py

2. CHECK WORKING-STORAGE
   [ ] Has CS-PROGRAM constant
   [ ] Has counters (WS-NB-*-COUNT)
   [ ] Has timestamp fields (WS-EXEC-*)
   [ ] Has date conversion work fields (DA-CCYYMMDD, DA-DD-MM-CCYY)
   [ ] Has helper fields for each date source (HELP-*)

3. CHECK PROCEDURE DIVISION STRUCTURE
   [ ] Starts with PERFORM 100-INITIALIZE
   [ ] 100-INITIALIZE has DCLGEN initializations
   [ ] Cursor OPEN after initialization
   [ ] Counter increments after FETCH/WRITE
   [ ] End-of-run display before STOP RUN

4. CHECK FIELD MAPPINGS
   [ ] All MOVE statements use qualified reference (OF <group>)
   [ ] All date fields have conversion before MOVE
   [ ] No hardcoded DCLGEN group names
   [ ] No hardcoded program names

5. VALIDATE WITH CHECKLIST
   Run the validation checklist for each issue:
   - Issue #1: Date Conversion Checklist
   - Issue #2: Field Mapping Checklist
   - Issue #3: Initialization Placement Checklist
   - Issue #4: Program Constant Checklist
   - Issue #5: COBOL Standard Checklist

================================================================================
RELATED DOCUMENTATION
================================================================================

- manual_conventions/README.md — Why these standards exist
- manual_conventions/DEFERRED_DECISIONS.md — Decision status (D-1 through D-10)
- rules/ folder — All rule files (180+ files)
- patterns/ folder — Pattern recognition (regex files)
- catalogs/sheet_mapping_schema.py — Sheet Mapping structure
- code_review/ folder — Code review framework

================================================================================
QUESTIONS?
================================================================================

1. "My date conversion logic looks different" → Check Issue #1 standard sequence
2. "My MOVE statements are unqualified" → Check Issue #2 field mapping rules
3. "Where should INITIALIZE go?" → Check Issue #3 initialization placement rules
4. "Should I hardcode the program name?" → Check Issue #4 (use CS-PROGRAM)
5. "What COBOL fields are standard?" → Check Issue #5 standard checklist

For manual reference program examples, see:
- VMDZ4420_*.cbl (recent conversion with all standards applied)
- INTEGRATION_EXAMPLE.md (walkthrough example)
"""

from __future__ import annotations

# This is a documentation-only file.
# It serves as the master index for all 5 issues and their solutions.
# No code logic belongs here — it's reference documentation.

ISSUES_ADDRESSED = [
    "Issue #1: Date Conversion Standards (DA_* fields)",
    "Issue #2: Field Mapping Standards (MOVE statements)",
    "Issue #3: DCLGEN Initialization Placement",
    "Issue #4: Program-Name Constant Replacement",
    "Issue #5: COBOL Standard Initialization and Validation",
]

FILES_TO_READ = {
    "Issue #1": [
        "rules/db2_date_conversion_standards.py",
        "rules/db2_date_conversion_rules.py",
        "rules/db2_output_date_conversion_rules.py",
    ],
    "Issue #2": [
        "rules/field_mapping_standards.py",
        "rules/field_mapping_rules.py",
    ],
    "Issue #3": [
        "rules/initialization_placement_rules.py",
        "rules/cobol_standard_initialization_rules.py",
    ],
    "Issue #4": [
        "rules/counter_rules.py",
        "rules/cobol_standard_initialization_rules.py",
    ],
    "Issue #5": [
        "rules/cobol_standard_initialization_rules.py",
        "rules/counter_rules.py",
        "rules/counter_declaration_rules.py",
    ],
}

DEFERRED_DECISIONS_RELATED = {
    "D-2": "Processing counters (Issue #5)",
    "D-4": "Commit-flow restructure (separate decision)",
    "D-8": "Program-name constant (Issue #4)",
    "D-9": "DCLGEN initialization placement (Issue #3)",
    "D-10": "COBOL standard initialization (Issue #5)",
}

"""
Practical Example: Applying All 5 Issues to a COBOL Program

This example shows a BEFORE-and-AFTER conversion, demonstrating how to apply
all 5 standards to a real IDMS→DB2 conversion.

================================================================================
EXAMPLE PROGRAM: VMDZ4420 (with all 5 issues)
================================================================================

SCENARIO:
- Input: IDMS COBOL program reading BEFF record, outputting to file
- Includes a DATE field (DA-UBSECIS) needing conversion
- Needs counters and audit fields for standard COBOL practices
- Manual reference shows how it should look after conversion

================================================================================
WORKING-STORAGE SECTION (AFTER)
================================================================================

This shows the correct WORKING-STORAGE structure addressing all issues:

    WORKING-STORAGE SECTION.
    
    * --- Issue #4: Program-Name Constant
    * --- Issue #5: Processing Counters and Control Fields
    01  WS-CONTROL-FIELDS.
        10  CS-PROGRAM                 PIC X(8)       VALUE 'VMDZ4420'.
        10  WS-NB-BEFF-COUNT           PIC 9(7)       COMP-3 VALUE ZEROES.
        10  WS-NB-OUTPUT-COUNT         PIC 9(7)       COMP-3 VALUE ZEROES.
    
    * --- Issue #5: Timestamp Audit Fields
    01  WS-TIMESTAMPS.
        05  WS-EXEC-START-TIME         PIC 9(8)       VALUE ZEROES.
        05  WS-EXEC-START-DATE         PIC 9(8)       VALUE ZEROES.
        05  WS-EXEC-END-TIME           PIC 9(8)       VALUE ZEROES.
        05  WS-EXEC-END-DATE           PIC 9(8)       VALUE ZEROES.
    
    * --- Issue #1: Date Conversion Work Fields
    01  WS-DATUMVELDEN.
        03  DA-CCYYMMDD.
            05  CC                      PIC 99         VALUE ZERO.
            05  YY                      PIC 99         VALUE ZERO.
            05  MM                      PIC 99         VALUE ZERO.
            05  DD                      PIC 99         VALUE ZERO.
        03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.
            05  CCYY                    PIC 9999.
            05  MM                      PIC 99.
            05  DD                      PIC 99.
        03  DA-DD-MM-CCYY.
            05  DD                      PIC 9(02).
            05  TE-MARKER5              PIC X          VALUE '.'.
            05  MM                      PIC 9(02).
            05  TE-MARKER6              PIC X          VALUE '.'.
            05  CCYY                    PIC 9(04).
    
    * --- Issue #1: Date Helper Fields (one per date source)
    * --- Issue #2: Qualified reference via Sheet Mapping
    01  WS-OUTPUT-DATE-HELPERS.
        02  HELP-UIT-DA-UBSEC            PIC 9(8)     VALUE ZEROES.
    
    * --- Include DCLGEN groups
    EXEC SQL INCLUDE DCLDZBEFFTV END-EXEC.
    EXEC SQL INCLUDE DCLDZEVEFTV END-EXEC.
    
    * --- File record definition
    FD  OUTPUT-FILE.
    01  UIT-OUTPUT-RECORD.
        05  UIT-AM-CN-STOCK             PIC X(10).
        05  UIT-AM-CND-STOCK            PIC X(10).
        05  UIT-DA-UBSEC                PIC 9(8).
        05  FILLER                      PIC X(50).

================================================================================
PROCEDURE DIVISION (AFTER)
================================================================================

PROCEDURE DIVISION.
    
    * --- Issue #3: Dedicated 100-INITIALIZE paragraph (Issue #5)
    PERFORM 100-INITIALIZE.
    
    * --- Standard flow
    PERFORM 200-OPEN-CURSORS.
    PERFORM 300-MAIN-PROCESSING.
    PERFORM 400-CLOSE-CURSORS.
    PERFORM 500-DISPLAY-TOTALS.
    STOP RUN.

* -----------------------------------------------------------------------
* 100-INITIALIZE — Paragraph dedicated to startup (Issue #3, #5)
* -----------------------------------------------------------------------
100-INITIALIZE.
    * --- Initialize all DCLGEN groups (Issue #3)
    INITIALIZE DCLDZBEFFTV.
    INITIALIZE DCLDZEVEFTV.
    
    * --- Initialize date work fields (Issue #1)
    MOVE ZEROES TO DA-CCYYMMDD.
    
    * --- Initialize date helper fields (Issue #1)
    MOVE ZEROES TO HELP-UIT-DA-UBSEC.
    
    * --- Issue #4: Set program name from constant
    MOVE CS-PROGRAM TO PROGRAM-NAME.
    
    * --- Issue #5: Capture start timestamp
    ACCEPT WS-EXEC-START-TIME FROM TIME.
    ACCEPT WS-EXEC-START-DATE FROM DATE.
    .

* -----------------------------------------------------------------------
* 200-OPEN-CURSORS — Open all DB2 cursors
* -----------------------------------------------------------------------
200-OPEN-CURSORS.
    OPEN CURSOR-BEFF.
    .

* -----------------------------------------------------------------------
* 300-MAIN-PROCESSING — Main processing loop (Issues #1, #2, #5)
* -----------------------------------------------------------------------
300-MAIN-PROCESSING.
    PERFORM UNTIL SQLCODE NOT = 0
        FETCH CURSOR-BEFF
            MOVE DB2-FETCH-STATUS TO SQLCODE
        
        IF SQLCODE = 0
            * --- Issue #5: Increment counter after successful FETCH
            ADD 1 TO WS-NB-BEFF-COUNT
            
            * --- Issue #2: Qualified field reference (from DCLGEN)
            MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV 
                TO UIT-AM-CN-STOCK
            MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV 
                TO UIT-AM-CND-STOCK
            
            * --- Issue #1: Date conversion BEFORE output write
            * --- (follows standard sequence from db2_date_conversion_standards.py)
            PERFORM 350-CONVERT-DATE-UBSEC
            
            * --- Issue #2: Output field receives converted date
            MOVE HELP-UIT-DA-UBSEC TO UIT-DA-UBSEC
            
            * --- Write output record
            WRITE UIT-OUTPUT-RECORD
            
            * --- Issue #5: Increment counter after successful write
            ADD 1 TO WS-NB-OUTPUT-COUNT
        END-IF
    END-PERFORM.
    .

* -----------------------------------------------------------------------
* 350-CONVERT-DATE-UBSEC — Date conversion (Issue #1 standard)
* -----------------------------------------------------------------------
* This paragraph implements the standard date conversion sequence for
* DA-UBSECIS field. All date conversions follow this same pattern.
* -----------------------------------------------------------------------
350-CONVERT-DATE-UBSEC.
    * --- Step 1: Initialize helper fields
    MOVE ZEROES TO DA-CCYYMMDD.
    MOVE ZEROES TO HELP-UIT-DA-UBSEC.
    
    * --- Step 2: Move source date to work field
    MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY.
    
    * --- Step 3: Evaluate and convert (edge cases explicit)
    EVALUATE TRUE
        WHEN DA-DD-MM-CCYY = '01.01.0001'
            MOVE ZEROES TO DA-CCYYMMDD-R
        WHEN DA-DD-MM-CCYY = '31.12.9999'
            MOVE '99999999' TO DA-CCYYMMDD-R
        WHEN OTHER
            MOVE CCYY OF DA-DD-MM-CCYY 
                TO CCYY OF DA-CCYYMMDD-R
            MOVE MM   OF DA-DD-MM-CCYY 
                TO MM   OF DA-CCYYMMDD-R
            MOVE DD   OF DA-DD-MM-CCYY 
                TO DD   OF DA-CCYYMMDD-R
    END-EVALUATE.
    
    * --- Step 4: Move converted date to helper
    MOVE DA-CCYYMMDD-R TO HELP-UIT-DA-UBSEC.
    .

* -----------------------------------------------------------------------
* 400-CLOSE-CURSORS — Close all DB2 cursors
* -----------------------------------------------------------------------
400-CLOSE-CURSORS.
    CLOSE CURSOR-BEFF.
    .

* -----------------------------------------------------------------------
* 500-DISPLAY-TOTALS — Issue #5: Display counters before STOP RUN
* -----------------------------------------------------------------------
500-DISPLAY-TOTALS.
    * --- Capture end timestamp
    ACCEPT WS-EXEC-END-TIME FROM TIME.
    ACCEPT WS-EXEC-END-DATE FROM DATE.
    
    * --- Display counters
    DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT.
    DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT.
    .

================================================================================
VALIDATION CHECKLIST (All 5 Issues Addressed)
================================================================================

ISSUE #1: Date Conversion
[X] Date conversion happens BEFORE output write (paragraph 350-CONVERT-DATE-UBSEC)
[X] Edge cases handled explicitly ('01.01.0001' and '31.12.9999')
[X] Helper field initialized once at startup (HELP-UIT-DA-UBSEC)
[X] DA-CCYYMMDD work fields declared in WORKING-STORAGE
[X] Conversion sequence follows standard (MOVE→EVALUATE→MOVE)
[X] No hardcoded DCLGEN group names (uses OF qualified reference)

ISSUE #2: Field Mapping
[X] All MOVE statements use qualified reference (OF DCLDZBEFFTV)
[X] Source field names from Sheet Mapping (AM-CNSTK-479BEFF, etc.)
[X] Target field names from Sheet Mapping (UIT-AM-CN-STOCK, etc.)
[X] Date field converted before MOVE to output
[X] No unqualified field references
[X] No hardcoded DCLGEN group names

ISSUE #3: DCLGEN Initialization Placement
[X] INITIALIZE statements in dedicated 100-INITIALIZE paragraph
[X] 100-INITIALIZE called immediately after PROCEDURE DIVISION
[X] No initializations immediately after PROCEDURE DIVISION statement
[X] No initializations inside fetch loop
[X] Initialization paragraph called before cursor open

ISSUE #4: Program-Name Constant
[X] CS-PROGRAM constant declared in WORKING-STORAGE
[X] CS-PROGRAM has correct program ID ('VMDZ4420')
[X] MOVE CS-PROGRAM TO PROGRAM-NAME (not hardcoded string)
[X] No hardcoded program names in MOVE statements

ISSUE #5: COBOL Standard Initialization
[X] WS-NB-BEFF-COUNT counter declared
[X] WS-NB-OUTPUT-COUNT counter declared
[X] Timestamp fields declared (WS-EXEC-START-*, WS-EXEC-END-*)
[X] CS-PROGRAM constant declared
[X] Counter incremented after FETCH success
[X] Counter incremented after output write
[X] End-of-run display before STOP RUN
[X] All counters initialized to ZEROES
[X] DCLGEN initialization in 100-INITIALIZE

================================================================================
KEY DIFFERENCES FROM BEFORE (What Changed)
================================================================================

BEFORE (Problems):
    PROCEDURE DIVISION.
    INITIALIZE DCLDZBEFFTV.           <- Wrong placement (Issue #3)
    OPEN CURSOR-BEFF.
    MOVE 'VMDZ4420' TO PROGRAM-NAME.  <- Hardcoded (Issue #4)
    
    PERFORM UNTIL SQLCODE NOT = 0
        FETCH CURSOR-BEFF
        IF SQLCODE = 0
            MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV 
                TO UIT-AM-CN-STOCK          <- Good (Issue #2)
            MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV
                TO UIT-DA-UBSEC             <- Bad: no conversion (Issue #1)
            WRITE UIT-OUTPUT-RECORD
        END-IF
    END-PERFORM.
    
    STOP RUN.                           <- No counters (Issue #5)

AFTER (All standards applied):
    PROCEDURE DIVISION.
    PERFORM 100-INITIALIZE.            <- Dedicated paragraph (Issue #3)
    PERFORM 200-OPEN-CURSORS.
    PERFORM 300-MAIN-PROCESSING.
    PERFORM 400-CLOSE-CURSORS.
    PERFORM 500-DISPLAY-TOTALS.
    STOP RUN.
    
    100-INITIALIZE.
        INITIALIZE DCLDZBEFFTV.        <- Correct placement (Issue #3)
        MOVE ZEROES TO DA-CCYYMMDD.
        MOVE ZEROES TO HELP-UIT-DA-UBSEC.
        MOVE CS-PROGRAM TO PROGRAM-NAME. <- Constant (Issue #4)
        ACCEPT WS-EXEC-START-TIME FROM TIME. <- Audit (Issue #5)
    
    300-MAIN-PROCESSING.
        PERFORM UNTIL SQLCODE NOT = 0
            FETCH CURSOR-BEFF
            IF SQLCODE = 0
                ADD 1 TO WS-NB-BEFF-COUNT.  <- Counter (Issue #5)
                MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV
                    TO UIT-AM-CN-STOCK
                PERFORM 350-CONVERT-DATE-UBSEC.
                MOVE HELP-UIT-DA-UBSEC TO UIT-DA-UBSEC. <- Converted (Issue #1)
                WRITE UIT-OUTPUT-RECORD
                ADD 1 TO WS-NB-OUTPUT-COUNT.  <- Counter (Issue #5)
            END-IF
        END-PERFORM.
    
    350-CONVERT-DATE-UBSEC.
        MOVE ZEROES TO DA-CCYYMMDD.
        MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY.
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
        MOVE DA-CCYYMMDD-R TO HELP-UIT-DA-UBSEC.
    
    500-DISPLAY-TOTALS.
        ACCEPT WS-EXEC-END-TIME FROM TIME.   <- Audit (Issue #5)
        DISPLAY 'TOTAL BEFF RECORDS   : '
            WS-NB-BEFF-COUNT.
        DISPLAY 'TOTAL OUTPUT RECORDS : '
            WS-NB-OUTPUT-COUNT.

================================================================================
IMPLEMENTATION STEPS (For Your Own Program)
================================================================================

Step 1: Read the standards
  - rules/ISSUES_1_TO_5_MASTER_INDEX.py (this file points to everything)
  - rules/db2_date_conversion_standards.py
  - rules/field_mapping_standards.py
  - rules/initialization_placement_rules.py
  - rules/cobol_standard_initialization_rules.py

Step 2: Update WORKING-STORAGE
  - Add CS-PROGRAM constant (Issue #4)
  - Add counters (WS-NB-*-COUNT) for each cursor (Issue #5)
  - Add timestamps (Issue #5)
  - Verify date work fields (Issue #1)

Step 3: Update PROCEDURE DIVISION
  - Create 100-INITIALIZE paragraph (Issue #3)
  - Move INITIALIZE statements into 100-INITIALIZE (Issue #3)
  - Call 100-INITIALIZE first thing (Issue #3)
  - Add MOVE CS-PROGRAM to replace hardcoded name (Issue #4)

Step 4: Update field mappings
  - Check all MOVE statements use qualified reference (Issue #2)
  - For DATE fields, add conversion paragraph (Issue #1)
  - Increment counters after successful operations (Issue #5)

Step 5: Validate
  - Run the validation checklist above
  - Compare output structure to this example
  - Test end-of-run display
  - Verify all counters increment correctly

================================================================================
QUESTIONS?
================================================================================

Q: "Should I create this by hand, or does the converter do it?"
A: The converter SHOULD generate all of this automatically if configured
   correctly with the rules files. If you're seeing violations, either:
   1. The converter version is outdated (run git pull)
   2. The Sheet Mapping is incomplete
   3. The rule is disabled in rules/counter_rules.py, etc.

Q: "What if my date field format is different?"
A: The standard handles DD.MM.CCYY input format. If your source date is
   different, check Sheet Mapping DATATYPE column. If not DATE, no
   conversion is applied (check if this is correct).

Q: "Can I skip any of the 5 issues?"
A: No. All 5 are standards:
   - Issue #1: Date conversion is MANDATORY for all DATE fields
   - Issue #2: Field mapping is MANDATORY (qualified references)
   - Issue #3: Initialization placement is MANDATORY (100-INITIALIZE)
   - Issue #4: Program constant is STANDARD (every program)
   - Issue #5: COBOL audit fields are STANDARD (every program)

Q: "What if this example doesn't match my output?"
A: File a conversion issue with your program name and a comparison.
   This example represents the STANDARD. Deviations indicate either:
   1. A bug in the converter (report it)
   2. A Sheet Mapping error (fix input data)
   3. A rule that needs adjustment (discuss with COBOL team)
"""

from __future__ import annotations

# This is a documentation and example file.
# No executable code logic belongs here.

EXAMPLE_PROGRAM = "VMDZ4420"
EXAMPLE_ISSUES_ADDRESSED = [
    "Issue #1: Date Conversion Standards",
    "Issue #2: Field Mapping Standards",
    "Issue #3: DCLGEN Initialization Placement",
    "Issue #4: Program-Name Constant",
    "Issue #5: COBOL Standard Initialization",
]

EXPECTED_SECTIONS = {
    "100-INITIALIZE": "Startup and DCLGEN initialization",
    "200-OPEN-CURSORS": "Cursor open",
    "300-MAIN-PROCESSING": "Fetch loop with counter increments",
    "350-CONVERT-DATE-*": "Date conversion (one per DATE field)",
    "400-CLOSE-CURSORS": "Cursor close",
    "500-DISPLAY-TOTALS": "Counter and timestamp display",
}

VALIDATION_CHECKLIST_COUNT = 25  # Approximately 25 items to check

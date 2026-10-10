"""
Change 1 & 2: Program Constant Style and Generic Timestamp Paragraph

This document shows how to apply both standardized changes to any program:

Change 1: CS-PROGRAM Declaration and Usage Style
Change 2: Generic 600-GET-TIMESTAMP Paragraph

Both changes are REUSABLE ACROSS ALL PROGRAMS and enforce COBOL standards
for consistency and maintainability.

================================================================================
CHANGE 1: CS-PROGRAM Constant — Formatting Standard
================================================================================

WHAT IS IT?
- Program name stored as a constant in WORKING-STORAGE
- Used everywhere instead of hardcoded 'VMDZ4420' strings
- Standard formatting ensures alignment across all programs

WORKING-STORAGE DECLARATION:
-----------------------------

01  WS-CONTROL-FIELDS.
    10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.
    10  WS-NB-BEFF-COUNT         PIC 9(7) COMP-3 VALUE ZEROES.
    10  WS-NB-OUTPUT-COUNT       PIC 9(7) COMP-3 VALUE ZEROES.

    Key formatting:
    - Line starts with "10  " (level and spaces)
    - Field name: left-aligned in 28-character column
    - "PIC X(8)" (4 spaces before PIC)
    - "VALUE" (4 spaces before VALUE)
    - String in single quotes: 'VMDZ4420'
    - Period at end

PROCEDURE USAGE:
----------------

    MOVE CS-PROGRAM   TO PROGRAM-NAME.

    Key formatting:
    - "MOVE " (uppercase)
    - Constant name: CS-PROGRAM
    - "   TO " (3 spaces before TO, 1 space after)
    - Target field name: PROGRAM-NAME
    - Period at end

STYLE RULES:
- Field name is left-aligned in 28-character column (including "CS-PROGRAM")
- "PIC X(8)" always has 4 spaces before it
- "VALUE" always has 4 spaces before it
- MOVE uses 3 spaces after constant name, 3 spaces before TO
- All alignment is consistent with other COBOL declarations

EXAMPLE (from VMDZ4420):
    10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.
    MOVE CS-PROGRAM   TO PROGRAM-NAME.

NEVER (violations):
    MOVE 'VMDZ4420' TO PROGRAM-NAME.           <- Hardcoded
    10  CS-PROGRAM PIC X(8) VALUE 'VMDZ4420'.  <- Wrong alignment
    MOVE CS-PROGRAM TO PROGRAM-NAME.           <- Wrong spacing


================================================================================
CHANGE 2: Generic 600-GET-TIMESTAMP Paragraph
================================================================================

WHAT IS IT?
- One generic paragraph that captures current system date/time
- Converts it from system format to human-readable format
- Same paragraph works in ANY program (no customization needed)
- Called as: PERFORM 600-GET-TIMESTAMP

WHY GENERIC?
- The conversion logic (FUNCTION CURRENT-DATE) is identical for all programs
- No program-specific information is hardcoded
- Same TS-SYSTEM and TS-TIMESTAMP structure everywhere
- Copy the entire paragraph into any program without changes

WORKING-STORAGE STRUCTURE (Required):
--------------------------------------

01  WS-TIMESTAMP-FIELDS.
    05  TS-SYSTEM.
        10  DA-SYS.
            15  DA-SYS-CCYY.
                20  CC                    PIC X(2).
                20  YY                    PIC X(2).
            15  MM                        PIC X(2).
            15  DD                        PIC X(2).
        10  HR-SYS.
            15  HH                        PIC X(2).
            15  MI                        PIC X(2).
            15  SS                        PIC X(2).
            15  TT                        PIC X(2).
    05  TS-TIMESTAMP.
        10  CC                            PIC X(2).
        10  YY                            PIC X(2).
        10  TE-MARKER1                    PIC X     VALUE '-'.
        10  MM                            PIC X(2).
        10  TE-MARKER2                    PIC X     VALUE '-'.
        10  DD                            PIC X(2).
        10  TE-MARKER3                    PIC X     VALUE '-'.
        10  HH                            PIC X(2).
        10  TE-MARKER4                    PIC X     VALUE '.'.
        10  MI                            PIC X(2).
        10  TE-MARKER5                    PIC X     VALUE '.'.
        10  SS                            PIC X(2).
        10  TE-MARKER6                    PIC X     VALUE '.'.
        10  TT                            PIC X(2).
        10  NNNN                          PIC 9(04) VALUE 0.

GENERIC PROCEDURE DIVISION PARAGRAPH:
--------------------------------------

600-GET-TIMESTAMP.
    MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.
    MOVE CC OF TS-SYSTEM                  TO CC OF TS-TIMESTAMP.
    MOVE YY OF TS-SYSTEM                  TO YY OF TS-TIMESTAMP.
    MOVE MM OF TS-SYSTEM                  TO MM OF TS-TIMESTAMP.
    MOVE DD OF TS-SYSTEM                  TO DD OF TS-TIMESTAMP.
    MOVE HH OF TS-SYSTEM                  TO HH OF TS-TIMESTAMP.
    MOVE MI OF TS-SYSTEM                  TO MI OF TS-TIMESTAMP.
    MOVE SS OF TS-SYSTEM                  TO SS OF TS-TIMESTAMP.
    MOVE TT OF TS-SYSTEM                  TO TT OF TS-TIMESTAMP.

USAGE LOCATIONS (WHERE TO CALL):
---------------------------------

PROCEDURE DIVISION.
    PERFORM 100-INITIALIZE.
    PERFORM 600-GET-TIMESTAMP.              <- Startup timestamp
    PERFORM 200-OPEN-CURSORS.
    PERFORM 300-MAIN-PROCESSING.
    PERFORM 400-CLOSE-CURSORS.
    PERFORM 600-GET-TIMESTAMP.              <- Before display totals
    PERFORM 500-DISPLAY-TOTALS.
    STOP RUN.

100-INITIALIZE.
    MOVE ZEROES TO DA-CCYYMMDD.
    INITIALIZE DCLDZBEFFTV.
    MOVE CS-PROGRAM TO PROGRAM-NAME.        <- Change 1: Program constant
    .

500-DISPLAY-TOTALS.
    DISPLAY 'Program started: ' TS-TIMESTAMP.
    DISPLAY 'Program ended  : ' TS-TIMESTAMP.
    .

TIMESTAMP OUTPUT FORMAT:
- Input: FUNCTION CURRENT-DATE (raw: CCYYMMDDHHMMSSNNNNNN)
- Output: TS-TIMESTAMP formatted as CCYY-MM-DD-HH.MI.SS.TT

EXAMPLE OUTPUT:
    2026-10-08-14.35.22.50

This is consistent, human-readable, and used everywhere.


================================================================================
PUTTING BOTH CHANGES TOGETHER: Complete Example
================================================================================

WORKING-STORAGE SECTION (with both Changes 1 & 2):

01  WS-CONTROL-FIELDS.
    10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.
    10  WS-NB-BEFF-COUNT         PIC 9(7) COMP-3 VALUE ZEROES.
    10  WS-NB-OUTPUT-COUNT       PIC 9(7) COMP-3 VALUE ZEROES.

01  WS-TIMESTAMP-FIELDS.
    05  TS-SYSTEM.
        10  DA-SYS.
            15  DA-SYS-CCYY.
                20  CC                    PIC X(2).
                20  YY                    PIC X(2).
            15  MM                        PIC X(2).
            15  DD                        PIC X(2).
        10  HR-SYS.
            15  HH                        PIC X(2).
            15  MI                        PIC X(2).
            15  SS                        PIC X(2).
            15  TT                        PIC X(2).
    05  TS-TIMESTAMP.
        10  CC                            PIC X(2).
        10  YY                            PIC X(2).
        10  TE-MARKER1                    PIC X     VALUE '-'.
        10  MM                            PIC X(2).
        10  TE-MARKER2                    PIC X     VALUE '-'.
        10  DD                            PIC X(2).
        10  TE-MARKER3                    PIC X     VALUE '-'.
        10  HH                            PIC X(2).
        10  TE-MARKER4                    PIC X     VALUE '.'.
        10  MI                            PIC X(2).
        10  TE-MARKER5                    PIC X     VALUE '.'.
        10  SS                            PIC X(2).
        10  TE-MARKER6                    PIC X     VALUE '.'.
        10  TT                            PIC X(2).
        10  NNNN                          PIC 9(04) VALUE 0.

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
    MOVE CS-PROGRAM   TO PROGRAM-NAME.          <- Change 1
    PERFORM 600-GET-TIMESTAMP.                  <- Change 2
    DISPLAY 'Started: ' TS-TIMESTAMP.
    .

200-OPEN-CURSORS.
    OPEN CURSOR-BEFF.
    .

300-MAIN-PROCESSING.
    PERFORM UNTIL SQLCODE NOT = 0
        FETCH CURSOR-BEFF
            IF SQLCODE = 0
                ADD 1 TO WS-NB-BEFF-COUNT
                <-- Process fields
                ADD 1 TO WS-NB-OUTPUT-COUNT
            END-IF
    END-PERFORM.
    .

400-CLOSE-CURSORS.
    CLOSE CURSOR-BEFF.
    .

500-DISPLAY-TOTALS.
    PERFORM 600-GET-TIMESTAMP.                  <- Change 2
    DISPLAY 'Ended  : ' TS-TIMESTAMP.
    DISPLAY 'TOTAL BEFF RECORDS   : ' WS-NB-BEFF-COUNT.
    DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT.
    .

600-GET-TIMESTAMP.
    MOVE FUNCTION CURRENT-DATE            TO TS-SYSTEM.
    MOVE CC OF TS-SYSTEM                  TO CC OF TS-TIMESTAMP.
    MOVE YY OF TS-SYSTEM                  TO YY OF TS-TIMESTAMP.
    MOVE MM OF TS-SYSTEM                  TO MM OF TS-TIMESTAMP.
    MOVE DD OF TS-SYSTEM                  TO DD OF TS-TIMESTAMP.
    MOVE HH OF TS-SYSTEM                  TO HH OF TS-TIMESTAMP.
    MOVE MI OF TS-SYSTEM                  TO MI OF TS-TIMESTAMP.
    MOVE SS OF TS-SYSTEM                  TO SS OF TS-TIMESTAMP.
    MOVE TT OF TS-SYSTEM                  TO TT OF TS-TIMESTAMP.
    .


================================================================================
APPLICATION TO ALL PROGRAMS (Generic Rules)
================================================================================

Change 1 (CS-PROGRAM Formatting) is ALWAYS applied to:
- Every converted program
- Every new program
- Every manually-edited program
- Standard formatting ensures consistency

Change 2 (600-GET-TIMESTAMP Generic Paragraph) is ALWAYS:
- The same paragraph in every program
- No customization needed
- Copy-paste directly
- Just change the program ID in CS-PROGRAM (line 1 of WS-CONTROL-FIELDS)

IMPLEMENTATION:
1. Copy the WORKING-STORAGE section above (both groups)
2. Copy the 600-GET-TIMESTAMP paragraph (it's generic - no changes)
3. Update CS-PROGRAM VALUE with your program ID ('VMDZ4420' → 'YOURPROG')
4. Call PERFORM 600-GET-TIMESTAMP wherever you need current timestamp
5. Use TS-TIMESTAMP in DISPLAY statements

VALIDATION:
- [ ] WS-CONTROL-FIELDS has CS-PROGRAM (with correct formatting)
- [ ] WS-TIMESTAMP-FIELDS has TS-SYSTEM and TS-TIMESTAMP
- [ ] 600-GET-TIMESTAMP paragraph exists
- [ ] 600-GET-TIMESTAMP called in 100-INITIALIZE
- [ ] 600-GET-TIMESTAMP called before 500-DISPLAY-TOTALS
- [ ] All MOVE statements in 600-GET-TIMESTAMP are present (9 total)
- [ ] MOVE CS-PROGRAM TO PROGRAM-NAME uses correct spacing
- [ ] TS-TIMESTAMP format is CCYY-MM-DD-HH.MI.SS.TT


================================================================================
FILES TO READ/UPDATE
================================================================================

Standards and Rules:
  - rules/counter_rules.py (Change 1: PROGRAM_CONSTANT_TEMPLATE)
  - rules/timestamp_conversion_standards.py (Change 2: Generic paragraph)
  - rules/cobol_standard_initialization_rules.py (Integration)

Master Index:
  - rules/ISSUES_1_TO_5_MASTER_INDEX.py

Practical Example:
  - rules/ISSUES_1_TO_5_PRACTICAL_EXAMPLE.py

References:
  - rules/ISSUES_1_TO_5_CHANGES_1_2.py (this file)


================================================================================
FREQUENTLY ASKED QUESTIONS
================================================================================

Q: "Do I have to use 600-GET-TIMESTAMP?"
A: Yes. It's the standard paragraph for all programs. It's generic, so
   no customization needed. Just copy it.

Q: "Can I rename 600-GET-TIMESTAMP?"
A: No. Keep it as 600-GET-TIMESTAMP so all programs are consistent.
   The paragraph number is part of the standard.

Q: "What if I need the timestamp in a different format?"
A: TS-TIMESTAMP is always CCYY-MM-DD-HH.MI.SS.TT. This is the standard
   format. If you need a different format, create a separate paragraph
   but keep 600-GET-TIMESTAMP for the standard.

Q: "Do I need all 9 MOVE statements in 600-GET-TIMESTAMP?"
A: Yes. All 9 are required to populate TS-TIMESTAMP completely.
   Don't skip any.

Q: "Can I put 600-GET-TIMESTAMP in a copybook?"
A: Yes. It's so generic that you can COPY it from a library.
   No program-specific code is in it.

Q: "What about the NNNN field (hundredths of second)?"
A: It's a placeholder (PIC 9(04) VALUE 0) for future use.
   Not populated by FUNCTION CURRENT-DATE in current version.
   Leave it at zero.

Q: "Is CS-PROGRAM formatting strict (28 characters)?"
A: Yes. The 28-character alignment is standard across all programs.
   It ensures visual consistency in code reviews and output.

Q: "Can I use CS-PROGRAM for anything else?"
A: No. It's reserved for the program ID only. For other constants,
   create separate fields in WS-CONTROL-FIELDS with the same formatting.
"""

from __future__ import annotations

# This is a comprehensive guide for implementing Change 1 and Change 2
# together, showing how they integrate in a real program.

CHANGES_SUMMARY = {
    "Change 1": {
        "name": "CS-PROGRAM Declaration and Usage Style",
        "affects": "All programs",
        "standard_file": "rules/counter_rules.py",
        "formatting": "28-character left-aligned field name with 4-space PIC offset",
        "usage_spacing": "MOVE {name}   TO {target} (3 spaces on each side)",
    },
    "Change 2": {
        "name": "Generic 600-GET-TIMESTAMP Paragraph",
        "affects": "All programs",
        "standard_file": "rules/timestamp_conversion_standards.py",
        "reusable": True,
        "requires_working_storage": [
            "TS-SYSTEM (raw FUNCTION CURRENT-DATE)",
            "TS-TIMESTAMP (formatted output)",
        ],
        "paragraph_name": "600-GET-TIMESTAMP",
        "calls_in_program": [
            "100-INITIALIZE (after MOVE CS-PROGRAM)",
            "500-DISPLAY-TOTALS (before display)",
        ],
    },
}

BOTH_CHANGES_ARE_GENERIC = True
BOTH_CHANGES_APPLY_TO_ALL_PROGRAMS = True
NO_CUSTOMIZATION_NEEDED = True

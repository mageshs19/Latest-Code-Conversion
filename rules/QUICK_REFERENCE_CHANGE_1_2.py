"""
QUICK REFERENCE: Change 1 & 2 (Program Constant and Timestamp)

One-page summary for developers. Print this and keep it handy.

================================================================================
CHANGE 1: CS-PROGRAM CONSTANT (Program Name)
================================================================================

WORKING-STORAGE:
    01  WS-CONTROL-FIELDS.
        10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.

KEY POINTS:
  • Field name: CS-PROGRAM (always this name)
  • PIC: X(8) (always 8 characters)
  • VALUE: Program ID in single quotes ('VMDZ4420')
  • Alignment: 28-character column for field name
  • Left-align the field name, so it looks like above

IN PROCEDURE DIVISION:
    MOVE CS-PROGRAM   TO PROGRAM-NAME.

KEY POINTS:
  • Use MOVE, not SET
  • 3 spaces after CS-PROGRAM
  • 3 spaces before TO
  • Target is PROGRAM-NAME (always)

NEVER:
    MOVE 'VMDZ4420' TO PROGRAM-NAME.        <- Hardcoded (WRONG)
    10 CS-PROGRAM PIC X(8) VALUE...         <- Wrong alignment (WRONG)
    MOVE CS-PROGRAM TO PROGRAM-NAME.        <- Wrong spacing (WRONG)

================================================================================
CHANGE 2: 600-GET-TIMESTAMP PARAGRAPH (Current Date/Time)
================================================================================

WORKING-STORAGE (copy this exactly):
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

IN PROCEDURE DIVISION (copy this exactly):
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

KEY POINTS:
  • Paragraph name: 600-GET-TIMESTAMP (always this name)
  • Generic: Same paragraph in every program (no changes)
  • No customization needed
  • All 9 MOVE statements are required
  • Produces output: CCYY-MM-DD-HH.MI.SS.TT (26 bytes)

WHEN TO CALL:
    PROCEDURE DIVISION.
        PERFORM 100-INITIALIZE.
        PERFORM 600-GET-TIMESTAMP.              <- Call here (startup)
        PERFORM 200-OPEN-CURSORS.
        PERFORM 300-MAIN-PROCESSING.
        PERFORM 400-CLOSE-CURSORS.
        PERFORM 600-GET-TIMESTAMP.              <- Call here (before display)
        PERFORM 500-DISPLAY-TOTALS.
        STOP RUN.

USAGE:
    DISPLAY 'Started: ' TS-TIMESTAMP.
    DISPLAY 'Ended  : ' TS-TIMESTAMP.

================================================================================
COMPLETE WORKING EXAMPLE (Both Changes Together)
================================================================================

WORKING-STORAGE SECTION.
    01  WS-CONTROL-FIELDS.
        10  CS-PROGRAM               PIC X(8)    VALUE 'VMDZ4420'.
        10  WS-NB-RECORDS-COUNT      PIC 9(7) COMP-3 VALUE ZEROES.
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
    MOVE CS-PROGRAM   TO PROGRAM-NAME.      <- Change 1
    PERFORM 600-GET-TIMESTAMP.              <- Change 2
    DISPLAY 'Started: ' TS-TIMESTAMP.
    .

500-DISPLAY-TOTALS.
    PERFORM 600-GET-TIMESTAMP.              <- Change 2
    DISPLAY 'Ended  : ' TS-TIMESTAMP.
    DISPLAY 'Total records: ' WS-NB-RECORDS-COUNT.
    .

600-GET-TIMESTAMP.                          <- Change 2: Generic paragraph
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
IMPLEMENTATION CHECKLIST
================================================================================

CHANGE 1 (CS-PROGRAM):
  [ ] Added to WS-CONTROL-FIELDS
  [ ] Formatted with 28-character alignment
  [ ] VALUE has correct program ID
  [ ] MOVE CS-PROGRAM TO PROGRAM-NAME in 100-INITIALIZE
  [ ] 3 spaces after constant name
  [ ] 3 spaces before TO

CHANGE 2 (600-GET-TIMESTAMP):
  [ ] TS-SYSTEM structure in WORKING-STORAGE
  [ ] TS-TIMESTAMP structure in WORKING-STORAGE
  [ ] 600-GET-TIMESTAMP paragraph in PROCEDURE DIVISION
  [ ] All 9 MOVE statements present
  [ ] Called in 100-INITIALIZE
  [ ] Called in 500-DISPLAY-TOTALS
  [ ] Used in DISPLAY statements

================================================================================
COMMON MISTAKES TO AVOID
================================================================================

MISTAKE 1: Hardcoded program name
    WRONG:  MOVE 'VMDZ4420' TO PROGRAM-NAME.
    RIGHT:  MOVE CS-PROGRAM TO PROGRAM-NAME.

MISTAKE 2: Wrong field alignment (24 instead of 28)
    WRONG:  10  CS-PROGRAM               PIC X(8)...
            (fewer spaces before PIC)
    RIGHT:  10  CS-PROGRAM               PIC X(8)...
            (28-character alignment)

MISTAKE 3: Missing MOVE statements in timestamp paragraph
    WRONG:  600-GET-TIMESTAMP.
                MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.
                MOVE CC OF TS-SYSTEM TO CC OF TS-TIMESTAMP.
                ... (only 3 moves instead of 9)

    RIGHT:  600-GET-TIMESTAMP.
                MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.
                MOVE CC OF TS-SYSTEM TO CC OF TS-TIMESTAMP.
                MOVE YY OF TS-SYSTEM TO YY OF TS-TIMESTAMP.
                MOVE MM OF TS-SYSTEM TO MM OF TS-TIMESTAMP.
                MOVE DD OF TS-SYSTEM TO DD OF TS-TIMESTAMP.
                MOVE HH OF TS-SYSTEM TO HH OF TS-TIMESTAMP.
                MOVE MI OF TS-SYSTEM TO MI OF TS-TIMESTAMP.
                MOVE SS OF TS-SYSTEM TO SS OF TS-TIMESTAMP.
                MOVE TT OF TS-SYSTEM TO TT OF TS-TIMESTAMP.

MISTAKE 4: Renaming the timestamp paragraph
    WRONG:  700-CAPTURE-TIME.
    RIGHT:  600-GET-TIMESTAMP.

MISTAKE 5: Customizing the timestamp paragraph
    WRONG:  [Changing field names or logic]
    RIGHT:  [Copy as-is, no changes]

================================================================================
FOR MORE INFORMATION
================================================================================

Detailed guide:  rules/ISSUES_1_TO_5_CHANGES_1_2.py
Working example: rules/ISSUES_1_TO_5_PRACTICAL_EXAMPLE.py
Timestamp rules: rules/timestamp_conversion_standards.py
Counter rules:   rules/counter_rules.py
Master index:    rules/ISSUES_1_TO_5_MASTER_INDEX.py
"""

from __future__ import annotations

# This is a quick reference card for developers.
# No executable code logic belongs here.

CHANGE_1_KEY_POINTS = {
    "Field name": "CS-PROGRAM",
    "Picture": "PIC X(8)",
    "Alignment": "28 characters (left-aligned)",
    "Formatting": "4 spaces before PIC, 4 spaces before VALUE",
    "Usage": "MOVE CS-PROGRAM   TO PROGRAM-NAME",
}

CHANGE_2_KEY_POINTS = {
    "Paragraph name": "600-GET-TIMESTAMP",
    "Type": "Generic (same in every program)",
    "Customization": "None needed",
    "Working storage": "TS-SYSTEM + TS-TIMESTAMP",
    "Output format": "CCYY-MM-DD-HH.MI.SS.TT",
    "Called in": ["100-INITIALIZE", "500-DISPLAY-TOTALS"],
}

QUICK_CHECKLIST = {
    "Change 1": 6,  # 6 items to check
    "Change 2": 7,  # 7 items to check
    "Total": 13,    # 13 items to validate
}

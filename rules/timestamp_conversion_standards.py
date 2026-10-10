"""
Timestamp Conversion Standards and Generic Paragraph (Change 2).

Standards for timestamp handling across all converted programs. Defines
the generic 600-GET-TIMESTAMP paragraph that captures system time/date
and converts it to TS-TIMESTAMP format for standardized use.

This implements a REUSABLE, GENERIC timestamp paragraph that every program
can call, eliminating duplication.

STANDARD TIMESTAMP STRUCTURE:
=============================

Working-storage section includes TWO timestamp groups:

1. TS-SYSTEM: Raw output from FUNCTION CURRENT-DATE (21 bytes)
   Format: CCYYMMDDHHMMSSNNNNNN (where NN = 100ths of second)
   
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

2. TS-TIMESTAMP: Formatted human-readable timestamp (26 bytes)
   Format: CCYY-MM-DD-HH.MI.SS.TT
   
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

GENERIC PARAGRAPH: 600-GET-TIMESTAMP
=====================================

Every converted program includes this paragraph to capture and format
the current date/time. Call it whenever you need current timestamp.

600-GET-TIMESTAMP.
    MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.
    MOVE CC OF TS-SYSTEM TO CC OF TS-TIMESTAMP.
    MOVE YY OF TS-SYSTEM TO YY OF TS-TIMESTAMP.
    MOVE MM OF TS-SYSTEM TO MM OF TS-TIMESTAMP.
    MOVE DD OF TS-SYSTEM TO DD OF TS-TIMESTAMP.
    MOVE HH OF TS-SYSTEM TO HH OF TS-TIMESTAMP.
    MOVE MI OF TS-SYSTEM TO MI OF TS-TIMESTAMP.
    MOVE SS OF TS-SYSTEM TO SS OF TS-TIMESTAMP.
    MOVE TT OF TS-SYSTEM TO TT OF TS-TIMESTAMP.

USAGE EXAMPLE:
==============

PROCEDURE DIVISION.
    PERFORM 100-INITIALIZE.
    PERFORM 600-GET-TIMESTAMP.          <- Capture start timestamp
    DISPLAY 'Program started at: ' TS-TIMESTAMP.
    PERFORM 200-OPEN-CURSORS.
    PERFORM 300-MAIN-PROCESSING.
    PERFORM 400-CLOSE-CURSORS.
    PERFORM 600-GET-TIMESTAMP.          <- Capture end timestamp
    DISPLAY 'Program ended at: ' TS-TIMESTAMP.
    STOP RUN.

BENEFITS:
=========
1. GENERIC: Same paragraph works for any program (no customization needed)
2. REUSABLE: Call 600-GET-TIMESTAMP as many times as needed
3. STANDARD: Same format across all programs (CCYY-MM-DD-HH.MI.SS.TT)
4. SIMPLE: Just one PERFORM call to get formatted timestamp
5. NO DUPLICATION: Paragraph is declared once, used everywhere

TIMESTAMP LOCATIONS (Standard Placements):
===========================================
Call 600-GET-TIMESTAMP at:
1. Program startup (before PERFORM 200-OPEN-CURSORS)
2. Before main processing loop
3. After main processing loop completes
4. Just before STOP RUN

Each call updates TS-TIMESTAMP with current system time. Store in
WS-EXEC-* fields if you need to preserve timestamps across calls.

INTEGRATION WITH ISSUE #5:
==========================
WS-EXEC-START-TIME and WS-EXEC-END-TIME (separate numeric fields)
store the time portion for calculation purposes.

When you need to CAPTURE a timestamp for storage:
    PERFORM 600-GET-TIMESTAMP
    MOVE TS-TIMESTAMP TO WS-AUDIT-TIMESTAMP
    OR
    MOVE SS OF TS-TIMESTAMP TO WS-EXEC-START-TIME

When you need to DISPLAY current time:
    PERFORM 600-GET-TIMESTAMP
    DISPLAY 'Current: ' TS-TIMESTAMP

VALIDATION CHECKLIST:
=====================
[ ] TS-SYSTEM group structure in WORKING-STORAGE (raw CURRENT-DATE)
[ ] TS-TIMESTAMP group structure in WORKING-STORAGE (formatted)
[ ] 600-GET-TIMESTAMP paragraph exists in PROCEDURE DIVISION
[ ] Paragraph moves from TS-SYSTEM to TS-TIMESTAMP correctly
[ ] All 9 field moves are present (CC, YY, MM, DD, HH, MI, SS, TT)
[ ] 600-GET-TIMESTAMP called at startup
[ ] 600-GET-TIMESTAMP called before major operations
[ ] TS-TIMESTAMP used in DISPLAY statements
[ ] Format is always CCYY-MM-DD-HH.MI.SS.TT
"""

from __future__ import annotations

# =====================================================================
# Master control switch
# =====================================================================
EMIT_TIMESTAMP_CONVERSION_PARAGRAPH = True

# =====================================================================
# Timestamp Structure Definition (WORKING-STORAGE)
# =====================================================================

TIMESTAMP_WORKING_STORAGE_COMMENT = "* STANDARD TIMESTAMP FIELDS"

# Raw timestamp group (output of FUNCTION CURRENT-DATE)
TIMESTAMP_TS_SYSTEM_STRUCTURE = [
    "01  WS-TIMESTAMP-FIELDS.",
    "    05  TS-SYSTEM.",
    "        10  DA-SYS.",
    "            15  DA-SYS-CCYY.",
    "                20  CC                    PIC X(2).",
    "                20  YY                    PIC X(2).",
    "            15  MM                        PIC X(2).",
    "            15  DD                        PIC X(2).",
    "        10  HR-SYS.",
    "            15  HH                        PIC X(2).",
    "            15  MI                        PIC X(2).",
    "            15  SS                        PIC X(2).",
    "            15  TT                        PIC X(2).",
]

# Formatted timestamp group (CCYY-MM-DD-HH.MI.SS.TT)
TIMESTAMP_TS_TIMESTAMP_STRUCTURE = [
    "    05  TS-TIMESTAMP.",
    "        10  CC                            PIC X(2).",
    "        10  YY                            PIC X(2).",
    "        10  TE-MARKER1                    PIC X     VALUE '-'.",
    "        10  MM                            PIC X(2).",
    "        10  TE-MARKER2                    PIC X     VALUE '-'.",
    "        10  DD                            PIC X(2).",
    "        10  TE-MARKER3                    PIC X     VALUE '-'.",
    "        10  HH                            PIC X(2).",
    "        10  TE-MARKER4                    PIC X     VALUE '.'.",
    "        10  MI                            PIC X(2).",
    "        10  TE-MARKER5                    PIC X     VALUE '.'.",
    "        10  SS                            PIC X(2).",
    "        10  TE-MARKER6                    PIC X     VALUE '.'.",
    "        10  TT                            PIC X(2).",
    "        10  NNNN                          PIC 9(04) VALUE 0.",
]

# =====================================================================
# Generic Paragraph: 600-GET-TIMESTAMP
# =====================================================================

TIMESTAMP_PARAGRAPH_NAME = "600-GET-TIMESTAMP"
TIMESTAMP_PARAGRAPH_COMMENT = "* Generic paragraph - copy to any program"

# The exact conversion sequence (order matters)
TIMESTAMP_CONVERSION_LINES = [
    "{indent}MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.",
    "{indent}MOVE CC OF TS-SYSTEM TO CC OF TS-TIMESTAMP.",
    "{indent}MOVE YY OF TS-SYSTEM TO YY OF TS-TIMESTAMP.",
    "{indent}MOVE MM OF TS-SYSTEM TO MM OF TS-TIMESTAMP.",
    "{indent}MOVE DD OF TS-SYSTEM TO DD OF TS-TIMESTAMP.",
    "{indent}MOVE HH OF TS-SYSTEM TO HH OF TS-TIMESTAMP.",
    "{indent}MOVE MI OF TS-SYSTEM TO MI OF TS-TIMESTAMP.",
    "{indent}MOVE SS OF TS-SYSTEM TO SS OF TS-TIMESTAMP.",
    "{indent}MOVE TT OF TS-SYSTEM TO TT OF TS-TIMESTAMP.",
]

# =====================================================================
# Timestamp Output Format
# =====================================================================
TIMESTAMP_OUTPUT_FORMAT = "CCYY-MM-DD-HH.MI.SS.TT"
TIMESTAMP_OUTPUT_LENGTH = 26  # bytes (including separators)

# =====================================================================
# Standard Calling Locations
# =====================================================================
TIMESTAMP_CALL_LOCATIONS = [
    "100-INITIALIZE (after DCLGEN initialization)",
    "Before PERFORM 200-OPEN-CURSORS",
    "Before main processing loop",
    "After main processing loop",
    "Before STOP RUN (500-DISPLAY-TOTALS)",
]

# =====================================================================
# Diagnostics
# =====================================================================
TIMESTAMP_MESSAGES = {
    "paragraph_generated": (
        "Timestamp: generated 600-GET-TIMESTAMP paragraph."
    ),
    "structure_declared": (
        "Timestamp: declared WS-TIMESTAMP-FIELDS (TS-SYSTEM and TS-TIMESTAMP)."
    ),
    "conversion_complete": (
        "Timestamp: conversion from TS-SYSTEM to TS-TIMESTAMP complete."
    ),
    "missing_call": (
        "Timestamp: paragraph 600-GET-TIMESTAMP not called at startup; "
        "recommend PERFORM 600-GET-TIMESTAMP in 100-INITIALIZE."
    ),
    "missing_structure": (
        "Timestamp: WS-TIMESTAMP-FIELDS structure not found in WORKING-STORAGE; "
        "add before using 600-GET-TIMESTAMP."
    ),
}

# =====================================================================
# Integration Note
# =====================================================================
TIMESTAMP_PARAGRAPH_IS_GENERIC = True
TIMESTAMP_PARAGRAPH_NO_CUSTOMIZATION = True
TIMESTAMP_REUSABLE_ACROSS_ALL_PROGRAMS = True

TIMESTAMP_NOTE = (
    "600-GET-TIMESTAMP is intentionally generic and reusable. "
    "No program-specific customization needed. Copy the paragraph into "
    "any program and call it whenever current timestamp is needed."
)

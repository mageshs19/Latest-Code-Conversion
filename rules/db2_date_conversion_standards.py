"""
Enhanced DB2 Date Conversion Standards (Issue #1).

Standards for DB2 DATE field conversion in COBOL, specifying:
- WHERE conversions must happen (before output, not inside loop)
- HOW to handle edge-case dates (01.01.0001, 31.12.9999)
- WHAT the conversion sequence must be

This file documents the STANDARD PATTERN that all date conversions must follow.
The rules folder contains the templates; this file documents the intent.

STANDARD SEQUENCE FOR DATE CONVERSION:
=====================================

Step 1: Initialize helper fields (once at startup, NOT in loop)
    MOVE ZEROES TO DA-CCYYMMDD
    MOVE ZEROES TO <helper-field>

Step 2: Before processing any date field
    MOVE <source-date-from-dclgen> TO DA-DD-MM-CCYY

Step 3: Evaluate date value and convert
    EVALUATE TRUE
        WHEN DA-DD-MM-CCYY = '01.01.0001'
            MOVE ZEROES TO DA-CCYYMMDD-R
        WHEN DA-DD-MM-CCYY = '31.12.9999'
            MOVE '99999999' TO DA-CCYYMMDD-R
        WHEN OTHER
            MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R
            MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R
            MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R
    END-EVALUATE

Step 4: Write converted date to output
    MOVE DA-CCYYMMDD-R TO <output-field>

CRITICAL REQUIREMENTS:
======================
1. Date initialization (ZEROES) happens ONCE before any processing
   - Location: dedicated INITIALIZE paragraph or WORKING-STORAGE VALUE clause
   - NOT inside fetch loop

2. Date comparison/conversion BEFORE write
   - Location: immediately before MOVE to output field
   - Reason: ensures output always receives converted value

3. Edge case handling is MANDATORY
   - '01.01.0001' (DB2 minimum) → '00000000' (COBOL zero date)
   - '31.12.9999' (DB2 maximum) → '99999999' (COBOL high date)
   - All other dates → CCYY-MM-DD realignment

4. No hardcoded field names in the conversion logic
   - DCLGEN group name: dynamic, from source metadata
   - Helper field name: derived from source field name
   - Output field name: from Sheet Mapping

5. Shared work fields reduce duplication
   - DA-CCYYMMDD (source structure for realignment)
   - DA-DD-MM-CCYY (helper for source input)
   - DA-CCYYMMDD-R (redefined numeric output)
   - Declared once in WORKING-STORAGE, reused for all dates

EXAMPLE (from VMDZ4420):
=======================

WORKING-STORAGE SECTION.
    * DB2 DATE CONVERSION WORKING STORAGE
    01  WS-DATUMVELDEN.
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
    01  HELP-UIT-DA-UBSEC              PIC 9(8)     VALUE ZEROES.

PROCEDURE DIVISION.
    100-CONVERT-DATE.
        MOVE ZEROES                    TO DA-CCYYMMDD.
        MOVE ZEROES                    TO HELP-UIT-DA-UBSEC.
        MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY.
        EVALUATE TRUE
            WHEN DA-DD-MM-CCYY = '01.01.0001'
                MOVE ZEROES            TO DA-CCYYMMDD-R
            WHEN DA-DD-MM-CCYY = '31.12.9999'
                MOVE '99999999'        TO DA-CCYYMMDD-R
            WHEN OTHER
                MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R
                MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R
                MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R
        END-EVALUATE.
        MOVE DA-CCYYMMDD-R TO HELP-UIT-DA-UBSEC.
        <-- HELP-UIT-DA-UBSEC now contains converted date, ready for output

FIELD MAPPING INTEGRATION (Issue #2):
======================================
All date conversions are driven by Sheet Mapping metadata:
- Source: DCLGEN field (e.g., DA-UBSECIS-479BEFF OF DCLDZBEFFTV)
- Target: Output record field (e.g., UIT-DA-UBSEC)
- Conversion: Automatically injected when source is DATE type

No hardcoding of DCLGEN names or field names occurs in the conversion logic.
Every source/target pair is looked up via Sheet Mapping.

VALIDATION CHECKLIST:
=====================
Before closing a conversion:
- [ ] All DATE fields in DCLGEN have conversion rules
- [ ] Conversion happens BEFORE output write, not inside loop
- [ ] Edge cases (01.01.0001, 31.12.9999) are explicitly handled
- [ ] Helper field is initialized once, not in loop
- [ ] No hardcoded field names in EVALUATE logic
- [ ] Sheet Mapping has SOURCE=DATE and valid TARGET field
- [ ] Output date fields are NUMERIC (PIC 9(8))
"""

from __future__ import annotations

# =====================================================================
# Master control switches
# =====================================================================
ENFORCE_DATE_CONVERSION_STANDARD = True
ENFORCE_DATE_CONVERSION_TIMING = True  # Conversion before write, not in loop

# =====================================================================
# Standard date edge cases (from DB2 specification)
# =====================================================================
DB2_DATE_EDGE_CASES = {
    "LOW": {
        "db2_format": "01.01.0001",      # DB2 minimum date
        "cobol_numeric": "00000000",     # Maps to COBOL zero
        "description": "DB2 minimum date (01.01.0001 year 1)",
    },
    "HIGH": {
        "db2_format": "31.12.9999",      # DB2 maximum date
        "cobol_numeric": "99999999",     # Maps to COBOL high date
        "description": "DB2 maximum date (31.12.9999 year 9999)",
    },
}

# =====================================================================
# Work field declarations (shared, single instantiation)
# =====================================================================
DATE_CONVERSION_WORKING_STORAGE_COMMENT = "* DB2 DATE CONVERSION WORKING STORAGE"

DATE_CONVERSION_WORK_FIELDS = [
    "01  WS-DATUMVELDEN.",
    "    03  DA-CCYYMMDD.",
    "        05  CC                    PIC 99       VALUE ZERO.",
    "        05  YY                    PIC 99       VALUE ZERO.",
    "        05  MM                    PIC 99       VALUE ZERO.",
    "        05  DD                    PIC 99       VALUE ZERO.",
    "    03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.",
    "        05  CCYY                  PIC 9999.",
    "        05  MM                    PIC 99.",
    "        05  DD                    PIC 99.",
    "    03  DA-DD-MM-CCYY.",
    "        05  DD                    PIC 9(02).",
    "        05  TE-MARKER5            PIC X        VALUE '.'.",
    "        05  MM                    PIC 9(02).",
    "        05  TE-MARKER6            PIC X        VALUE '.'.",
    "        05  CCYY                  PIC 9(04).",
]

# =====================================================================
# Helper field generation (one per date source)
# =====================================================================
HELPER_FIELD_TEMPLATE = "    02  {helper:<30} PIC 9(8)     VALUE ZEROES."

HELPER_NAMING_CONVENTION = "HELP-{output_field_name}"

# =====================================================================
# Conversion sequence templates (in order)
# =====================================================================
DATE_CONVERSION_SEQUENCE = [
    "{indent}MOVE ZEROES TO DA-CCYYMMDD",
    "{indent}MOVE ZEROES TO {helper}",
    "{indent}MOVE {field_name} OF {group_name} TO DA-DD-MM-CCYY",
    "{indent}EVALUATE TRUE",
    "{indent} WHEN DA-DD-MM-CCYY = '{db2_low_date}'",
    "{indent}      MOVE ZEROES TO DA-CCYYMMDD-R",
    "{indent} WHEN DA-DD-MM-CCYY = '{db2_high_date}'",
    "{indent}      MOVE '{cobol_high_numeric}' TO DA-CCYYMMDD-R",
    "{indent} WHEN OTHER",
    "{indent}      MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF DA-CCYYMMDD-R",
    "{indent}      MOVE MM   OF DA-DD-MM-CCYY TO MM   OF DA-CCYYMMDD-R",
    "{indent}      MOVE DD   OF DA-DD-MM-CCYY TO DD   OF DA-CCYYMMDD-R",
    "{indent}END-EVALUATE",
    "{indent}MOVE DA-CCYYMMDD-R TO {helper}",
]

# =====================================================================
# Timing constraints
# =====================================================================
CONVERSION_TIMING_RULE = {
    "description": "Date conversion MUST execute before output write",
    "trigger": "MOVE <date-field> TO <output-field>",
    "action": "Inject conversion sequence immediately before the MOVE",
    "location": "Not in fetch loop, not in cursor open sequence",
}

# =====================================================================
# Validation queries
# =====================================================================
VALIDATION_CHECKS = {
    "all_sources_converted": "All DATE fields in DCLGEN have conversion rules?",
    "no_hardcoded_names": "Conversion logic contains zero hardcoded names?",
    "edge_cases_handled": "01.01.0001 and 31.12.9999 explicitly handled?",
    "proper_timing": "Conversion happens before write, not in initialization?",
    "helper_unique": "Each date source has unique, derived helper field?",
}

# =====================================================================
# Diagnostics
# =====================================================================
DATE_CONVERSION_MESSAGES = {
    "standards_applied": (
        "Date conversion: applied standard sequence for {field_name} "
        "in {group_name}."
    ),
    "edge_case_handled": (
        "Date conversion: edge case {edge_case} mapped to {cobol_value}."
    ),
    "helper_declared": (
        "Date conversion: declared helper field {helper}."
    ),
    "timing_violation": (
        "Date conversion: timing violation on line {line}: conversion "
        "happens after output write (should be before)."
    ),
    "timing_ok": (
        "Date conversion: timing verified; conversion on line {line} "
        "happens before output write on line {write_line}."
    ),
}

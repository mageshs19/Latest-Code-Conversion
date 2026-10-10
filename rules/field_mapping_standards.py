"""
Field Mapping and MOVE Statement Standards (Issue #2).

Standards for how MOVE operations should work when converting from DCLGEN
fields to output record fields. This ensures field mappings are clean and
follow COBOL best practices.

STANDARD PATTERN FOR FIELD MAPPING:
====================================

1. QUALIFIED REFERENCE (PREFERRED)
   Format: MOVE <field> OF <dclgen-group> TO <output-field>
   Example: MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK
   
   Rules:
   - DCLGEN field name comes from Sheet Mapping (SOURCE)
   - DCLGEN group name comes from DCLGEN metadata
   - Output field name comes from Sheet Mapping (TARGET)
   - Never invent or hardcode any of these

2. UNQUALIFIED REFERENCE (NOT RECOMMENDED)
   Example: MOVE AM-CNSTK-479BEFF TO UIT-AM-CN-STOCK
   
   Status: DEPRECATED
   Reason: No explicit DCLGEN group reference; loses traceability
   Use only when field name is globally unique (rare)

3. SPECIAL CASE: NUMERIC DATE FIELDS
   Pattern:
   - Convert date using DA-CCYYMMDD helper (see db2_date_conversion_standards.py)
   - THEN move converted helper to output field
   
   Example:
       MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY
       <-- (evaluate and convert)
       MOVE DA-CCYYMMDD-R TO UIT-DA-UBSEC

4. INITIALIZATION BEFORE MOVE (IF NEEDED)
   When output field may not have been cleared:
   
   INITIALIZE UIT-RECORD    <-- Once per paragraph or as needed
   MOVE <source> OF <group> TO <target>


VIOLATION PATTERNS TO AVOID:
=============================

WRONG 1: Bare field reference (loses DCLGEN context)
    MOVE CCUSTK-479BEFF TO UIT-AM-CN-STOCK
    ^-- Which DCLGEN group? Unknown if field exists.

WRONG 2: Hardcoded DCLGEN or record names
    MOVE <field> OF DCLDZBEFFTV TO UIT-AM-CN-STOCK
    ^-- If DCLGEN name changes, hardcode breaks.

WRONG 3: Field name mismatch (Sheet Mapping error)
    MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-WRONG-FIELD
    ^-- Sheet Mapping says map to UIT-AM-CN-STOCK, not UIT-WRONG-FIELD

WRONG 4: Uninitialized output before move
    MOVE <field> TO UIT-RECORD
    <-- UIT-RECORD might have garbage from previous iteration

WRONG 5: Date without conversion
    MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO UIT-DA-UBSEC
    ^-- DA field is DD.MM.CCYY; needs conversion to CCYYMMDD first


FIELD MAPPING CHECKLIST:
========================
For each MOVE statement to an output field:
- [ ] Source is DCLGEN field name (from Sheet Mapping SOURCE)
- [ ] DCLGEN group is explicitly stated (OF <group>)
- [ ] Target is Sheet Mapping TARGET field name
- [ ] If source is DATE type: conversion sequence done first
- [ ] If target needs clearing: INITIALIZE done before MOVE
- [ ] No hardcoded names in the MOVE statement
- [ ] If field has numeric picture, moving numeric source
- [ ] If field has alpha picture, moving alphanumeric source


INTEGRATION WITH SHEET MAPPING:
================================
The converter reads Sheet Mapping for:
- Column-to-DCLGEN mappings (SOURCE column)
- DCLGEN field-to-output mappings (TARGET field)
- Data type (SOURCE=DATE triggers conversion)

Example Sheet Mapping entry:
    | Sheet | Column | DCLGEN_Group | DCLGEN_Field | DCLGEN_Qual | OUTPUT_Field | Type |
    |-------|--------|--------------|--------------|-------------|--------------|------|
    | BEF   | AM_CNSTK | DCLDZBEFFTV | AM-CNSTK | 479BEFF | UIT-AM-CN-STOCK | CHAR |
    | BEF   | DA_UBSEC | DCLDZBEFFTV | DA-UBSECIS | 479BEFF | UIT-DA-UBSEC | DATE |

Converter generates:
    MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK
    <-- (for non-DATE fields)

    MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO DA-DD-MM-CCYY
    <-- (date conversion sequence)
    MOVE DA-CCYYMMDD-R TO UIT-DA-UBSEC


IMPACT ON VALIDATION:
=====================
When validating output:
- All output fields should be populated via qualified MOVE statements
- Traceability: output field → Sheet Mapping TARGET → Sheet Mapping SOURCE → DCLGEN
- Date fields should have numeric conversion helper applied
- No uninitialized or partially initialized output records


TIMESTAMP FIELDS:
=================
Similar to DATE fields but for timestamp data.
- Source: TIMESTAMP-type DCLGEN field (format: YYYY-MM-DD-HH.MM.SS.NNNNNN)
- Conversion: Depends on OUTPUT field type (DATE vs full TIMESTAMP)
- Output: Target field format per Sheet Mapping
- Standard: Apply conversion before MOVE (like DATE fields)
"""

from __future__ import annotations

# =====================================================================
# Qualified reference pattern (RECOMMENDED)
# =====================================================================
QUALIFIED_FIELD_MOVE_PATTERN = (
    "MOVE {source_field} OF {dclgen_group} TO {target_field}"
)

UNQUALIFIED_FIELD_MOVE_PATTERN = (
    "MOVE {source_field} TO {target_field}"
)

# =====================================================================
# Field mapping validation rules
# =====================================================================
FIELD_MAPPING_VALIDATION_RULES = [
    "All MOVE statements to output fields must use qualified reference",
    "Source field name must match Sheet Mapping SOURCE exactly",
    "DCLGEN group name must match DCLGEN metadata exactly",
    "Target field name must match Sheet Mapping TARGET exactly",
    "DATE fields must be converted before MOVE (use DA-CCYYMMDD helper)",
    "Never hardcode DCLGEN group names or field names",
    "Never invent output field names not in Sheet Mapping",
    "Initialize output record before first MOVE if needed",
]

# =====================================================================
# Forbidden patterns (violations)
# =====================================================================
FORBIDDEN_FIELD_MOVE_PATTERNS = [
    r"MOVE\s+\w+\s+TO\s+[\w\-]+\s+\.",  # Bare field (no OF clause)
    r"MOVE\s+\w+\s+OF\s+DCLDZXXX\s+TO",  # Hardcoded DCLGEN group (example)
]

# =====================================================================
# Pre-move actions (context)
# =====================================================================
PREMOVE_ACTIONS = {
    "initialize_output": "INITIALIZE <output-field> before first MOVE",
    "convert_date": "Apply date conversion before MOVE (if source is DATE)",
    "convert_timestamp": "Apply timestamp conversion before MOVE (if source is TIMESTAMP)",
    "validate_type": "Verify source and target picture types match",
}

# =====================================================================
# Diagnostics
# =====================================================================
FIELD_MAPPING_MESSAGES = {
    "qualified_reference": (
        "Field mapping: using qualified reference for {source_field} "
        "of {dclgen_group}."
    ),
    "unqualified_reference_deprecated": (
        "Field mapping: unqualified reference {source_field} (line {line}); "
        "should be {source_field} OF {dclgen_group}."
    ),
    "missing_sheet_mapping": (
        "Field mapping: no Sheet Mapping entry for source {source_field}; "
        "cannot verify target field name."
    ),
    "date_conversion_needed": (
        "Field mapping: date conversion needed for {source_field} "
        "before MOVE to {target_field}."
    ),
    "hardcoded_group_detected": (
        "Field mapping: hardcoded DCLGEN group name in line {line}; "
        "should be parameterized."
    ),
}

"""
COBOL Initialization Placement Rules (Issue #3).

Standards for WHERE initialization statements are placed in the procedure,
ensuring they execute in the correct sequence per COBOL best practices.

STANDARD:
---------
1. INITIALIZE statements for DCLGEN groups (e.g., DCLDZBEFFTV) must be 
   placed BEFORE the cursor is opened, not immediately after PROCEDURE DIVISION.

2. Placement sequence:
   PROCEDURE DIVISION.
       <-- INITIALIZATION PARAGRAPH (or inline)
       <-- DATE/TIME stamp section (if needed)
       <-- OPEN CURSOR
       <-- Main processing loop

3. If initializations are needed immediately before processing:
   - Place them in a dedicated paragraph like "100-INITIALIZE-DCLGEN"
   - Call this paragraph BEFORE opening cursors
   - This separates initialization logic from procedure flow

4. NEVER place initializations:
   - Immediately after PROCEDURE DIVISION.
   - Inside the cursor fetch loop (unless needed for that iteration)
   - After OPEN CURSOR

VIOLATION MARKERS:
- PROCEDURE DIVISION.
  INITIALIZE DCLGEN-GROUP.     <-- WRONG (immediate)
  OPEN CURSOR-NAME.             <-- Cursor open follows directly

CORRECT PATTERN:
- PROCEDURE DIVISION.
  PERFORM 100-INITIALIZE-DCLGEN.
  PERFORM 200-OPEN-CURSORS.
  <-- Main flow

RATIONALE:
- DCLGEN initialization must happen once at startup, not per fetch
- Separating concerns keeps code maintainable
- Follows COBOL section/paragraph flow conventions
- Mirrors manual reference program structure
"""

from __future__ import annotations

# =====================================================================
# Master switch
# =====================================================================
ENFORCE_INITIALIZATION_PLACEMENT = True

# =====================================================================
# Recognized DCLGEN group patterns (case-insensitive)
# =====================================================================
DCLGEN_INITIALIZATION_PATTERNS = [
    r"INITIALIZE\s+\w*DCL\w+\s*\.",  # INITIALIZE DCLDZBEFFTV
    r"INITIALIZE\s+\w*STRUCT\w+\s*\.",  # INITIALIZE structures
]

# =====================================================================
# Forbidden placement contexts
# =====================================================================
INITIALIZATION_FORBIDDEN_AFTER = [
    "PROCEDURE DIVISION.",
    "OPEN",
    "FETCH",
]

# =====================================================================
# Correct placement anchors
# =====================================================================
INITIALIZATION_PLACEMENT_ANCHORS = [
    "100-INITIALIZE",
    "MAIN-PROCEDURE",
    "PERFORM.*OPEN",
]

# =====================================================================
# Paragraph naming convention for init sections
# =====================================================================
INITIALIZATION_PARAGRAPH_PREFIX = "100-INITIALIZE"
INITIALIZATION_PARAGRAPH_TEMPLATE = "{prefix}-{token}"

# =====================================================================
# Diagnostics
# =====================================================================
INITIALIZATION_PLACEMENT_MESSAGES = {
    "violation_found": (
        "Initialization: {init_statement} found immediately after "
        "PROCEDURE DIVISION on line {line}; should be in dedicated paragraph."
    ),
    "corrected": (
        "Initialization: moved {init_statement} to {paragraph}."
    ),
    "paragraph_created": (
        "Initialization: created {paragraph} for DCLGEN initialization."
    ),
    "skipped_unknown_anchor": (
        "Initialization: cannot determine safe placement; manual review needed."
    ),
}

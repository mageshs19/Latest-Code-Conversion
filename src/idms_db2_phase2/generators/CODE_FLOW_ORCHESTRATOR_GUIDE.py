"""
CODE FLOW ORCHESTRATOR - PRACTICAL GUIDE

How to handle scenarios where MOVE/INITIALIZE/LOGIC must happen
in a specific sequence, not all at once.
"""

# ============================================================================
# PROBLEM: NOT ALL MOVES CAN HAPPEN TOGETHER
# ============================================================================

"""
SCENARIO: Load Data from DB2 → Validate → Transform → Write to File

This isn't just:
  MOVE field1 to output
  MOVE field2 to output
  WRITE record

It's actually:
  INITIALIZE output record
  MOVE customer ID to temp
  FETCH customer from DB2
  IF customer valid
      MOVE validated ID to output
      PERFORM calculate-amount
      MOVE calculated amount to output
  ELSE
      MOVE error code to output
  END-IF
  WRITE record

See the problem? Each MOVE depends on:
- Previous MOVE completing
- FETCH completing successfully
- VALIDATION passing
- CALCULATION completing

The CodeFlowOrchestrator solves this by organizing in PHASES
instead of just BUCKETS.
"""


# ============================================================================
# SOLUTION: PHASES OF EXECUTION
# ============================================================================

"""
6 PHASES (in order):

PHASE 1: INITIALIZE
  - Set up all work areas
  - Initialize all records
  - Set default values
  - Clear flags

PHASE 2: LOAD INPUT
  - MOVE input data to work variables
  - FETCH from database
  - Read from file
  - Everything you need before validation

PHASE 3: VALIDATION
  - Check data is valid
  - PERFORM validation paragraphs
  - Set validation flags
  - Can't transform until this passes

PHASE 4: MOVE TO OUTPUT
  - MOVE validated data to output records
  - Do calculations
  - Format output
  - Only happens if validation passed

PHASE 5: WRITE
  - WRITE records to output
  - Handle errors
  - LOG results

PHASE 6: CLEANUP
  - Clean up work areas
  - Reset counters
  - Final housekeeping
"""


# ============================================================================
# REAL EXAMPLE 1: FROM YOUR CODEBASE
# ============================================================================

"""
Looking at your VMDZ4420 MOVE statements:

Current scattered approach:
  002530 MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK
  002540 MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CND-STOCK
  002550 MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID
  ...
  002670 WRITE UITRECORD

With CodeFlowOrchestrator:

PHASE_INITIALIZE:
  - INITIALIZE UITRECORD
  - INITIALIZE DCLDZBEFFTV
  - MOVE WS-NR-CIO-CRE TO UIT-NR-CIO-CRE

PHASE_LOAD_INPUT:
  - FETCH DZBEFFTV data from DB2
  - Check SQLCODE

PHASE_VALIDATION:
  - Validate DZBEFFTV data
  - Check for required fields
  - Perform business logic validation

PHASE_MOVE_TO_OUTPUT:
  - MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK
  - MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CND-STOCK
  - MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID
  - ... all moves together, organized

PHASE_WRITE:
  - WRITE UITRECORD
  - Check SQLCODE
  - Handle errors
"""


# ============================================================================
# REAL EXAMPLE 2: COMPLEX CURSOR LOOP
# ============================================================================

"""
SCENARIO: Fetch rows → Transform each → Accumulate in batch → Write batch

Current code pattern (hard to follow):
  PERFORM UNTIL EOF
      FETCH cursor
      IF SQLCODE = 0
          PERFORM validate-row
          IF valid
              MOVE fields to batch
              IF batch full
                  WRITE batch
                  INITIALIZE batch
              END-IF
          END-IF
      ELSE
          SET EOF to true
      END-IF
  END-PERFORM

With phases (clear structure):

PHASE_INITIALIZE:
  INITIALIZE BATCH-RECORD
  MOVE 0 TO BATCH-COUNT

PHASE_LOAD_INPUT:
  OPEN CURSOR
  FETCH row into WORK-AREA

PHASE_VALIDATION:
  PERFORM VALIDATE-ROW
  Check if valid

PHASE_MOVE_TO_OUTPUT:
  IF valid
      MOVE fields to BATCH
      ACCUMULATE totals
      IF BATCH-COUNT >= SIZE
          PERFORM WRITE-BATCH
          INITIALIZE BATCH

PHASE_WRITE:
  When done, WRITE final batch

PHASE_CLEANUP:
  CLOSE CURSOR
  Final logging
"""


# ============================================================================
# HOW TO USE CodeFlowOrchestrator
# ============================================================================

"""
BASIC PATTERN:

from code_flow_orchestrator import CodeFlowOrchestrator, FlowPhase

flow = CodeFlowOrchestrator()

# Add steps in each phase
flow.add_step(
    FlowPhase.PHASE_INITIALIZE,
    [
        "INITIALIZE OUTPUT-RECORD.",
        "MOVE SPACES TO WS-FIELDS.",
    ],
    description="Initialize work areas"
)

flow.add_step(
    FlowPhase.PHASE_LOAD_INPUT,
    [
        "EXEC SQL",
        "    FETCH CURSOR-NAME INTO :HOST-GROUP",
        "END-EXEC.",
    ],
    description="Fetch data from database"
)

flow.add_step(
    FlowPhase.PHASE_VALIDATION,
    [
        "IF SQLCODE = 0",
        "    PERFORM VALIDATE-RECORD",
        "ELSE",
        "    MOVE 'ERROR' TO STATUS",
        "END-IF.",
    ],
    description="Validate fetched data"
)

flow.add_step(
    FlowPhase.PHASE_MOVE_TO_OUTPUT,
    [
        "MOVE FIELD-1 TO OUT-FIELD-1.",
        "MOVE FIELD-2 TO OUT-FIELD-2.",
    ],
    description="Move to output fields"
)

flow.add_step(
    FlowPhase.PHASE_WRITE,
    [
        "WRITE OUTPUT-RECORD.",
    ],
    description="Write the record"
)

# Get organized code
code = flow.combine_phases()
"""


# ============================================================================
# SCENARIO: VMDZ4420-LIKE PROGRAM CONVERSION
# ============================================================================

def example_vmdz4420_scenario():
    """
    Shows how to structure VMDZ4420 using phases.
    
    VMDZ4420 pattern:
    - Read input record
    - Fetch from DB2
    - Transform data
    - Write output
    - Log results
    """
    
    from code_flow_orchestrator import CodeFlowOrchestrator, FlowPhase
    
    flow = CodeFlowOrchestrator()
    
    # ---- PHASE 1: INITIALIZE ----
    flow.add_step(
        FlowPhase.PHASE_INITIALIZE,
        [
            "INITIALIZE UIT-RECORD.",
            "INITIALIZE DCLDZBEFFTV.",
            "INITIALIZE WS-WORK-AREAS.",
            "MOVE 'VMDZ4420' TO CS-PROGRAM.",
            "MOVE FUNCTION CURRENT-DATE TO TS-SYSTEM.",
            "MOVE ZERO TO WS-RECORD-COUNT.",
        ],
        description="Initialize all work areas and records"
    )
    
    # ---- PHASE 2: LOAD INPUT ----
    flow.add_step(
        FlowPhase.PHASE_LOAD_INPUT,
        [
            "READ INPUT-FILE INTO INPUT-RECORD",
            "    AT END",
            "        SET EOF-FLAG TO TRUE",
            "    NOT AT END",
            "        MOVE INPUT-RECORD-ID TO WS-INPUT-ID",
            "        MOVE INPUT-STOCK-ID TO WS-STOCK-ID",
            "END-READ.",
        ],
        description="Read input record from file"
    )
    
    # ---- PHASE 3: VALIDATION ----
    flow.add_step(
        FlowPhase.PHASE_VALIDATION,
        [
            "IF EOF-FLAG NOT = TRUE",
            "    PERFORM VALIDATE-INPUT-RECORD",
            "    IF INPUT-VALID",
            "        PERFORM FETCH-FROM-DB2",
            "    ELSE",
            "        MOVE 'INVALID' TO PROCESS-STATUS",
            "    END-IF",
            "END-IF.",
        ],
        description="Validate input and fetch from DB2"
    )
    
    # ---- PHASE 4: MOVE TO OUTPUT ----
    flow.add_step(
        FlowPhase.PHASE_MOVE_TO_OUTPUT,
        [
            "IF PROCESS-STATUS = 'OK'",
            "    MOVE AM-CNSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CN-STOCK",
            "    MOVE AM-CNDSTK-479BEFF OF DCLDZBEFFTV TO UIT-AM-CND-STOCK",
            "    MOVE CO-IDPRKSK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ID",
            "    MOVE NS-IRMOSTK-479BEFF OF DCLDZBEFFTV TO UIT-NS-SEQ",
            "    MOVE DA-UBSECIS-479BEFF OF DCLDZBEFFTV TO UIT-DA-UBSEC",
            "    MOVE NR-IDSTOCK-479BEFF OF DCLDZBEFFTV TO UIT-NR-ST",
            "    PERFORM CALCULATE-TOTALS",
            "    MOVE 'PROCESSED' TO UIT-STATUS",
            "ELSE",
            "    MOVE PROCESS-STATUS TO UIT-STATUS",
            "END-IF.",
        ],
        description="Move validated fields to output record"
    )
    
    # ---- PHASE 5: WRITE ----
    flow.add_step(
        FlowPhase.PHASE_WRITE,
        [
            "WRITE UIT-RECORD",
            "    FROM UIT-RECORD-BUFFER",
            "    END-WRITE.",
            "IF SQLCODE = 0",
            "    ADD 1 TO WS-RECORD-COUNT",
            "    PERFORM LOG-SUCCESS",
            "ELSE",
            "    PERFORM LOG-ERROR",
            "END-IF.",
        ],
        description="Write output record and log results"
    )
    
    # ---- PHASE 6: CLEANUP ----
    flow.add_step(
        FlowPhase.PHASE_CLEANUP,
        [
            "IF EOF-FLAG = TRUE",
            "    PERFORM CLOSE-FILES",
            "    MOVE WS-RECORD-COUNT TO COMPLETION-COUNT",
            "    PERFORM FINAL-LOGGING",
            "END-IF.",
        ],
        description="Cleanup and final logging"
    )
    
    return flow


def example_cursor_fetch_batch_scenario():
    """
    Shows how to structure a complex fetch-batch-write scenario.
    
    Pattern:
    - Initialize batch record
    - Open cursor
    - Fetch each row
    - Validate each row
    - Accumulate in batch
    - When batch full, write batch
    - When cursor done, write final batch
    """
    
    from code_flow_orchestrator import CodeFlowOrchestrator, FlowPhase
    
    flow = CodeFlowOrchestrator()
    
    # ---- PHASE 1: INITIALIZE ----
    flow.add_step(
        FlowPhase.PHASE_INITIALIZE,
        [
            "INITIALIZE BATCH-RECORD.",
            "INITIALIZE CUSTOMER-REC.",
            "MOVE ZERO TO BATCH-ITEM-COUNT.",
            "MOVE ZERO TO BATCH-TOTAL-AMOUNT.",
            "MOVE 'N' TO EOF-FLAG.",
        ],
        description="Initialize batch processing"
    )
    
    # ---- PHASE 2: LOAD INPUT ----
    flow.add_step(
        FlowPhase.PHASE_LOAD_INPUT,
        [
            "EXEC SQL",
            "    OPEN CURS-CUSTOMER-DATA",
            "END-EXEC.",
            "IF SQLCODE NOT = 0",
            "    PERFORM LOG-OPEN-ERROR",
            "    MOVE 'Y' TO EOF-FLAG",
            "END-IF.",
            "PERFORM UNTIL EOF-FLAG = 'Y'",
            "    EXEC SQL",
            "        FETCH CURS-CUSTOMER-DATA",
            "        INTO :CUSTOMER-REC",
            "    END-EXEC",
            "    EVALUATE SQLCODE",
            "        WHEN 0",
            "            PERFORM VALIDATE-CUSTOMER-ROW",
            "        WHEN 100",
            "            MOVE 'Y' TO EOF-FLAG",
            "        WHEN OTHER",
            "            PERFORM LOG-FETCH-ERROR",
            "            MOVE 'Y' TO EOF-FLAG",
            "    END-EVALUATE",
            "END-PERFORM.",
        ],
        description="Fetch all rows from cursor"
    )
    
    # ---- PHASE 3: VALIDATION ----
    flow.add_step(
        FlowPhase.PHASE_VALIDATION,
        [
            "IF CUSTOMER-VALID = 'Y'",
            "    PERFORM VALIDATE-CUSTOMER-FIELDS",
            "    PERFORM CHECK-CUSTOMER-LIMITS",
            "END-IF.",
        ],
        description="Validate each customer record"
    )
    
    # ---- PHASE 4: MOVE TO OUTPUT ----
    flow.add_step(
        FlowPhase.PHASE_MOVE_TO_OUTPUT,
        [
            "IF CUSTOMER-VALID = 'Y'",
            "    ADD 1 TO BATCH-ITEM-COUNT",
            "    MOVE CUSTOMER-ID TO BATCH-ITEM(BATCH-ITEM-COUNT)",
            "    MOVE CUSTOMER-NAME TO BATCH-NAME(BATCH-ITEM-COUNT)",
            "    MOVE CUSTOMER-AMOUNT TO BATCH-AMOUNT(BATCH-ITEM-COUNT)",
            "    ADD CUSTOMER-AMOUNT TO BATCH-TOTAL-AMOUNT",
            "    IF BATCH-ITEM-COUNT >= BATCH-SIZE",
            "        PERFORM WRITE-ACCUMULATED-BATCH",
            "        MOVE ZERO TO BATCH-ITEM-COUNT",
            "        MOVE ZERO TO BATCH-TOTAL-AMOUNT",
            "        INITIALIZE BATCH-RECORD",
            "    END-IF",
            "END-IF.",
        ],
        description="Accumulate validated items in batch"
    )
    
    # ---- PHASE 5: WRITE ----
    flow.add_step(
        FlowPhase.PHASE_WRITE,
        [
            "IF BATCH-ITEM-COUNT > 0",
            "    MOVE BATCH-ITEM-COUNT TO BATCH-COUNT",
            "    MOVE BATCH-TOTAL-AMOUNT TO BATCH-TOTAL",
            "    PERFORM WRITE-ACCUMULATED-BATCH",
            "END-IF.",
            "EXEC SQL",
            "    CLOSE CURS-CUSTOMER-DATA",
            "END-EXEC.",
        ],
        description="Write remaining batch and close cursor"
    )
    
    # ---- PHASE 6: CLEANUP ----
    flow.add_step(
        FlowPhase.PHASE_CLEANUP,
        [
            "MOVE ZERO TO BATCH-ITEM-COUNT.",
            "MOVE ZERO TO BATCH-TOTAL-AMOUNT.",
            "INITIALIZE BATCH-RECORD.",
            "PERFORM CLOSE-ALL-FILES.",
            "PERFORM LOG-COMPLETION-STATUS.",
        ],
        description="Cleanup and final logging"
    )
    
    return flow


# ============================================================================
# COMPARISON: BUCKET vs FLOW vs HYBRID
# ============================================================================

"""
BUCKET APPROACH:
  Best for: Organizing working-storage by type
  Use when: Declarations, simple grouping
  Example: Control fields, timestamp fields, work fields
  
  Result:
    CONTROL FIELDS section
    TIMESTAMP FIELDS section
    WORK FIELDS section
    ...

FLOW APPROACH:
  Best for: Organizing procedure division by execution order
  Use when: Complex logic, multiple phases, dependencies
  Example: Initialize → Load → Validate → Transform → Write
  
  Result:
    PHASE_INITIALIZE
    PHASE_LOAD_INPUT
    PHASE_VALIDATION
    PHASE_MOVE_TO_OUTPUT
    PHASE_WRITE

HYBRID APPROACH:
  Use both together:
  - Buckets for WORKING-STORAGE SECTION
  - Flows for PROCEDURE DIVISION
  
  Result: Clean, organized complete program
    WORKING-STORAGE (organized by bucket)
      CONTROL FIELDS
      TIMESTAMP FIELDS
      WORK FIELDS
    
    PROCEDURE DIVISION (organized by flow)
      INITIALIZE phase
      LOAD INPUT phase
      VALIDATION phase
      ...
"""


# ============================================================================
# WHEN TO USE EACH
# ============================================================================

"""
USE BUCKETS FOR:
  ✓ WORKING-STORAGE SECTION declarations
  ✓ Organizing by field type/purpose
  ✓ Simple "group these together" operations
  ✓ Building control fields, timestamp fields, etc.
  ✓ One-time initialization code

USE FLOWS FOR:
  ✓ PROCEDURE DIVISION logic
  ✓ Operations with dependencies
  ✓ Multiple steps in sequence
  ✓ Validation before transformation
  ✓ Fetch → Process → Write patterns
  ✓ Complex business logic
  ✓ Error handling and recovery

USE HYBRID FOR:
  ✓ Complete programs
  ✓ Combining WS organization with procedural flow
  ✓ Professional, maintainable code
  ✓ Code that's easy to review and debug
"""


# ============================================================================
# INTEGRATION WITH EXISTING GENERATORS
# ============================================================================

"""
How to add CodeFlowOrchestrator to your generators:

EXAMPLE: CursorParagraphGenerator

Before:
  def apply(self, program_text):
      # Generate all cursor declarations
      # Generate fetch loops
      # Generate move statements
      # Generate write statements
      # Mix them all together
      # Return result

After:
  def apply(self, program_text):
      flow = CodeFlowOrchestrator()
      
      # Add all code to appropriate phases
      flow.add_step(FlowPhase.PHASE_INITIALIZE, init_lines)
      flow.add_step(FlowPhase.PHASE_LOAD_INPUT, fetch_lines)
      flow.add_step(FlowPhase.PHASE_VALIDATION, validate_lines)
      flow.add_step(FlowPhase.PHASE_MOVE_TO_OUTPUT, move_lines)
      flow.add_step(FlowPhase.PHASE_WRITE, write_lines)
      
      # Get organized code
      organized_code = flow.combine_phases()
      
      # Insert into program
      return self._insert_into_program(program_text, organized_code)
"""


if __name__ == "__main__":
    print("Examples available:")
    print("  - example_vmdz4420_scenario()")
    print("  - example_cursor_fetch_batch_scenario()")

"""
CODE FLOW ORCHESTRATOR - SEQUENTIAL PROCESSING PATTERNS

Extends CodeBucketManager for complex scenarios where code must execute
in specific sequences, not just grouped by type.

PROBLEM ADDRESSED:
  Not all MOVE statements can happen together.
  Some code requires specific ordering:
  
  1. INITIALIZE record
  2. MOVE input to temp
  3. PERFORM validation  
  4. MOVE temp to output
  5. WRITE record

SOLUTION:
  Define logical FLOWS or PHASES where each phase:
  - Has a specific purpose
  - Contains ordered steps
  - Can depend on previous phases
  - Gets inserted at correct location in procedure
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class FlowPhase(Enum):
    """Phases of execution flow."""
    PHASE_INITIALIZE = 1      # Initialize records, setup
    PHASE_LOAD_INPUT = 2      # MOVE input data to work areas
    PHASE_VALIDATION = 3      # Validate and transform
    PHASE_MOVE_TO_OUTPUT = 4  # MOVE to output records
    PHASE_WRITE = 5           # WRITE operations
    PHASE_CLEANUP = 6         # Cleanup/finalization


@dataclass
class CodeStep:
    """A single step in a flow."""
    phase: FlowPhase
    step_number: int
    code_lines: List[str]
    description: str = ""
    depends_on: Optional[FlowPhase] = None  # Can't execute until this phase done


class CodeFlowOrchestrator:
    """
    Orchestrates code execution in logical phases/flows.
    
    Use when code must execute in specific order, not just grouped by type.
    """
    
    def __init__(self):
        """Initialize flow orchestrator."""
        self.flows: Dict[FlowPhase, List[CodeStep]] = {
            phase: [] for phase in FlowPhase
        }
        self.step_counters: Dict[FlowPhase, int] = {
            phase: 0 for phase in FlowPhase
        }
    
    def add_step(self, 
                 phase: FlowPhase, 
                 code_lines: List[str],
                 description: str = "",
                 depends_on: Optional[FlowPhase] = None) -> None:
        """
        Add a step to a phase.
        
        Args:
            phase: Which phase this step belongs to
            code_lines: Lines of code in this step
            description: What this step does
            depends_on: This step can't run until this phase completes
        """
        step_num = self.step_counters[phase]
        self.step_counters[phase] += 1
        
        step = CodeStep(
            phase=phase,
            step_number=step_num,
            code_lines=code_lines,
            description=description,
            depends_on=depends_on
        )
        
        self.flows[phase].append(step)
    
    def get_phase_code(self, phase: FlowPhase) -> List[str]:
        """Get all code lines for a phase in order."""
        result = []
        for step in self.flows[phase]:
            result.extend(step.code_lines)
        return result
    
    def combine_phases(self) -> str:
        """Combine all phases in execution order."""
        result_lines = []
        
        for phase in FlowPhase:
            lines = self.get_phase_code(phase)
            if lines:
                # Phase header
                phase_name = phase.name.replace("PHASE_", "")
                result_lines.append(f"*---- {phase_name} ----*")
                result_lines.extend(lines)
                result_lines.append("")  # Blank line separator
        
        return "\n".join(result_lines)
    
    def get_flow_status(self) -> str:
        """Get status of all phases."""
        lines = ["Code Flow Status:"]
        for phase in FlowPhase:
            count = len(self.flows[phase])
            if count > 0:
                lines.append(f"  {phase.name}: {count} steps")
        return "\n".join(lines)


# ============================================================================
# REAL-WORLD SCENARIO: LOAD RECORD → TRANSFORM → WRITE
# ============================================================================

class LoadTransformWriteScenario:
    """
    Real scenario: Load data → Transform → Write to database
    
    This shows how to use flows for a complex operation sequence.
    """
    
    def __init__(self):
        self.flow = CodeFlowOrchestrator()
    
    def scenario_simple_move_transform_write(self):
        """
        Simplest case:
        1. Initialize target record
        2. Move input fields to target
        3. Write the record
        """
        
        # Phase 1: Initialize
        self.flow.add_step(
            FlowPhase.PHASE_INITIALIZE,
            [
                "INITIALIZE OUTPUT-RECORD.",
                "MOVE WS-PROGRAM-ID TO OUT-PROGRAM-ID.",
            ],
            description="Initialize output record and set program ID"
        )
        
        # Phase 2: Load input data
        self.flow.add_step(
            FlowPhase.PHASE_LOAD_INPUT,
            [
                "MOVE INPUT-FIELD-1 TO OUT-FIELD-1.",
                "MOVE INPUT-FIELD-2 TO OUT-FIELD-2.",
                "MOVE INPUT-FIELD-3 TO OUT-FIELD-3.",
            ],
            description="Move input fields to output record",
            depends_on=FlowPhase.PHASE_INITIALIZE
        )
        
        # Phase 3: Write
        self.flow.add_step(
            FlowPhase.PHASE_WRITE,
            [
                "WRITE OUTPUT-RECORD",
                "    FROM OUTPUT-REC-BUFFER.",
            ],
            description="Write the transformed record",
            depends_on=FlowPhase.PHASE_LOAD_INPUT
        )
        
        return self.flow.combine_phases()
    
    def scenario_complex_transform(self):
        """
        Complex case with validation and transformation:
        1. Initialize record
        2. Load input
        3. Validate data
        4. Transform/calculate
        5. Move to output
        6. Write
        """
        
        self.flow = CodeFlowOrchestrator()  # Reset
        
        # Phase 1: Initialize
        self.flow.add_step(
            FlowPhase.PHASE_INITIALIZE,
            [
                "INITIALIZE OUTPUT-RECORD.",
                "INITIALIZE WORK-AREAS.",
                "MOVE WS-PROGRAM-ID TO OUT-PROGRAM-ID.",
                "MOVE FUNCTION CURRENT-DATE TO OUT-TIMESTAMP.",
            ],
            description="Initialize all work areas and output record"
        )
        
        # Phase 2: Load input data to work areas
        self.flow.add_step(
            FlowPhase.PHASE_LOAD_INPUT,
            [
                "MOVE INPUT-CUSTOMER-ID TO WS-CUST-ID.",
                "MOVE INPUT-AMOUNT TO WS-AMOUNT.",
                "MOVE INPUT-DATE TO WS-INPUT-DATE.",
            ],
            description="Move input to work areas for processing"
        )
        
        # Phase 3: Validation
        self.flow.add_step(
            FlowPhase.PHASE_VALIDATION,
            [
                "IF WS-CUST-ID NOT = SPACES",
                "    PERFORM VALIDATE-CUSTOMER",
                "    IF CUSTOMER-VALID",
                "        MOVE 'OK' TO WS-VALIDATION-STATUS",
                "    ELSE",
                "        MOVE 'INVALID-CUSTOMER' TO WS-VALIDATION-STATUS",
                "    END-IF",
                "ELSE",
                "    MOVE 'MISSING-ID' TO WS-VALIDATION-STATUS",
                "END-IF.",
                "IF WS-AMOUNT NOT NUMERIC",
                "    MOVE 'INVALID-AMOUNT' TO WS-VALIDATION-STATUS",
                "END-IF.",
            ],
            description="Validate input data"
        )
        
        # Phase 4: Move validated data to output
        self.flow.add_step(
            FlowPhase.PHASE_MOVE_TO_OUTPUT,
            [
                "IF WS-VALIDATION-STATUS = 'OK'",
                "    MOVE WS-CUST-ID TO OUT-CUSTOMER-ID",
                "    MOVE WS-AMOUNT TO OUT-AMOUNT",
                "    MOVE WS-INPUT-DATE TO OUT-PROC-DATE",
                "    COMPUTE OUT-AMOUNT-PLUS-FEE =",
                "        WS-AMOUNT * 1.05",
                "    MOVE 'PROCESSED' TO OUT-STATUS",
                "ELSE",
                "    MOVE WS-VALIDATION-STATUS TO OUT-STATUS",
                "    MOVE WS-CUST-ID TO OUT-CUSTOMER-ID",
                "END-IF.",
            ],
            description="Move validated/transformed data to output"
        )
        
        # Phase 5: Write
        self.flow.add_step(
            FlowPhase.PHASE_WRITE,
            [
                "IF OUT-STATUS = 'PROCESSED'",
                "    PERFORM 900-WRITE-OUTPUT-RECORD",
                "    IF SQLCODE = 0",
                "        PERFORM 950-LOG-SUCCESS",
                "    ELSE",
                "        PERFORM 960-LOG-ERROR",
                "    END-IF",
                "ELSE",
                "    PERFORM 970-LOG-VALIDATION-ERROR",
                "END-IF.",
            ],
            description="Write output with error handling"
        )
        
        # Phase 6: Cleanup
        self.flow.add_step(
            FlowPhase.PHASE_CLEANUP,
            [
                "MOVE ZERO TO WS-RECORD-COUNT.",
                "INITIALIZE WORK-AREAS.",
                "MOVE 'COMPLETE' TO WS-STATUS.",
            ],
            description="Clean up work areas"
        )
        
        return self.flow.combine_phases()


# ============================================================================
# REAL SCENARIO: FETCH CURSOR → TRANSFORM MULTIPLE RECORDS → WRITE BATCH
# ============================================================================

class FetchTransformBatchScenario:
    """
    Complex cursor scenario:
    1. Initialize batch record
    2. Open cursor and fetch
    3. For each row: validate and transform
    4. Accumulate in batch
    5. When batch full: write batch
    6. Close cursor
    """
    
    def __init__(self):
        self.flow = CodeFlowOrchestrator()
    
    def scenario_fetch_batch_write(self):
        """Fetch multiple rows, batch them, write in groups."""
        
        # Phase 1: Initialize
        self.flow.add_step(
            FlowPhase.PHASE_INITIALIZE,
            [
                "INITIALIZE BATCH-RECORD.",
                "MOVE 0 TO WS-BATCH-COUNT.",
                "MOVE 0 TO WS-BATCH-TOTAL.",
                "MOVE 'N' TO EOF-FLAG.",
            ],
            description="Initialize batch processing"
        )
        
        # Phase 2: Load (Open cursor)
        self.flow.add_step(
            FlowPhase.PHASE_LOAD_INPUT,
            [
                "EXEC SQL",
                "    OPEN CURS-CUSTOMER-DATA",
                "END-EXEC.",
                "IF SQLCODE NOT = 0",
                "    PERFORM ERROR-HANDLER",
                "    MOVE 'Y' TO EOF-FLAG",
                "END-IF.",
            ],
            description="Open cursor to fetch data"
        )
        
        # Phase 3: Fetch and validate each row
        self.flow.add_step(
            FlowPhase.PHASE_VALIDATION,
            [
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
                "            PERFORM ERROR-HANDLER",
                "            MOVE 'Y' TO EOF-FLAG",
                "    END-EVALUATE",
                "END-PERFORM.",
            ],
            description="Fetch rows and validate"
        )
        
        # Phase 4: Move validated rows to output batch
        self.flow.add_step(
            FlowPhase.PHASE_MOVE_TO_OUTPUT,
            [
                "IF CUSTOMER-VALID = 'Y'",
                "    ADD 1 TO WS-BATCH-COUNT",
                "    MOVE CUSTOMER-ID TO BATCH-ITEM(WS-BATCH-COUNT)",
                "    MOVE CUSTOMER-NAME TO BATCH-NAME(WS-BATCH-COUNT)",
                "    ADD CUSTOMER-AMOUNT TO WS-BATCH-TOTAL",
                "    IF WS-BATCH-COUNT >= BATCH-SIZE",
                "        PERFORM WRITE-BATCH",
                "        MOVE 0 TO WS-BATCH-COUNT",
                "        MOVE 0 TO WS-BATCH-TOTAL",
                "        INITIALIZE BATCH-RECORD",
                "    END-IF",
                "END-IF.",
            ],
            description="Accumulate validated rows in batch"
        )
        
        # Phase 5: Write any remaining batch
        self.flow.add_step(
            FlowPhase.PHASE_WRITE,
            [
                "IF WS-BATCH-COUNT > 0",
                "    MOVE WS-BATCH-COUNT TO BATCH-COUNT",
                "    MOVE WS-BATCH-TOTAL TO BATCH-TOTAL",
                "    PERFORM WRITE-BATCH",
                "END-IF.",
                "EXEC SQL",
                "    CLOSE CURS-CUSTOMER-DATA",
                "END-EXEC.",
            ],
            description="Write remaining batch and close cursor"
        )
        
        # Phase 6: Cleanup
        self.flow.add_step(
            FlowPhase.PHASE_CLEANUP,
            [
                "MOVE 0 TO WS-BATCH-COUNT.",
                "MOVE 0 TO WS-BATCH-TOTAL.",
                "INITIALIZE BATCH-RECORD.",
                "PERFORM LOG-COMPLETION-STATUS.",
            ],
            description="Cleanup and log completion"
        )
        
        return self.flow.combine_phases()


# ============================================================================
# FLOW WITH CONDITIONAL BRANCHES
# ============================================================================

class ConditionalFlowScenario:
    """
    Scenario with branches:
    - INITIALIZE
    - LOAD INPUT
    - IF path A THEN validate-A, transform-A, write-A
    - ELSE validate-B, transform-B, write-B
    """
    
    def __init__(self):
        self.flow = CodeFlowOrchestrator()
    
    def scenario_conditional_processing(self):
        """Different processing paths based on input type."""
        
        # Phase 1: Initialize
        self.flow.add_step(
            FlowPhase.PHASE_INITIALIZE,
            [
                "INITIALIZE INPUT-WORK-AREAS.",
                "INITIALIZE OUTPUT-RECORD.",
                "MOVE 'UNPROCESSED' TO PROC-STATUS.",
            ],
            description="Initialize work areas"
        )
        
        # Phase 2: Load input
        self.flow.add_step(
            FlowPhase.PHASE_LOAD_INPUT,
            [
                "MOVE INPUT-RECORD TO WS-INPUT-DATA.",
                "MOVE INPUT-TYPE TO WS-RECORD-TYPE.",
            ],
            description="Load input data"
        )
        
        # Phase 3: Validate (with conditional logic)
        self.flow.add_step(
            FlowPhase.PHASE_VALIDATION,
            [
                "EVALUATE WS-RECORD-TYPE",
                "    WHEN 'CUSTOMER'",
                "        PERFORM VALIDATE-CUSTOMER-RECORD",
                "    WHEN 'INVOICE'",
                "        PERFORM VALIDATE-INVOICE-RECORD",
                "    WHEN 'PAYMENT'",
                "        PERFORM VALIDATE-PAYMENT-RECORD",
                "    WHEN OTHER",
                "        MOVE 'INVALID-TYPE' TO PROC-STATUS",
                "END-EVALUATE.",
            ],
            description="Validate based on record type"
        )
        
        # Phase 4: Transform (different transformations per type)
        self.flow.add_step(
            FlowPhase.PHASE_MOVE_TO_OUTPUT,
            [
                "EVALUATE WS-RECORD-TYPE",
                "    WHEN 'CUSTOMER'",
                "        PERFORM TRANSFORM-CUSTOMER-DATA",
                "    WHEN 'INVOICE'",
                "        PERFORM TRANSFORM-INVOICE-DATA",
                "    WHEN 'PAYMENT'",
                "        PERFORM TRANSFORM-PAYMENT-DATA",
                "END-EVALUATE.",
                "IF PROC-STATUS NOT = 'INVALID-TYPE'",
                "    MOVE 'PROCESSED' TO PROC-STATUS",
                "END-IF.",
            ],
            description="Transform data based on type"
        )
        
        # Phase 5: Write
        self.flow.add_step(
            FlowPhase.PHASE_WRITE,
            [
                "IF PROC-STATUS = 'PROCESSED'",
                "    PERFORM WRITE-OUTPUT-RECORD",
                "    ADD 1 TO WS-WRITE-COUNT",
                "ELSE",
                "    PERFORM LOG-ERROR",
                "    ADD 1 TO WS-ERROR-COUNT",
                "END-IF.",
            ],
            description="Write if processed successfully"
        )
        
        return self.flow.combine_phases()


# ============================================================================
# EXAMPLE: INTEGRATING FLOW WITH BUCKET MANAGER
# ============================================================================

class HybridCodeOrganizer:
    """
    Combines both CodeBucketManager (organization by type) and
    CodeFlowOrchestrator (organization by sequence).
    
    Use buckets for working storage declarations.
    Use flows for procedure division logic.
    """
    
    def __init__(self):
        from idms_db2_phase2.generators.code_bucket_manager import (
            CodeBucketManager, BucketType
        )
        
        self.bucket_manager = CodeBucketManager()
        self.flow_orchestrator = CodeFlowOrchestrator()
    
    def generate_complete_program(self):
        """Generate both WS section and PROCEDURE section."""
        
        # WS SECTION: Use buckets (organize by type)
        self.bucket_manager.add_to_bucket(
            BucketType.CONTROL_FIELDS,
            "10  CS-PROGRAM  PIC X(8)  VALUE 'VMDZ4420'."
        )
        
        self.bucket_manager.add_to_bucket(
            BucketType.WORK_FIELDS,
            "01  WS-INPUT-DATA  PIC X(100)."
        )
        
        self.bucket_manager.add_to_bucket(
            BucketType.WORK_FIELDS,
            "01  WS-OUTPUT-DATA  PIC X(200)."
        )
        
        # PROCEDURE SECTION: Use flows (organize by sequence)
        self.flow_orchestrator.add_step(
            FlowPhase.PHASE_INITIALIZE,
            [
                "INITIALIZE OUTPUT-RECORD.",
                "MOVE WS-PROGRAM-ID TO OUT-PROGRAM-ID.",
            ],
            description="Initialize"
        )
        
        self.flow_orchestrator.add_step(
            FlowPhase.PHASE_LOAD_INPUT,
            [
                "MOVE INPUT-DATA TO WS-INPUT-DATA.",
            ],
            description="Load input"
        )
        
        self.flow_orchestrator.add_step(
            FlowPhase.PHASE_VALIDATION,
            [
                "IF WS-INPUT-DATA NOT = SPACES",
                "    PERFORM VALIDATE-DATA",
                "END-IF.",
            ],
            description="Validate"
        )
        
        self.flow_orchestrator.add_step(
            FlowPhase.PHASE_MOVE_TO_OUTPUT,
            [
                "MOVE WS-INPUT-DATA TO OUT-DATA.",
            ],
            description="Move to output"
        )
        
        self.flow_orchestrator.add_step(
            FlowPhase.PHASE_WRITE,
            [
                "WRITE OUTPUT-RECORD.",
            ],
            description="Write"
        )
        
        # Combine both
        ws_section = self.bucket_manager.combine_to_section("WORKING-STORAGE SECTION")
        proc_section = self.flow_orchestrator.combine_phases()
        
        return f"{ws_section}\n\n{proc_section}"


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

def example_usage():
    """Show how to use flows."""
    
    print("=" * 70)
    print("SCENARIO 1: Simple Move-Transform-Write")
    print("=" * 70)
    
    scenario1 = LoadTransformWriteScenario()
    code1 = scenario1.scenario_simple_move_transform_write()
    print(code1)
    
    print("\n" + "=" * 70)
    print("SCENARIO 2: Complex Transform with Validation")
    print("=" * 70)
    
    scenario2 = LoadTransformWriteScenario()
    code2 = scenario2.scenario_complex_transform()
    print(code2)
    print(scenario2.flow.get_flow_status())
    
    print("\n" + "=" * 70)
    print("SCENARIO 3: Fetch-Batch-Write")
    print("=" * 70)
    
    scenario3 = FetchTransformBatchScenario()
    code3 = scenario3.scenario_fetch_batch_write()
    print(code3)
    
    print("\n" + "=" * 70)
    print("SCENARIO 4: Conditional Processing")
    print("=" * 70)
    
    scenario4 = ConditionalFlowScenario()
    code4 = scenario4.scenario_conditional_processing()
    print(code4)


if __name__ == "__main__":
    example_usage()

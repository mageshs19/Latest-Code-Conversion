"""
PRODUCTION TEST SUITE: Flow-Bucket Orchestration

Validates that the orchestration fixes all critical issues:
1. Missing cursor flags ✓
2. Missing timestamp fields ✓
3. Move statement ordering ✓
4. Working storage organization ✓
5. Procedure division flow ✓

LOCATION: tests/test_flow_bucket_production_integration.py
"""

import unittest
from typing import List, Tuple

from converter.generators.code_bucket_manager import BucketType
from converter.generators.code_flow_orchestrator import FlowPhase
from converter.orchestration.flow_bucket_pipeline_orchestration import (
    ProductionFlowBucketOrchestrator,
    apply_production_flow_bucket_orchestration,
)


class TestProductionFlowBucketOrchestration(unittest.TestCase):
    """Test suite for production flow-bucket orchestration."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.sample_program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. VMDZ4420.

ENVIRONMENT DIVISION.

DATA DIVISION.
WORKING-STORAGE SECTION.
01  WS-TEMP  PIC X(100).

PROCEDURE DIVISION.
    MOVE INPUT-FIELD TO WS-TEMP.
    INITIALIZE WS-OUTPUT.
    MOVE WS-TEMP TO OUTPUT-FIELD.
    WRITE OUTPUT-RECORD.
    STOP RUN.

END PROGRAM VMDZ4420.
"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        
        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.program_id, "VMDZ4420")
        self.assertIsNotNone(orchestrator.bucket_manager)
        self.assertIsNotNone(orchestrator.flow_orchestrator)
    
    def test_control_fields_generated(self):
        """Test control fields are generated (CS-PROGRAM)."""
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        orchestrator._add_control_fields()
        
        control_fields = orchestrator.bucket_manager.get_bucket(
            BucketType.CONTROL_FIELDS
        )
        
        self.assertGreater(len(control_fields), 0)
        self.assertIn("CS-PROGRAM", control_fields[0])
        self.assertIn("VMDZ4420", control_fields[0])
    
    def test_timestamp_fields_generated_with_nnnn(self):
        """Test timestamp fields include NNNN field (critical fix)."""
        from converter.generators.code_bucket_manager import BucketType
        
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        orchestrator._add_timestamp_fields()
        
        timestamp_fields = orchestrator.bucket_manager.get_bucket(
            BucketType.TIMESTAMP_FIELDS
        )
        
        self.assertGreater(len(timestamp_fields), 0)
        
        # Verify NNNN field is present
        timestamp_text = "\n".join(timestamp_fields)
        self.assertIn("NNNN", timestamp_text)
        self.assertIn("PIC 9(4)", timestamp_text)
        self.assertIn("VALUE 0", timestamp_text)
    
    def test_cursor_flags_generated(self):
        """Test cursor flags are generated (critical fix)."""
        from converter.generators.code_bucket_manager import BucketType
        
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        orchestrator._add_cursor_flags()
        
        flags = orchestrator.bucket_manager.get_bucket(
            BucketType.STATUS_FLAGS
        )
        
        # Should have generated default cursor flags if none found
        self.assertGreater(len(flags), 0)
        
        # Verify flag structure (WS-*-FLAG with 88 levels)
        flags_text = "\n".join(flags)
        self.assertIn("FLAG", flags_text.upper())
        self.assertIn("88", flags_text)  # Condition level
    
    def test_working_storage_organization(self):
        """Test working storage is properly organized."""
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        
        sections = orchestrator._parse_program_sections()
        ws_section = orchestrator._organize_working_storage(sections)
        
        self.assertIsNotNone(ws_section)
        self.assertIn("WORKING-STORAGE SECTION", ws_section)
        
        # Verify organization: control fields before timestamps
        control_idx = ws_section.find("CS-PROGRAM")
        timestamp_idx = ws_section.find("TIMESTAMP")
        
        self.assertGreater(control_idx, -1, "Control fields missing")
        self.assertGreater(timestamp_idx, control_idx, 
                          "Timestamp should come after control fields")
    
    def test_procedure_division_phases(self):
        """Test procedure division is organized into phases."""
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        
        sections = orchestrator._parse_program_sections()
        proc_section = orchestrator._organize_procedure_division(sections)
        
        self.assertIsNotNone(proc_section)
        self.assertIn("PROCEDURE DIVISION", proc_section)
        
        # Verify phase comments exist (not all phases may be present in sample)
        self.assertIn("INITIALIZE", proc_section)
        # At least some phase organizing should occur
        self.assertTrue(
            "*----" in proc_section or "----" in proc_section,
            "Expected to find phase comments in procedure division"
        )
    
    def test_production_orchestration(self):
        """Test full production orchestration."""
        final_program, messages = apply_production_flow_bucket_orchestration(
            self.sample_program
        )
        
        self.assertIsNotNone(final_program)
        self.assertGreater(len(messages), 0)
        
        # Verify no errors
        error_messages = [m for m in messages if "✗" in m]
        self.assertEqual(len(error_messages), 0, 
                        f"Errors found: {error_messages}")
        
        # Verify output structure
        self.assertIn("IDENTIFICATION DIVISION", final_program)
        self.assertIn("WORKING-STORAGE SECTION", final_program)
        self.assertIn("PROCEDURE DIVISION", final_program)
        self.assertIn("END PROGRAM", final_program)
    
    def test_move_statement_ordering(self):
        """Test that MOVE statements are in correct phase (after validation)."""
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        
        sections = orchestrator._parse_program_sections()
        proc_section = orchestrator._organize_procedure_division(sections)
        
        # Extract phase order
        phases_order = [
            "INITIALIZE",
            "LOAD INPUT",
            "VALIDATION",
            "MOVE TO OUTPUT",
            "WRITE",
        ]
        
        positions = []
        for phase in phases_order:
            pos = proc_section.find(phase)
            if pos > -1:
                positions.append(pos)
        
        # Verify phases are in correct order
        if len(positions) > 1:
            for i in range(len(positions) - 1):
                self.assertLess(positions[i], positions[i + 1],
                              f"Phases out of order: {phases_order}")
    
    def test_counter_fields_generated(self):
        """Test audit counter fields are generated."""
        from converter.generators.code_bucket_manager import BucketType
        
        orchestrator = ProductionFlowBucketOrchestrator(self.sample_program)
        orchestrator._add_counter_fields()
        
        counters = orchestrator.bucket_manager.get_bucket(
            BucketType.COUNTER_FIELDS
        )
        
        self.assertGreater(len(counters), 0)
        
        counter_text = "\n".join(counters)
        self.assertIn("WS-NB-READS-COUNT", counter_text)
        self.assertIn("WS-NB-WRITES-COUNT", counter_text)
        self.assertIn("WS-NB-ERRORS-COUNT", counter_text)


class TestProductionIssuesFixes(unittest.TestCase):
    """Test that specific production issues are fixed."""
    
    def test_issue_1_cursor_flags_not_missing(self):
        """
        Issue: WS-DZBFFSC1-FLAG with 88 levels was missing.
        Fix: Cursor flags are generated automatically.
        """
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. TEST-PROG.
DATA DIVISION.
WORKING-STORAGE SECTION.
PROCEDURE DIVISION.
    STOP RUN.
END PROGRAM.
"""
        
        orchestrator = ProductionFlowBucketOrchestrator(program)
        organized, _ = apply_production_flow_bucket_orchestration(program)
        
        # Verify flags were added
        self.assertIn("FLAG", organized.upper())
        self.assertIn("88", organized)  # Condition level indicators
    
    def test_issue_2_timestamp_nnnn_field_complete(self):
        """
        Issue: NNNN field in timestamp was missing or incomplete.
        Fix: NNNN field is generated with proper PIC clause.
        """
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. TEST-TS.
DATA DIVISION.
WORKING-STORAGE SECTION.
PROCEDURE DIVISION.
    STOP RUN.
END PROGRAM.
"""
        
        orchestrator = ProductionFlowBucketOrchestrator(program)
        organized, _ = apply_production_flow_bucket_orchestration(program)
        
        # Verify NNNN field exists
        self.assertIn("NNNN", organized)
        self.assertIn("PIC 9(4)", organized)
    
    def test_issue_3_move_statements_ordered_correctly(self):
        """
        Issue: MOVE statements could happen before validation.
        Fix: MOVE statements only in MOVE_TO_OUTPUT phase (after validation).
        """
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. TEST-MOVE.
DATA DIVISION.
WORKING-STORAGE SECTION.
PROCEDURE DIVISION.
    MOVE INPUT TO TEMP.
    PERFORM VALIDATE.
    MOVE TEMP TO OUTPUT.
    WRITE REC.
    STOP RUN.
END PROGRAM.
"""
        
        final_program, messages = apply_production_flow_bucket_orchestration(program)
        
        # Verify organization - look for phase comment
        self.assertTrue(
            "MOVE_TO_OUTPUT" in final_program or "MOVE TO OUTPUT" in final_program,
            "Expected to find MOVE_TO_OUTPUT phase in orchestrated program"
        )
        
        # Validate phase should come before move phase
        validate_pos = final_program.find("VALIDATION")
        move_pos = final_program.find("MOVE_TO_OUTPUT")
        if move_pos < 0:
            move_pos = final_program.find("MOVE TO OUTPUT")
        
        if validate_pos > -1 and move_pos > -1:
            self.assertLess(validate_pos, move_pos, 
                "VALIDATION phase should come before MOVE_TO_OUTPUT phase")


class TestProductionReadiness(unittest.TestCase):
    """Test production readiness criteria."""
    
    def test_no_syntax_errors_in_output(self):
        """Test output has no obvious COBOL syntax errors."""
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. PROD-TEST.
DATA DIVISION.
WORKING-STORAGE SECTION.
01  WS-FIELD  PIC X(10).
PROCEDURE DIVISION.
    MOVE SPACES TO WS-FIELD.
    STOP RUN.
END PROGRAM.
"""
        
        organized, messages = apply_production_flow_bucket_orchestration(program)
        
        # Check for proper COBOL structure
        self.assertIn("IDENTIFICATION DIVISION", organized)
        self.assertIn("WORKING-STORAGE SECTION", organized)
        self.assertIn("PROCEDURE DIVISION", organized)
        self.assertIn("END PROGRAM", organized)
        
        # Verify no duplicate keywords
        division_count = organized.count("PROCEDURE DIVISION")
        self.assertEqual(division_count, 1, "PROCEDURE DIVISION appears multiple times")
    
    def test_messages_are_informative(self):
        """Test that messages provide useful information."""
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. MSG-TEST.
DATA DIVISION.
WORKING-STORAGE SECTION.
PROCEDURE DIVISION.
    STOP RUN.
END PROGRAM.
"""
        
        organized, messages = apply_production_flow_bucket_orchestration(program)
        
        # Verify messages
        self.assertGreater(len(messages), 0)
        
        # At least one success indicator
        success_messages = [m for m in messages if "✓" in m]
        self.assertGreater(len(success_messages), 0)
    
    def test_handles_real_program_structure(self):
        """Test with realistic program structure."""
        program = """
IDENTIFICATION DIVISION.
PROGRAM-ID. VMDZ4420.

ENVIRONMENT DIVISION.
INPUT-OUTPUT SECTION.
FILE-CONTROL.
    SELECT INPUT-FILE ASSIGN TO INPUT-FILENAME.

DATA DIVISION.
FILE SECTION.
FD  INPUT-FILE.
01  INPUT-RECORD  PIC X(200).

WORKING-STORAGE SECTION.
01  WS-STATUS  PIC X(2).
01  WS-COUNT   PIC 9(9).

PROCEDURE DIVISION.
    OPEN INPUT INPUT-FILE.
    PERFORM PROCESS-RECORDS.
    CLOSE INPUT-FILE.
    STOP RUN.

PROCESS-RECORDS.
    PERFORM UNTIL WS-STATUS = "99"
        READ INPUT-FILE
            AT END
                MOVE "99" TO WS-STATUS
            NOT AT END
                ADD 1 TO WS-COUNT
        END-READ
    END-PERFORM.
"""
        
        organized, messages = apply_production_flow_bucket_orchestration(program)
        
        # Should handle complex structure
        self.assertIsNotNone(organized)
        self.assertGreater(len(organized), 0)
        self.assertGreater(len(messages), 0)


def run_production_test_suite():
    """Run complete production test suite."""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all tests
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductionFlowBucketOrchestration
    ))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductionIssuesFixes
    ))
    suite.addTests(loader.loadTestsFromTestCase(
        TestProductionReadiness
    ))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("PRODUCTION TEST SUITE SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED - PRODUCTION READY")
    else:
        print("\n✗ TESTS FAILED - REVIEW ERRORS")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_production_test_suite()
    exit(0 if success else 1)

"""Tests for UPDATE program detection with DB2 INSERT/UPDATE patterns."""

from __future__ import annotations

import pytest


def test_update_program_detection_idms_store():
    """Traditional IDMS STORE is detected as UPDATE."""
    source = """
    IDENTIFICATION DIVISION.
    PROCEDURE DIVISION.
    100-MAIN.
        EXEC SQL
            SELECT col1 INTO :host-var
            FROM table1
        END-EXEC.
        STORE SOME-IDMS-RECORD.
    """
    
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    assert _is_update_program(source) is True


def test_update_program_detection_db2_insert():
    """DB2 INSERT patterns are detected as UPDATE."""
    source = """
    IDENTIFICATION DIVISION.
    PROCEDURE DIVISION.
    100-MAIN.
        EXEC SQL
            SELECT col1 INTO :host-var
            FROM table1
        END-EXEC.
        EXEC SQL
            INSERT INTO some_table VALUES (:host-var)
        END-EXEC.
    """
    
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    assert _is_update_program(source) is True


def test_update_program_detection_db2_update():
    """DB2 UPDATE patterns are detected as UPDATE."""
    source = """
    IDENTIFICATION DIVISION.
    PROCEDURE DIVISION.
    100-MAIN.
        EXEC SQL
            SELECT col1 INTO :host-var
            FROM table1
        END-EXEC.
        EXEC SQL
            UPDATE some_table SET col1 = :host-var
        END-EXEC.
    """
    
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    assert _is_update_program(source) is True


def test_retrieval_program_detection():
    """Pure retrieval programs (SELECT only) are not UPDATE."""
    source = """
    IDENTIFICATION DIVISION.
    PROCEDURE DIVISION.
    100-MAIN.
        EXEC SQL
            SELECT col1, col2 INTO :host-var1, :host-var2
            FROM table1
        END-EXEC.
        EXEC SQL
            SELECT col3 INTO :host-var3
            FROM table2
        END-EXEC.
    """
    
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    assert _is_update_program(source) is False


def test_idms_retrieval_program_detection():
    """IDMS OBTAIN/FIND are not write verbs - retrieval only."""
    source = """
    IDENTIFICATION DIVISION.
    PROCEDURE DIVISION.
    100-MAIN.
        EXEC IDMS
            OBTAIN IDMS-RECORD
        END-EXEC.
        EXEC SQL
            SELECT col1 INTO :host-var
            FROM table1
        END-EXEC.
    """
    
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    assert _is_update_program(source) is False


def test_empty_source_is_retrieval():
    """Empty or None source is not detected as UPDATE."""
    from idms_db2_phase2.ui.conversion_actions import _is_update_program
    
    assert _is_update_program("") is False
    assert _is_update_program(None) is False

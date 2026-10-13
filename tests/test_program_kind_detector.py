"""Regression tests for source-based program-kind detection.

The batch review path supplies one global kind of UNKNOWN. Kind is a
per-program fact, so the review must recover UPDATE vs RETRIEVAL from the
program text, otherwise UPDATE programs are reviewed as UNKNOWN and their
UPDATE-only checks are skipped.
"""

from __future__ import annotations

from review.engine.context import (
    KIND_RETRIEVAL,
    KIND_UNKNOWN,
    KIND_UPDATE,
)
from review.standards.program_kind_detector import detect_program_kind


def test_idms_write_verb_in_kept_comment_means_update() -> None:
    converted = "*DB2-KEEP   STORE VMBTL07-R01 WHERE ST-VMBEVEF."
    assert detect_program_kind(converted) == KIND_UPDATE


def test_idms_modify_verb_means_update() -> None:
    converted = "*DB2-KEEP   MODIFY VMBTL07-R01 WHERE MO-VMBEVEF."
    assert detect_program_kind(converted) == KIND_UPDATE


def test_exec_sql_insert_means_update() -> None:
    converted = "       EXEC SQL\n         INSERT INTO DZBEFFTV\n       END-EXEC."
    assert detect_program_kind(converted) == KIND_UPDATE


def test_cursor_declare_means_retrieval() -> None:
    converted = "       EXEC SQL\n         DECLARE C1 CURSOR FOR\n       END-EXEC."
    assert detect_program_kind(converted) == KIND_RETRIEVAL


def test_idms_obtain_means_retrieval() -> None:
    converted = "       OBTAIN CALC VMBFAS."
    assert detect_program_kind(converted) == KIND_RETRIEVAL


def test_write_intent_wins_over_a_read() -> None:
    converted = (
        "*=      OBTAIN VMBEFF\n"
        "*DB2-KEEP   MODIFY VMBTL07-R01 WHERE MO-VMBEVEF."
    )
    assert detect_program_kind(converted) == KIND_UPDATE


def test_store_paragraph_name_is_not_a_write() -> None:
    # STORE must be followed by a record to count; a paragraph header must not.
    converted = " 210-STORE-EFF.\n     MOVE A TO B."
    assert detect_program_kind(converted) == KIND_UNKNOWN


def test_display_literal_update_is_not_a_write() -> None:
    converted = "     DISPLAY ' ** VM1BD526 UPDATE CLE FORM **'."
    assert detect_program_kind(converted) == KIND_UNKNOWN


def test_explicit_usage_mode_in_source_wins() -> None:
    source = "       USAGE-MODE IS RETRIEVAL."
    converted = "*DB2-KEEP   STORE VMBTL07-R01 WHERE ST-VMBEVEF."
    assert detect_program_kind(converted, source) == KIND_RETRIEVAL


def test_no_evidence_is_unknown() -> None:
    assert detect_program_kind("     MOVE A TO B.") == KIND_UNKNOWN

def test_audit_host_variable_is_not_a_write() -> None:
    """TS-UPDATE-479BFAR must not make a retrieval cursor look like a write."""
    converted = (
        "       EXEC SQL\n"
        "         DECLARE C1 CURSOR FOR\n"
        "         SELECT TS_UPDATE_479BFAR\n"
        "           INTO :DCLDZBFARTV.TS-UPDATE-479BFAR\n"
        "       END-EXEC."
    )
    assert detect_program_kind(converted) == KIND_RETRIEVAL


def test_real_sql_update_is_still_a_write() -> None:
    converted = (
        "       EXEC SQL\n"
        "         UPDATE DZBFARTV\n"
        "            SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR\n"
        "       END-EXEC."
    )
    assert detect_program_kind(converted) == KIND_UPDATE


def test_audit_host_variable_is_not_a_write() -> None:
    """TS-UPDATE-479BFAR must not make a retrieval cursor look like a write."""
    converted = (
        "       EXEC SQL\n"
        "         DECLARE C1 CURSOR FOR\n"
        "         SELECT TS_UPDATE_479BFAR\n"
        "           INTO :DCLDZBFARTV.TS-UPDATE-479BFAR\n"
        "       END-EXEC."
    )
    assert detect_program_kind(converted) == KIND_RETRIEVAL


def test_real_sql_update_is_still_a_write() -> None:
    converted = (
        "       EXEC SQL\n"
        "         UPDATE DZBFARTV\n"
        "            SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR\n"
        "       END-EXEC."
    )
    assert detect_program_kind(converted) == KIND_UPDATE


def test_real_sql_insert_into_is_still_a_write() -> None:
    converted = (
        "       EXEC SQL\n"
        "         INSERT INTO DZ01RSTV (NM_ID_RS_PROGRAM)\n"
        "         VALUES (:DCLDZ01RSTV.NM-ID-RS-PROGRAM)\n"
        "       END-EXEC."
    )
    assert detect_program_kind(converted) == KIND_UPDATE
"""The batch review path must resolve kind PER PROGRAM.

The detector was correct and fully tested while review_file.py never called
it: one global --kind of UNKNOWN reached every ReviewContext, so every
UPDATE-only check was skipped on every program. These tests guard the CALL
SITE, not the detector.
"""

from __future__ import annotations

from pathlib import Path

from review.engine.context import KIND_RETRIEVAL, KIND_UNKNOWN, KIND_UPDATE
from review.runner.review_file import build_context, describe_kinds

UPDATE_CBL = (
    "       EXEC SQL\n"
    "         UPDATE DZBFARTV\n"
    "            SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR\n"
    "       END-EXEC.\n"
)
RETRIEVAL_CBL = (
    "       EXEC SQL\n"
    "         DECLARE C1 CURSOR FOR\n"
    "         SELECT NR_IDFMAS_479BFAR\n"
    "       END-EXEC.\n"
)
AUDIT_HOST_CBL = (
    "       EXEC SQL\n"
    "         DECLARE C1 CURSOR FOR\n"
    "         SELECT TS_UPDATE_479BFAR\n"
    "           INTO :DCLDZBFARTV.TS-UPDATE-479BFAR\n"
    "       END-EXEC.\n"
)


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_unknown_kind_is_detected_per_program(tmp_path: Path) -> None:
    ctx = build_context(_write(tmp_path, "U.cbl", UPDATE_CBL), KIND_UNKNOWN, "")
    assert ctx.program_kind == KIND_UPDATE
    assert ctx.is_update is True


def test_two_files_in_one_run_get_different_kinds(tmp_path: Path) -> None:
    """The defect: one global kind was applied to a whole folder."""
    upd = build_context(_write(tmp_path, "U.cbl", UPDATE_CBL), KIND_UNKNOWN, "")
    ret = build_context(_write(tmp_path, "R.cbl", RETRIEVAL_CBL), KIND_UNKNOWN, "")
    assert upd.program_kind == KIND_UPDATE
    assert ret.program_kind == KIND_RETRIEVAL


def test_explicit_kind_overrides_detection(tmp_path: Path) -> None:
    ctx = build_context(_write(tmp_path, "U.cbl", UPDATE_CBL), KIND_RETRIEVAL, "")
    assert ctx.program_kind == KIND_RETRIEVAL


def test_audit_host_variable_does_not_look_like_a_write(tmp_path: Path) -> None:
    """TS-UPDATE-479BFAR must not promote a cursor to UPDATE."""
    ctx = build_context(_write(tmp_path, "A.cbl", AUDIT_HOST_CBL), KIND_UNKNOWN, "")
    assert ctx.program_kind == KIND_RETRIEVAL


def test_no_evidence_stays_unknown(tmp_path: Path) -> None:
    ctx = build_context(_write(tmp_path, "X.cbl", "       MOVE A TO B.\n"), KIND_UNKNOWN, "")
    assert ctx.program_kind == KIND_UNKNOWN


def test_banner_summary_reports_each_kind(tmp_path: Path) -> None:
    contexts = [
        build_context(_write(tmp_path, "U.cbl", UPDATE_CBL), KIND_UNKNOWN, ""),
        build_context(_write(tmp_path, "R.cbl", RETRIEVAL_CBL), KIND_UNKNOWN, ""),
    ]
    summary = describe_kinds(contexts)
    assert KIND_UPDATE in summary
    assert KIND_RETRIEVAL in summary


def test_banner_summary_for_one_file_is_just_the_kind(tmp_path: Path) -> None:
    contexts = [build_context(_write(tmp_path, "U.cbl", UPDATE_CBL), KIND_UNKNOWN, "")]
    assert describe_kinds(contexts) == KIND_UPDATE
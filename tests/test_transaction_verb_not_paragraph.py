"""A bare transaction verb must not be read as an Area-A paragraph.

ROLLBACK and COMMIT can appear as single-word, period-terminated
statements after IDMS-to-DB2 conversion. The procedure indent
normalizer must keep them in Area B, not promote them to paragraph
headers (which produced CHK-06.06 failures).
"""

from __future__ import annotations

from rules.procedure_indent_rules import NON_PARAGRAPH_SINGLE_WORDS
from idms_db2_phase2.composers.procedure_indent_normalizer import (
    ProcedureIndentNormalizer,
)


def test_rollback_and_commit_are_exempt_single_words() -> None:
    assert "ROLLBACK" in NON_PARAGRAPH_SINGLE_WORDS
    assert "COMMIT" in NON_PARAGRAPH_SINGLE_WORDS


def test_rollback_is_not_area_a_header() -> None:
    assert ProcedureIndentNormalizer._is_area_a_header("ROLLBACK.") is False


def test_commit_is_not_area_a_header() -> None:
    assert ProcedureIndentNormalizer._is_area_a_header("COMMIT.") is False


def test_real_paragraph_still_reads_as_header() -> None:
    assert ProcedureIndentNormalizer._is_area_a_header("IDMS-STOP.") is True

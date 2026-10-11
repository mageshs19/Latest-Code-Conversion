from __future__ import annotations

from converter.composers.procedure_indent.indent_models import (
    LineClassifier,
)
from rules.procedure_indent_rules import NON_PARAGRAPH_SINGLE_WORDS


def test_rollback_and_commit_are_exempt_single_words() -> None:
    assert "ROLLBACK" in NON_PARAGRAPH_SINGLE_WORDS
    assert "COMMIT" in NON_PARAGRAPH_SINGLE_WORDS


def test_rollback_is_not_area_a_header() -> None:
    assert LineClassifier.is_area_a_header("ROLLBACK.") is False


def test_commit_is_not_area_a_header() -> None:
    assert LineClassifier.is_area_a_header("COMMIT.") is False


def test_real_paragraph_still_reads_as_header() -> None:
    assert LineClassifier.is_area_a_header("IDMS-STOP.") is True
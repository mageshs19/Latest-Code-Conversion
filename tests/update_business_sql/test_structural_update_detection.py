# LOCATION: tests/update_business_sql/test_structural_update_detection.py
# ACTION: REPLACE ENTIRE FILE
"""The inline UPDATE is found by its shape, not by a comment.

VMDZ1526 carried a SQL-LOCATION anchor and was extracted. VMDZ1567
carried neither anchor, so its UPDATE stayed inline, got no
ADD 1 TO counter, and produced no end-of-run total.

UpdateSqlBlockExtractor is a MIXIN - it borrows line rendering from its
host. The host here supplies only _logical, which is all the detection
methods touch.
"""

from __future__ import annotations

import pytest

from converter.postprocess.update_business_sql.update_sql_block_extractor import (
    UpdateSqlBlockExtractor,
)


class _Host(UpdateSqlBlockExtractor):
    """Smallest host that satisfies the mixin's detection path."""

    @staticmethod
    def _logical(line):
        return " ".join(str(line or "").split())

    @staticmethod
    def _is_comment_line(line):
        return str(line or "").lstrip().startswith("*")


@pytest.fixture
def extractor() -> _Host:
    return _Host()


BLOCK = [
    "VERWERKING.",
    "    INITIALIZE DCLDZBFARTV",
    "    MOVE '1815' TO CT-A OF DCLDZBFARTV",
    "    EXEC SQL",
    "      UPDATE DZBFARTV",
    "        SET DA_X = :DCLDZBFARTV.DA-X",
    "      WHERE CT_A = :DCLDZBFARTV.CT-A",
    "    END-EXEC",
    "    EVALUATE SQLCODE",
    "      WHEN 0",
    "        CONTINUE",
    "      WHEN OTHER",
    "        PERFORM SQLERROR",
    "    END-EVALUATE",
    "    .",
]


def test_a_block_without_any_anchor_is_still_found(extractor):
    found = extractor._find_inline_update_block(
        lines=BLOCK, start=0, end=len(BLOCK)
    )
    assert found is not None
    _start, _end, record, group = found
    assert group == "DCLDZBFARTV"
    assert record == "DZBFAR"


def test_the_structural_find_is_reported(extractor):
    notes: list[str] = []
    extractor._find_inline_update_block(
        lines=BLOCK, start=0, end=len(BLOCK),
        diagnostics=notes, paragraph="VERWERKING",
    )
    assert any("block structure" in n for n in notes)


def test_a_paragraph_with_no_update_is_refused_out_loud(extractor):
    notes: list[str] = []
    lines = ["VERWERKING.", "    MOVE A TO B", "    ."]
    assert extractor._find_inline_update_block(
        lines=lines, start=0, end=len(lines),
        diagnostics=notes, paragraph="VERWERKING",
    ) is None
    assert any("no inline business UPDATE" in n for n in notes)


def test_the_marker_anchor_still_wins(extractor):
    lines = ["VERWERKING.", "*DB2: Converted MODIFY for VMBFAR"] + BLOCK[1:]
    _s, _e, record, _g = extractor._find_inline_update_block(
        lines=lines, start=0, end=len(lines)
    )
    assert record == "VMBFAR"
"""Regression tests for qualifier-connector aware line wrapping.

A fixed-format body wrap must never leave a qualifier connector (OF / IN)
dangling at the end of a fragment. When it did, the trailing qualifier landed
alone on the continuation line as "NAME.", which a later indentation pass
misread as an Area-A paragraph header, corrupting the program structure and
producing an invalid "... OF." statement that the compiler rejects.
"""

from __future__ import annotations

from converter.composers.fixed_format_wrapper import FixedFormatWrapper
from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
    glue_qualifier_connectors,
)
from patterns.procedure_indent_patterns import PARAGRAPH_HEADER_PATTERN

INDENT = "     "


def _wrap(stmt: str) -> list[str]:
    return FixedFormatWrapper().wrap_by_words(INDENT + stmt, INDENT + " ")


def test_connector_glue_keeps_of_with_following_name() -> None:
    words = ["TO", "DA-UBSECIS-479BEFF", "OF", "DCLDZBEFFTV."]
    assert glue_qualifier_connectors(words) == [
        "TO",
        "DA-UBSECIS-479BEFF",
        "OF DCLDZBEFFTV.",
    ]


def test_trailing_connector_without_following_name_is_untouched() -> None:
    assert glue_qualifier_connectors(["FOO", "OF"]) == ["FOO", "OF"]


def test_no_fragment_ends_with_a_dangling_connector() -> None:
    stmt = (
        "MOVE DA-UB-FORM-AS OF VMDZ205I "
        "TO DA-UBSECIS-479BEFF OF DCLDZBEFFTV."
    )
    for line in _wrap(stmt):
        assert not line.strip().upper().endswith(" OF")
        assert not line.strip().upper().endswith(" IN")


def test_continuation_fragment_is_not_mistaken_for_a_paragraph() -> None:
    stmt = (
        "MOVE DA-UB-FORM-AS OF VMDZ205I "
        "TO DA-UBSECIS-479BEFF OF DCLDZBEFFTV."
    )
    for line in _wrap(stmt):
        assert not PARAGRAPH_HEADER_PATTERN.match(line.strip().upper())


def test_multi_receiver_move_wraps_cleanly() -> None:
    stmt = (
        "MOVE 0 TO NR-IDISSUE-479BEFF OF DCLDZBEFFTV "
        "NR-CDISSUE-479BEFF OF DCLDZBEFFTV."
    )
    lines = _wrap(stmt)
    for line in lines:
        assert not line.strip().upper().endswith(" OF")
        assert not PARAGRAPH_HEADER_PATTERN.match(line.strip().upper())


def test_service_wrap_body_lines_also_glues_connectors() -> None:
    body = (
        "     MOVE DA-UB-FORM-AS OF VMDZ205I "
        "TO DA-UBSECIS-479BEFF OF DCLDZBEFFTV."
    )
    lines = FixedFormatLineService().wrap_body_lines(
        body, continuation_indent="      ", max_lines=3
    )
    assert lines
    for line in lines:
        assert not line.strip().upper().endswith(" OF")
        assert not PARAGRAPH_HEADER_PATTERN.match(line.strip().upper())

# LOCATION: tests/restart/test_m10d_line_utils.py
# ACTION: REPLACE ENTIRE FILE
"""M10d - RestartLineUtils.

CORRECTION 1 - the blank fixture was not a real line

BLANK was "000120", six characters. is_fixed() needs more than seven,
so the service read it as FREE-FORM and returned it whole. A real
fixed-format blank line is padded to 80 columns. The fixture is now
realistic, and the stray-sequence case it accidentally exposed is
tested on its own.

CORRECTION 2 - agreement was asserted on the WRONG thing

The suite's conftest stand-in and this adapter were required to return
the SAME string. They need not. The contract every restart module uses
is

    if not logical or is_comment(logical):   # skip

which has TWO legal routes: return "", or return a body is_comment()
recognises. Asserting equality forbade one of them. Agreement is now
asserted on SKIPPABILITY, which is what the callers depend on.

If a skippability test fails on the line_utils side, the conftest
fixture is letting comment lines through as code - a defect in the
fixture, not in this adapter.
"""

from __future__ import annotations

import pytest

from converter.composers.restart.restart_line_utils import RestartLineUtils

BODY_WIDTH = 65
RIGHT_WIDTH = 8


def _fixed(sequence: str, body: str, indicator: str = " ") -> str:
    """One realistic 80-column record."""
    right = f"{sequence}00"[:RIGHT_WIDTH].ljust(RIGHT_WIDTH, "0")
    return f"{sequence}{indicator}{body.ljust(BODY_WIDTH)}{right}"


CODE = _fixed("000100", "    MOVE A TO B.")
COMMENT = _fixed("000110", "   THIS IS A COMMENT", indicator="*")
BLANK = _fixed("000120", "")
FREE_FORM = "           MOVE A TO B."
SEQUENCE_ONLY = "000130"
SEQUENCE_ARTIFACT = "001690/."


@pytest.fixture
def utils():
    return RestartLineUtils()


def _is_skipped(line_tool, raw: str) -> bool:
    """The contract every restart module applies, in one place."""
    body = str(line_tool.logical(raw) or "").strip()
    return (not body) or bool(line_tool.is_comment(body))


#
# Contract
#
def test_a_code_line_yields_its_body(utils):
    assert utils.logical(CODE) == "MOVE A TO B."


def test_free_form_text_is_still_read(utils):
    assert utils.logical(FREE_FORM) == "MOVE A TO B."


def test_a_comment_line_yields_nothing(utils):
    """The asterisk lives in column 7 and never reaches the body."""
    assert utils.logical(COMMENT) == ""


def test_a_blank_line_yields_nothing(utils):
    assert utils.logical(BLANK) == ""


@pytest.mark.parametrize("raw", [SEQUENCE_ONLY, SEQUENCE_ARTIFACT])
def test_a_stray_sequence_area_yields_nothing(utils, raw):
    """001690. matches the paragraph-header shape; digits are legal."""
    assert utils.logical(raw) == ""


def test_a_numeric_paragraph_name_survives(utils):
    """Only a SIX digit run is a sequence area."""
    assert utils.logical(_fixed("000140", "1000-MAIN.")) == "1000-MAIN."
    assert utils.logical(_fixed("000150", "0100.")) == "0100."


@pytest.mark.parametrize("marker", ["*", "/"])
def test_marked_text_is_a_comment(utils, marker):
    assert utils.is_comment(f"{marker} anything") is True


def test_ordinary_text_is_not_a_comment(utils):
    assert utils.is_comment("MOVE A TO B.") is False


def test_split_and_join_round_trip(utils):
    text = "ONE\nTWO\nTHREE"
    assert utils.join(utils.lines(text)) == text


#
# Refusal
#
def test_an_unusable_service_is_refused_at_construction():
    """A wiring error must name the wiring, not a line three passes on."""
    with pytest.raises(TypeError) as error:
        RestartLineUtils(object())
    assert "logical" in str(error.value)


#
# Agreement with the suite's stand-in - on SKIPPABILITY, not on text
#
@pytest.mark.parametrize("raw", [COMMENT, BLANK, SEQUENCE_ONLY])
def test_both_implementations_skip_non_code(utils, line_utils, raw):
    assert _is_skipped(utils, raw) is True
    assert _is_skipped(line_utils, raw) is True


@pytest.mark.parametrize("raw", [CODE, FREE_FORM])
def test_both_implementations_keep_code(utils, line_utils, raw):
    assert _is_skipped(utils, raw) is False
    assert _is_skipped(line_utils, raw) is False
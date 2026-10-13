"""The body never extends past column 72.

A record off by one character kept its own sequence area as COBOL text,
the wrapper collapsed the whitespace between them, and the composer
emitted

    002340     STOP RUN. 02350000                           02340000

a complete statement followed by a stray numeric literal. 374 of them
across six generated programs, from one slice boundary.
"""

from __future__ import annotations

import re

from converter.composers.fixed_format_composer import FixedFormatComposer
from converter.composers.fixed_format_line_parser import FixedFormatLineParser

STATEMENT = "    STOP RUN."
SEQUENCE = "02350000"
STRANDED = re.compile(r"\s\d{8}\s*$")


def _record(body: str = STATEMENT, right: str = SEQUENCE) -> str:
    return "002340" + " " + body.ljust(65) + right


def _bodies(text: str) -> list[str]:
    return [line[7:72] for line in text.splitlines() if len(line) >= 72]


#
# The parser
#
def test_a_full_record_separates_the_sequence():
    parsed = FixedFormatLineParser().parse_line(_record())
    assert parsed["body"] == STATEMENT
    assert parsed["right_sequence"] == SEQUENCE


def test_a_record_one_character_short_still_stops_at_column_72():
    """CORRECTION 4. This returned a 72-character body carrying 0235000."""
    parsed = FixedFormatLineParser().parse_line(_record()[:79])
    assert parsed["body"] == STATEMENT
    assert SEQUENCE[:-1] not in str(parsed["body"])


def test_a_record_longer_than_80_still_stops_at_column_72():
    parsed = FixedFormatLineParser().parse_line(_record() + "   ")
    assert parsed["body"] == STATEMENT


def test_a_blank_sequence_area_yields_no_right_sequence():
    parsed = FixedFormatLineParser().parse_line(_record(right=" " * 8))
    assert parsed["body"] == STATEMENT
    assert parsed["right_sequence"] == ""


#
# The composer
#
def test_no_body_carries_a_stranded_sequence():
    source = "\n".join([_record(), _record()[:79], _record() + "  "]) + "\n"
    out = FixedFormatComposer().format(source)

    offenders = [body for body in _bodies(out) if STRANDED.search(body)]
    assert not offenders, offenders


def test_formatting_twice_is_idempotent():
    """The pass runs more than once per program. The second run must be
    a no-op; while the body ran past column 72 it was not."""
    composer = FixedFormatComposer()
    once = composer.format("\n".join([_record(), _record()[:79]]) + "\n")
    twice = FixedFormatComposer().format(once)
    assert twice == once


def test_every_emitted_record_is_80_columns():
    out = FixedFormatComposer().format(_record()[:79] + "\n")
    for line in out.splitlines():
        if line:
            assert len(line) == 80, repr(line)
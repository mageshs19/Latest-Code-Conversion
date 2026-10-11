# LOCATION: tests/restart/conftest.py
# ACTION: REPLACE ENTIRE FILE
"""Shared fixtures for the restart module tests."""

from __future__ import annotations

import pytest

from catalogs.restart_paragraph_catalog import production_restart_role
from converter.generators.restart.restart_config import (
    RestartConfig,
    RestartProgramNames,
)

SEQ = 6
IND = 7
BODY_END = 72

# Column 7 characters that mark a FIXED-FORMAT line. '-' is deliberately
# absent: 810000-CALL-USERABEN. carries a hyphen in column 7 and is a
# PARAGRAPH NAME, not a sequence area plus a continuation indicator.
INDICATORS = (" ", "*", "/", "D", "d")

# Indicator characters whose line is not code at all.
COMMENT_INDICATORS = ("*", "/")


class FixedFormatLineUtils:
    """Minimal stand-in for the shared retrieval line utility.

    CORRECTION 1 - a fixed-format comment was returned as CODE

    logical() sliced text[IND:BODY_END], which discards column 7 - and
    with it the asterisk that made the line a comment. is_comment() then
    inspected a body carrying no marker and answered False, so every
    fixed-format comment in this suite was read as a statement.

    The defect survived because the one test that claimed to cover it,
    test_m3_name_resolver::test_comment_lines_are_ignored, inserted its
    comment at index 0 - before PROCEDURE DIVISION, where the resolver
    never looks. It passed on line POSITION, not on comment handling.

    A comment now collapses to "", matching
    converter/composers/restart/restart_line_utils.py, which is what
    production uses. Both routes the callers accept stay valid:

        if not logical or is_comment(logical):   # skip

    CORRECTION 2 - a stray sequence area was returned as a statement

    "000130" is shorter than the slice guard, so it came back whole, and
    "001690." matches the paragraph-header shape exactly - digits are
    legal in a COBOL name. Either would have invented a paragraph and
    cut every span at it. Only an exact SEQ-digit run is treated as a
    sequence area, so a longer or shorter numeric name survives.
    """

    @staticmethod
    def logical(line: str) -> str:
        text = str(line or "").rstrip("\n")

        if (
            len(text) > IND
            and text[:SEQ].isdigit()
            and text[SEQ] in INDICATORS
        ):
            if text[SEQ] in COMMENT_INDICATORS:
                return ""
            text = text[IND:BODY_END]

        body = text.strip()
        return "" if FixedFormatLineUtils._is_sequence_only(body) else body

    @staticmethod
    def is_comment(line: str) -> bool:
        return str(line or "").lstrip().startswith(COMMENT_INDICATORS)

    @staticmethod
    def _is_sequence_only(body: str) -> bool:
        """Exactly SEQ digits, with an optional period, is not COBOL."""
        candidate = str(body or "").strip()
        if candidate.endswith("."):
            candidate = candidate[:-1]
        return len(candidate) == SEQ and candidate.isdigit()


@pytest.fixture
def line_utils():
    return FixedFormatLineUtils()


@pytest.fixture
def role():
    return production_restart_role()


@pytest.fixture
def complete_names():
    return RestartProgramNames(
        program_constant="CS-PROGRAM",
        run_date_field="DA-DD-MM-CCYY",
        file_name="OPERATIES",
        record_name="VMDZ205I",
        read_paragraph="READ-FLAT-FILE",
        process_paragraph="VERWERKING",
        eof_condition="VMDZ205I-EOF",
        not_eof_condition="VMDZ205I-NOT-EOF",
        input_counter="WS-NB-INPUT-UPD-I",
        commit_counter="WS-TELLER",
        input_save_area="WS-INPUT-KASBONS",
        restart_record="WS-RESTART-REC",
        restart_key_field="KY-RESTART",
        read_count_field="NB-READ",
        read_count_size=15,
        restart_key_size=1200,
        error_paragraph="SQLERROR",
        abend_module="USERABEN",
    )


@pytest.fixture
def config(role, complete_names):
    return RestartConfig.build(role, complete_names)


@pytest.fixture
def source_lines():
    """A minimal update program in fixed format."""
    return [
        "000100 DATA DIVISION.",
        "000110 FILE SECTION.",
        "000120 FD   OPERATIES",
        "000130      RECORD CONTAINS 1200 CHARACTERS.",
        "000140 01   OPERATIES-REC             PIC X(1200).",
        "000150 WORKING-STORAGE SECTION.",
        "000160 77  USERABEN                   PIC X(8).",
        "000170 01  WS-SWITCHES.",
        "000180     02  SW-VMDZ205I            PIC X.",
        "000190         88  VMDZ205I-NOT-EOF   VALUE 'N'.",
        "000200         88  VMDZ205I-EOF       VALUE 'Y'.",
        "000210 01  HELP-VARIABLE.",
        "000220     02  WS-RESTART-REC.",
        "000230         03  NB-READ            PIC 9(15).",
        "000240         03  KY-RESTART         PIC X(1200).",
        "000250     02  WS-INPUT-KASBONS       PIC X(1200).",
        "000260     02  WS-TELLER              PIC 9(9) COMP-3.",
        "000270     02  WS-NB-INPUT-UPD-I      PIC 9(7) COMP-3.",
        "000280 01  WS-DB2-GENERATED.",
        "000290     10  CS-PROGRAM             PIC X(8).",
        "000300 01  WS-DATUMVELDEN.",
        "000310     03  DA-DD-MM-CCYY          PIC X(10).",
        "000320      EXEC SQL",
        "000330           INCLUDE SQLERROR",
        "000340      END-EXEC.",
        "000350 PROCEDURE DIVISION.",
        "000360     OPEN INPUT OPERATIES.",
        "000370     PERFORM 700-RESTART-CONTROL.",
        "000380     PERFORM READ-FLAT-FILE.",
        "000390     PERFORM VERWERKING UNTIL VMDZ205I-EOF.",
        "000400     CLOSE OPERATIES.",
        "000410     STOP RUN.",
        "000420 VERWERKING.",
        "000430     CONTINUE.",
        "000440 READ-FLAT-FILE.",
        "000450     READ OPERATIES INTO VMDZ205I",
        "000460          AT END SET VMDZ205I-EOF TO TRUE.",
    ]
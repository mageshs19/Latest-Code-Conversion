# LOCATION: tests/restart/test_m3_name_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""M3 contract tests: the resolver reads names, or refuses.

The defect this module exists to prevent: the previous resolver returned
an invented literal when it could not find a name, so the generator
performed a paragraph that was never declared and moved to a field that
was never defined. The checkpoint payload length was invented the same
way - a constant 1215 that happened to match one program's layout.

CORRECTION - a fixture line was located by its sequence number

The infrastructure test read

    lines.index("000360     PERFORM VERWERKING UNTIL VMDZ205I-EOF.")

Adding three INCLUDE lines to the fixture renumbered that statement to
000390 and the test died with ValueError before asserting anything. A
test must not depend on where a fixture line happens to sit; the anchor
is now found by content.
"""

from __future__ import annotations

import pytest

from converter.generators.restart.restart_name_resolver import (
    RestartNameResolver,
)

PROCESS_LOOP_MARKER = "PERFORM VERWERKING UNTIL"


@pytest.fixture
def resolve(line_utils):
    def _resolve(lines):
        return RestartNameResolver(line_utils).resolve(lines)

    return _resolve


def _index_of(lines: list[str], marker: str) -> int:
    """Position of the first line containing the marker.

    Content, never a sequence number: the fixture may be renumbered.
    """
    return next(i for i, line in enumerate(lines) if marker in line)


# ---------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------

def test_a_complete_program_resolves_every_name(resolve, source_lines):
    names, report = resolve(source_lines)
    assert names.is_complete() is True
    assert report.refused == []


def test_file_and_record_come_from_the_read_statement(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.file_name == "OPERATIES"
    assert names.record_name == "VMDZ205I"


def test_eof_conditions_come_from_the_88_levels(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.eof_condition == "VMDZ205I-EOF"
    assert names.not_eof_condition == "VMDZ205I-NOT-EOF"


def test_the_reader_paragraph_is_found(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.read_paragraph == "READ-FLAT-FILE"


def test_the_business_paragraph_is_found(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.process_paragraph == "VERWERKING"


def test_working_storage_names_are_resolved(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.input_counter == "WS-NB-INPUT-UPD-I"
    assert names.commit_counter == "WS-TELLER"
    assert names.input_save_area == "WS-INPUT-KASBONS"
    assert names.restart_record == "WS-RESTART-REC"
    assert names.restart_key_field == "KY-RESTART"
    assert names.read_count_field == "NB-READ"
    assert names.program_constant == "CS-PROGRAM"
    assert names.run_date_field == "DA-DD-MM-CCYY"
    assert names.abend_module == "USERABEN"


# ---------------------------------------------------------------------
# Measurement, not assumption
# ---------------------------------------------------------------------

def test_the_payload_sizes_are_read_from_the_pictures(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.read_count_size == 15
    assert names.restart_key_size == 1200


def test_a_different_layout_produces_a_different_length(
    resolve, source_lines
):
    """1215 was never a constant; it is this program's measurement."""
    lines = [
        line.replace("PIC X(1200)", "PIC X(0800)")
        if "KY-RESTART" in line
        else line
        for line in source_lines
    ]
    names, _report = resolve(lines)
    assert names.restart_key_size == 800
    assert names.read_count_size == 15


def test_an_undeclared_payload_field_is_refused(resolve, source_lines):
    lines = [line for line in source_lines if "KY-RESTART" not in line]
    names, report = resolve(lines)
    assert names.restart_key_field == ""
    assert names.restart_key_size == 0
    assert "restart_key_field" in report.refused
    assert "restart_key_size" in report.refused


def test_a_group_item_is_named_but_not_measured(resolve, source_lines):
    """WS-RESTART-REC is a group; it has no picture to measure."""
    names, _report = resolve(source_lines)
    assert names.restart_record == "WS-RESTART-REC"


def test_a_comp_3_counter_is_measured_by_its_digits(resolve, source_lines):
    """Usage is not length. PIC 9(15) is fifteen digits either way."""
    lines = [
        line.replace("PIC 9(15)", "PIC 9(15) COMP-3")
        if "NB-READ" in line
        else line
        for line in source_lines
    ]
    names, _report = resolve(lines)
    assert names.read_count_size == 15


# ---------------------------------------------------------------------
# Infrastructure must never be mistaken for business logic
# ---------------------------------------------------------------------

def test_an_infrastructure_paragraph_is_never_chosen_as_business(
    resolve, source_lines
):
    lines = list(source_lines)
    anchor = _index_of(lines, PROCESS_LOOP_MARKER)
    lines.insert(
        anchor,
        "000385     PERFORM 800-PROCESS-COMMIT UNTIL VMDZ205I-EOF.",
    )
    names, _report = resolve(lines)
    assert names.process_paragraph == "VERWERKING"


@pytest.mark.parametrize(
    "paragraph",
    [
        "600-GET-TIMESTAMP",
        "700-RESTART-CONTROL",
        "710-JOB-IS-RESTART",
        "720-WRITE-RESTART-REC",
        "800-PROCESS-COMMIT",
        "810-JOB-IS-RESTART",
        "820-WRITE-RESTART-REC",
        "830-PROCESS-COMMIT",
        "810000-CALL-USERABEN",
    ],
)
def test_every_numbering_scheme_is_treated_as_infrastructure(paragraph):
    assert RestartNameResolver._is_infrastructure(paragraph) is True


def test_a_business_paragraph_is_not_infrastructure():
    assert RestartNameResolver._is_infrastructure("VERWERKING") is False
    assert RestartNameResolver._is_infrastructure("HOOFDVERWERKING") is False


def test_a_loop_on_the_wrong_condition_is_rejected(resolve, source_lines):
    lines = [
        line.replace("UNTIL VMDZ205I-EOF", "UNTIL SW-OTHER-EOC")
        for line in source_lines
    ]
    names, _report = resolve(lines)
    assert names.process_paragraph == ""
    assert "process_paragraph" in names.missing()


# ---------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------

def test_an_undeclared_default_is_never_emitted(resolve, source_lines):
    lines = [line for line in source_lines if "WS-TELLER" not in line]
    names, report = resolve(lines)
    assert names.commit_counter == ""
    assert "commit_counter" in report.refused


def test_a_refusal_is_reported_with_a_reason(resolve, source_lines):
    lines = [line for line in source_lines if "WS-INPUT-KASBONS" not in line]
    _names, report = resolve(lines)
    assert any(
        "input_save_area unresolved" in message for message in report.messages
    )
    assert any("refused to invent" in message for message in report.messages)


def test_an_empty_program_refuses_everything(resolve):
    names, report = resolve([])
    assert names.is_complete() is False
    assert len(report.refused) == len(names.REQUIRED)
    assert report.resolved == {}


def test_a_program_with_no_procedure_division_refuses_paragraphs(resolve):
    lines = [
        "000100 DATA DIVISION.",
        "000110 WORKING-STORAGE SECTION.",
        "000120 01  WS-TELLER                PIC 9(9) COMP-3.",
    ]
    names, _report = resolve(lines)
    assert names.read_paragraph == ""
    assert names.process_paragraph == ""


# ---------------------------------------------------------------------
# The SQL error paragraph is include-driven
# ---------------------------------------------------------------------

def test_the_error_paragraph_requires_its_include(resolve, source_lines):
    names, _report = resolve(source_lines)
    assert names.error_paragraph == "SQLERROR"


def test_a_missing_include_refuses_the_error_paragraph(resolve, source_lines):
    lines = [line for line in source_lines if "INCLUDE SQLERROR" not in line]
    names, report = resolve(lines)
    assert names.error_paragraph == ""
    assert "error_paragraph" in report.refused


def test_the_one_line_include_form_is_accepted(resolve):
    lines = [
        "000100 DATA DIVISION.",
        "000110 WORKING-STORAGE SECTION.",
        "000120      EXEC SQL INCLUDE SQLERROR END-EXEC.",
        "000130 PROCEDURE DIVISION.",
        "000140     STOP RUN.",
    ]
    names, _report = resolve(lines)
    assert names.error_paragraph == "SQLERROR"


def test_another_include_does_not_satisfy_the_error_paragraph(resolve):
    lines = [
        "000100 DATA DIVISION.",
        "000110 WORKING-STORAGE SECTION.",
        "000120      EXEC SQL INCLUDE SQLCA END-EXEC.",
        "000130      EXEC SQL INCLUDE SQLERRWS END-EXEC.",
        "000140 PROCEDURE DIVISION.",
        "000150     STOP RUN.",
    ]
    names, _report = resolve(lines)
    assert names.error_paragraph == ""


# ---------------------------------------------------------------------
# Line handling
# ---------------------------------------------------------------------

def test_comment_lines_are_ignored(resolve, source_lines):
    """The comment must sit where the resolver actually LOOKS.

    Inserted at index 0 this test passed on line position: the resolver
    scans the procedure region only, so a line before PROCEDURE DIVISION
    was never consulted and the comment handling was never exercised.
    """
    lines = list(source_lines)
    anchor = _index_of(lines, PROCESS_LOOP_MARKER)
    lines.insert(
        anchor,
        "000095* PERFORM FAKE-PARAGRAPH UNTIL VMDZ205I-EOF.",
    )
    names, _report = resolve(lines)
    assert names.process_paragraph == "VERWERKING"

def test_the_sequence_area_never_leaks_into_a_name(resolve, source_lines):
    names, _report = resolve(source_lines)
    for value in (
        names.file_name,
        names.record_name,
        names.process_paragraph,
        names.read_paragraph,
    ):
        assert not value[:1].isdigit()


def test_free_format_input_is_accepted(resolve):
    lines = [
        "DATA DIVISION.",
        "FILE SECTION.",
        "FD OPERATIES.",
        "WORKING-STORAGE SECTION.",
        "01 WS-SWITCHES.",
        "   02 SW-IN PIC X.",
        "      88 VMDZ205I-NOT-EOF VALUE 'N'.",
        "      88 VMDZ205I-EOF     VALUE 'Y'.",
        "PROCEDURE DIVISION.",
        "    PERFORM VERWERKING UNTIL VMDZ205I-EOF.",
        "VERWERKING.",
        "    CONTINUE.",
        "READ-FLAT-FILE.",
        "    READ OPERATIES INTO VMDZ205I AT END CONTINUE.",
    ]
    names, _report = resolve(lines)
    assert names.file_name == "OPERATIES"
    assert names.record_name == "VMDZ205I"
    assert names.process_paragraph == "VERWERKING"


# ---------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------

def test_resolution_is_repeatable(resolve, source_lines):
    first, _r1 = resolve(source_lines)
    second, _r2 = resolve(source_lines)
    assert first == second


def test_the_report_lists_every_resolved_name(resolve, source_lines):
    names, report = resolve(source_lines)
    for key in names.REQUIRED:
        assert key in report.resolved


def test_eighteen_entries_are_required():
    """Sixteen names plus two measurements."""
    from converter.generators.restart.restart_config import (
        RestartProgramNames,
    )

    assert len(RestartProgramNames.REQUIRED) == 18
    assert len(set(RestartProgramNames.REQUIRED)) == 18
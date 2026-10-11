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

CORRECTION - "declared or refused" was the wrong axis

Four tests here asserted that ANY undeclared name is refused. That is
right for a name the PROGRAM owns and wrong for a name this GENERATOR
owns. Seven working-storage fields, two picture sizes and the EOF pair
are created by RestartStorageInjector; requiring them to be declared
first meant they resolved empty, RestartConfig became unusable, and
RestartInjectionComposer refused BEFORE the injector that declares them
ever ran.

The axis is OWNERSHIP, not declaration:

    PROGRAM-owned    read from the source, refused when absent
    GENERATOR-owned  measured when declared, otherwise SUPPLIED from
                     catalogs/restart_storage_catalog.py and reported
                     in ResolutionReport.defaulted

Each retargeted test below still asserts a refusal - against a name the
program genuinely owns - so nothing stopped being guarded.

CORRECTION - the promise test was declared twice

test_every_supplied_name_is_actually_declared existed twice: once over a
filtered `source_lines` and once over BARE_PROGRAM. Python keeps the
second and silently discards the first, so half the file read as live
code that pytest never collected. The filtered version was also the
wrong fixture - see below.

THE RISK THE OWNERSHIP SPLIT OPENS, AND THE TESTS THAT CLOSE IT

Supplying a name is a PROMISE that M5 will declare it. If the two ever
disagree the generated family references an undeclared field, which is
exactly the defect the legacy generator shipped as

    ADD 1 TO WS-COMMIT-COUNTER      <- never declared

test_every_supplied_name_is_actually_declared asserts the promise on
BARE_PROGRAM, which is the shape the pipeline actually produces: a
converted program carrying none of the restart storage.

The first attempt derived its fixture by FILTERING source_lines. That
removed the group MEMBERS but left the group HEADERS, and the injector
is group-level idempotent - it saw "01 HELP-VARIABLE." already present,
reported "already declared", and added nothing. The test failed against
a state the pipeline never produces.

That near-miss is a real latent defect in its own right, so it is
recorded as test_a_partial_group_is_completed, marked xfail(strict).
When the injector becomes field-aware the marker must be removed, and
strict=True forces that rather than letting it rot.
"""

from __future__ import annotations

import pytest

from catalogs.restart_storage_catalog import GENERATED_STORAGE_FIELDS
from converter.composers.restart.restart_storage_injector import (
    RestartStorageInjector,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_name_resolver import (
    RestartNameResolver,
)

PROCESS_LOOP_MARKER = "PERFORM VERWERKING UNTIL"

# The roles this generator creates. Everything else belongs to the
# program and is refused when absent.
GENERATOR_OWNED = set(GENERATED_STORAGE_FIELDS) | {
    "read_count_size",
    "restart_key_size",
    "eof_condition",
    "not_eof_condition",
}

# A program carrying NONE of the restart working storage. This is what
# the pipeline hands the injector: a converted IDMS program whose
# checkpoint record has been removed and whose restart groups do not
# exist yet.
BARE_PROGRAM = [
    "000100 DATA DIVISION.",
    "000110 FILE SECTION.",
    "000120 FD  OPERATIES",
    "000130     RECORD CONTAINS 1200 CHARACTERS.",
    "000140 01  OPERATIES-REC             PIC X(1200).",
    "000150 WORKING-STORAGE SECTION.",
    "000160 77  USERABEN                  PIC X(8) VALUE 'USERABEN'.",
    "000170 77  CS-PROGRAM                PIC X(8) VALUE 'VMDZTEST'.",
    "000180      EXEC SQL INCLUDE SQLERROR END-EXEC.",
    "000190 PROCEDURE DIVISION.",
    "000200     OPEN INPUT OPERATIES.",
    "000210     PERFORM VERWERKING UNTIL VMDZ205I-EOF.",
    "000220     STOP RUN.",
    "000230 VERWERKING.",
    "000240     CONTINUE.",
    "000250 READ-FLAT-FILE.",
    "000260     READ OPERATIES INTO VMDZ205I",
    "000270        AT END SET VMDZ205I-EOF TO TRUE.",
]

# The same program, but the HELP group HEADER already exists with an
# unrelated member under it. Written out in full rather than built by
# list.insert(list.index(...)), which shifts under its own edits and
# hides what is being tested.
PARTIAL_GROUP_PROGRAM = [
    "000100 DATA DIVISION.",
    "000110 FILE SECTION.",
    "000120 FD  OPERATIES",
    "000130     RECORD CONTAINS 1200 CHARACTERS.",
    "000140 01  OPERATIES-REC             PIC X(1200).",
    "000150 WORKING-STORAGE SECTION.",
    "000160 77  USERABEN                  PIC X(8) VALUE 'USERABEN'.",
    "000170 77  CS-PROGRAM                PIC X(8) VALUE 'VMDZTEST'.",
    "000175 01  HELP-VARIABLE.",
    "000176     02  WS-SOMETHING-ELSE     PIC X.",
    "000180      EXEC SQL INCLUDE SQLERROR END-EXEC.",
    "000190 PROCEDURE DIVISION.",
    "000200     OPEN INPUT OPERATIES.",
    "000210     PERFORM VERWERKING UNTIL VMDZ205I-EOF.",
    "000220     STOP RUN.",
    "000230 VERWERKING.",
    "000240     CONTINUE.",
    "000250 READ-FLAT-FILE.",
    "000260     READ OPERATIES INTO VMDZ205I",
    "000270        AT END SET VMDZ205I-EOF TO TRUE.",
]


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


def _logical(line_utils, lines) -> list[str]:
    out = []
    for raw in lines:
        body = str(line_utils.logical(raw) or "").strip()
        if body:
            out.append(" ".join(body.upper().split()))
    return out


def _declared_text(line_utils, config, lines) -> str:
    """Everything the storage injector leaves declared, as one string."""
    injector = RestartStorageInjector(config, line_utils)
    return " ".join(_logical(line_utils, injector.inject(list(lines))))


def _assert_promise_kept(line_utils, role, resolve, lines) -> None:
    """Every SUPPLIED name must appear in the injected storage."""
    names, report = resolve(lines)
    assert report.defaulted, "fixture no longer exercises the fallback"

    declared = _declared_text(line_utils, RestartConfig.build(role, names), lines)

    for key in report.defaulted:
        value = getattr(names, key, "")
        if isinstance(value, str) and value:
            assert value in declared, f"{key} supplied but never declared"


# ---------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------

def test_a_complete_program_resolves_every_name(resolve, source_lines):
    names, report = resolve(source_lines)
    assert names.is_complete() is True
    assert report.refused == []


def test_a_complete_program_needs_no_defaults(resolve, source_lines):
    """Every name is MEASURED when the program carries it."""
    _names, report = resolve(source_lines)
    assert report.defaulted == []


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
    names, report = resolve(lines)
    assert names.restart_key_size == 800
    assert names.read_count_size == 15
    assert "restart_key_size" not in report.defaulted


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
# Ownership: GENERATOR-owned names are supplied, not refused
# ---------------------------------------------------------------------

def test_an_undeclared_payload_field_is_supplied(resolve, source_lines):
    """Was: refused. KY-RESTART is created by M5, so it is supplied.

    The measurement falls back to the catalogued size, and both facts
    are reported - a supplied value is never silent.
    """
    lines = [line for line in source_lines if "KY-RESTART" not in line]
    names, report = resolve(lines)

    assert names.restart_key_field == "KY-RESTART"
    assert names.restart_key_size == 1200
    assert "restart_key_field" in report.defaulted
    assert "restart_key_size" in report.defaulted
    assert "restart_key_field" not in report.refused


def test_an_undeclared_counter_is_supplied(resolve, source_lines):
    """Was: 'an undeclared default is never emitted'."""
    lines = [line for line in source_lines if "WS-TELLER" not in line]
    names, report = resolve(lines)

    assert names.commit_counter == "WS-TELLER"
    assert "commit_counter" in report.defaulted
    assert "commit_counter" not in report.refused


def test_a_supplied_name_says_so(resolve, source_lines):
    lines = [line for line in source_lines if "WS-INPUT-KASBONS" not in line]
    _names, report = resolve(lines)
    assert any(
        "input_save_area" in message and "catalogue" in message
        for message in report.messages
    )


def test_the_eof_pair_is_built_when_the_program_has_no_88_levels(resolve):
    """VMDZ1567 uses a bare 77-level switch. Refusing here would stop
    the whole family over a naming style."""
    lines = [
        "000100 DATA DIVISION.",
        "000110 FILE SECTION.",
        "000120 FD  OPERATIES.",
        "000130 WORKING-STORAGE SECTION.",
        "000140 77  SW-EOF                   PIC X VALUE 'N'.",
        "000150 PROCEDURE DIVISION.",
        "000160     PERFORM VERWERKING UNTIL SW-EOF = 'Y'.",
        "000170 VERWERKING.",
        "000180     CONTINUE.",
        "000190 READ-FLAT-FILE.",
        "000200     READ OPERATIES INTO VMDZ205I",
        "000210        AT END MOVE 'Y' TO SW-EOF.",
    ]
    names, report = resolve(lines)
    assert names.record_name == "VMDZ205I"
    assert names.eof_condition == "VMDZ205I-EOF"
    assert names.not_eof_condition == "VMDZ205I-NOT-EOF"
    assert "eof_condition" in report.defaulted


def test_the_eof_pair_is_refused_without_a_record_name(resolve):
    """It is BUILT from the record name. No record, no pair."""
    names, report = resolve(["000100 DATA DIVISION."])
    assert names.eof_condition == ""
    assert names.not_eof_condition == ""
    assert "eof_condition" in report.refused


# ---------------------------------------------------------------------
# Ownership: PROGRAM-owned names are still refused
# ---------------------------------------------------------------------

def test_a_program_owned_name_is_never_supplied(resolve, source_lines):
    """The guard that matters. CS-PROGRAM belongs to the program."""
    lines = [line for line in source_lines if "CS-PROGRAM" not in line]
    names, report = resolve(lines)

    assert names.program_constant == ""
    assert "program_constant" in report.refused
    assert "program_constant" not in report.defaulted


def test_a_refusal_is_reported_with_a_reason(resolve, source_lines):
    lines = [line for line in source_lines if "INCLUDE SQLERROR" not in line]
    _names, report = resolve(lines)
    assert any(
        "error_paragraph unresolved" in message for message in report.messages
    )
    assert any("refused to invent" in message for message in report.messages)


def test_no_generator_owned_name_is_ever_refused(resolve):
    """The two sets are disjoint, whatever the program looks like.

    The EOF pair is the one exception and it is deliberate: it is BUILT
    from record_name, which the program owns.
    """
    _names, report = resolve([])
    assert set(report.refused) & GENERATOR_OWNED == {
        "eof_condition",
        "not_eof_condition",
    }


def test_an_empty_program_refuses_every_program_owned_name(resolve):
    names, report = resolve([])
    assert names.is_complete() is False
    assert len(report.refused) + len(report.defaulted) == len(names.REQUIRED)
    for key in (
        "file_name",
        "record_name",
        "read_paragraph",
        "process_paragraph",
        "program_constant",
        "error_paragraph",
        "abend_module",
    ):
        assert key in report.refused


def test_an_empty_program_resolves_nothing_it_does_not_own(resolve):
    _names, report = resolve([])
    assert set(report.resolved) <= GENERATOR_OWNED


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
# The promise: a supplied name must actually be declared
# ---------------------------------------------------------------------

def test_a_bare_program_supplies_every_generator_owned_name(resolve):
    """The pipeline case: no restart storage anywhere."""
    names, report = resolve(BARE_PROGRAM)
    for key in GENERATED_STORAGE_FIELDS:
        assert key in report.defaulted, key
        assert getattr(names, key), key
    assert names.read_count_size == 15
    assert names.restart_key_size == 1200


def test_every_supplied_name_is_actually_declared(line_utils, resolve, role):
    """Supplying a name is a PROMISE that M5 declares it.

    Break the promise and the generated family moves to a field that
    does not exist - the defect the legacy generator shipped as
    ADD 1 TO WS-COMMIT-COUNTER. The resolver and the storage injector
    agree today only because both read the same catalogue; that
    agreement is asserted here rather than assumed.
    """
    _assert_promise_kept(line_utils, role, resolve, BARE_PROGRAM)


def test_a_partial_group_is_completed(line_utils, resolve, role):
    """A group header present with its members missing.

    Was xfail: the injector judged "already declared" per GROUP, so the
    members the resolver had already supplied were never written and the
    generated family moved to undeclared fields. The judgement is now
    per FIELD, and this is a live guard.
    """
    _assert_promise_kept(line_utils, role, resolve, PARTIAL_GROUP_PROGRAM)

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


def test_a_default_does_not_accumulate_across_runs(line_utils, source_lines):
    """One resolver instance, two calls: the defaulted list is reset."""
    lines = [line for line in source_lines if "WS-TELLER" not in line]
    resolver = RestartNameResolver(line_utils)
    _n1, first = resolver.resolve(lines)
    _n2, second = resolver.resolve(lines)
    assert first.defaulted == second.defaulted


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
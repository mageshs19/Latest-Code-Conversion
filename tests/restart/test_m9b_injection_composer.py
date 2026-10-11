# LOCATION: tests/restart/test_m9b_injection_composer.py
# ACTION: REPLACE ENTIRE FILE
"""M9b - RestartInjectionComposer.

    contract    - the family is injected, in role order, once
    refusal     - retrieval, no restart table, unusable config
    determinism - a second run reproduces the first byte for byte

CORRECTION - the test owned a PRIVATE paragraph vocabulary

The first cut declared its own NOT_A_PARAGRAPH set, which omitted
END-EXEC. The project already names END-EXEC a non-paragraph word in
rules/statement_layout_rules.py and rules/cobol_cleanup_rules.py, so
this was a THIRD copy that disagreed with both. The composer and its
test then disagreed about what a paragraph header is, and one span
defect was reported as four unrelated failures. The vocabulary is now
imported from the composer.

WHY THE CONFIG IS REBUILT HERE

The composer resolves names from the SOURCE. Asserting against a config
built from `complete_names` would test the fixture, not the composer.

WHY THE SQL ERROR PARAGRAPH IS EXEMPT FROM THE PERFORM CHECK

It arrives through EXEC SQL INCLUDE and carries no paragraph header.
"""

# LOCATION: tests/restart/test_m9b_injection_composer.py
# ACTION: REPLACE the imports block and the "Refusal" section

from __future__ import annotations

import dataclasses
import re
import types

import pytest

import converter.composers.restart.restart_injection_composer as module
from converter.composers.restart.restart_injection_composer import (
    NON_PARAGRAPH_WORDS,
    PROGRAM_KIND_RETRIEVAL,
    RestartInjectionComposer,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_name_resolver import (
    RestartNameResolver,
)
from rules.restart_standard_rules import (
    NOT_APPLICABLE_REASONS,
    RESTART_PARAGRAPH_ROLES,
    ROLE_COMMIT,
    ROLE_CONTROL,
)

TOTALS = ("           DISPLAY 'NUMBER OF RECORDS READ : ' WS-TOTALS-LINE.",)

HEADER = re.compile(r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s*[.]\s*$", re.IGNORECASE)
PERFORM = re.compile(r"^PERFORM\s+(?P<name>[A-Z0-9][A-Z0-9-]*)", re.IGNORECASE)
PERFORM_KEYWORDS = {"UNTIL", "VARYING", "TIMES", "WITH"}
INCLUDE_TEMPLATE = "           EXEC SQL INCLUDE {name} END-EXEC."
WORKING_STORAGE = "WORKING-STORAGE SECTION"


#
# Fixtures
#
@pytest.fixture
def prepared_lines(source_lines, role):
    """The fixture program, guaranteed to reference the restart table.

    The classification gate refuses a program that never names the
    restart table. The include is normally injected upstream; the
    fixture is topped up by CONTENT, never by line position.
    """
    table = str(role.table_name).upper()
    if any(table in str(line).upper() for line in source_lines):
        return list(source_lines)

    out = list(source_lines)
    for index, line in enumerate(out):
        if WORKING_STORAGE in str(line).upper():
            out.insert(index + 1, INCLUDE_TEMPLATE.format(name=role.table_name))
            return out
    return out


@pytest.fixture
def source_text(prepared_lines):
    return "\n".join(prepared_lines)


@pytest.fixture
def composer(line_utils):
    return RestartInjectionComposer(line_utils)


@pytest.fixture
def resolved(line_utils, prepared_lines, role):
    names, _report = RestartNameResolver(line_utils).resolve(prepared_lines)
    return RestartConfig.build(role, names)


@pytest.fixture
def output(composer, source_text, role):
    text, _messages = composer.compose(source_text, role=role, totals=TOTALS)
    return text


def _logical(line_utils, text):
    out = []
    for raw in str(text).splitlines():
        body = str(line_utils.logical(raw) or "").strip()
        if not body or line_utils.is_comment(body):
            continue
        out.append(" ".join(body.upper().split()))
    return out


def _headers(line_utils, text):
    """Headers as the COMPOSER defines them - one vocabulary, one truth."""
    names = []
    for body in _logical(line_utils, text):
        match = HEADER.match(body)
        if match and match.group("name").upper() not in NON_PARAGRAPH_WORDS:
            names.append(match.group("name").upper())
    return names


def _family(config):
    return [config.paragraph(role).upper() for role in RESTART_PARAGRAPH_ROLES]


#
# Contract
#
def test_every_restart_paragraph_is_declared_once(line_utils, output, resolved):
    headers = _headers(line_utils, output)
    for name in _family(resolved):
        assert headers.count(name) == 1, name


def test_the_family_is_spliced_in_role_order(line_utils, output, resolved):
    expected = _family(resolved)
    headers = _headers(line_utils, output)
    assert [name for name in headers if name in expected] == expected


def test_no_paragraph_header_is_duplicated(line_utils, output):
    headers = _headers(line_utils, output)
    assert len(headers) == len(set(headers))


@pytest.mark.parametrize(
    "word",
    ["CONTINUE", "END-EVALUATE", "END-EXEC", "END-IF", "EXIT"],
)
def test_a_scope_terminator_is_not_classified_as_a_paragraph(word):
    """END-EXEC. is a REAL line - it closes an SQL block. The contract is
    that it is never treated as a header, not that it is absent."""
    assert RestartInjectionComposer._is_not_a_paragraph(word) is True
    assert RestartInjectionComposer._is_not_a_paragraph(f"{word}.") is True


def test_a_real_paragraph_name_is_never_excluded():
    """Guards the next 'fix': a startswith('END-') rule would silently
    swallow a legitimate paragraph and truncate its span."""
    assert RestartInjectionComposer._is_not_a_paragraph("END-OF-JOB") is False
    assert RestartInjectionComposer._is_not_a_paragraph("800-PROCESS") is False


def test_the_sql_block_terminator_survives_in_the_output(line_utils, output):
    """The proof the span was not cut: END-EXEC. is still there, and the
    paragraph that owns it is still whole."""
    body = _logical(line_utils, output)
    assert any(line.startswith("END-EXEC") for line in body)

def test_the_control_paragraph_is_performed(line_utils, output, resolved):
    body = _logical(line_utils, output)
    target = f"PERFORM {resolved.paragraph(ROLE_CONTROL)}"
    assert any(line.startswith(target) for line in body)


def test_the_commit_paragraph_is_performed(line_utils, output, resolved):
    body = _logical(line_utils, output)
    target = f"PERFORM {resolved.paragraph(ROLE_COMMIT)}"
    assert any(line.startswith(target) for line in body)


def test_stop_run_is_written_exactly_once(line_utils, output):
    body = _logical(line_utils, output)
    assert len([line for line in body if line.startswith("STOP RUN")]) == 1


def test_stop_run_closes_the_mainline(line_utils, output):
    """Fall-through into the restart family is the defect M6 closed."""
    body = _logical(line_utils, output)
    stop = next(i for i, line in enumerate(body) if line.startswith("STOP RUN"))
    following = body[stop + 1] if stop + 1 < len(body) else ""
    assert not following or HEADER.match(following)


def test_every_perform_resolves_to_a_declared_paragraph(
    line_utils, output, resolved
):
    declared = set(_headers(line_utils, output))
    exempt = {str(resolved.names.error_paragraph or "").upper()}
    for line in _logical(line_utils, output):
        match = PERFORM.match(line)
        if not match:
            continue
        target = match.group("name").upper()
        if target in exempt or target in PERFORM_KEYWORDS:
            continue
        assert target in declared, target


def test_the_supplied_totals_reach_the_output(output):
    assert TOTALS[0].strip() in output


def test_the_run_is_reported(composer, source_text, role):
    _text, messages = composer.compose(source_text, role=role, totals=TOTALS)
    assert any("generated" in message for message in messages)


def test_the_legacy_cleanup_is_given_the_config(
    monkeypatch, line_utils, source_text, role
):
    """Pins the collaborator contract that an earlier cut guessed."""
    seen = {}
    real = module.LegacyRestartCleanup

    class _Spy(real):
        def __init__(self, config, line_utils):
            seen["config"] = config
            super().__init__(config, line_utils)

    monkeypatch.setattr(module, "LegacyRestartCleanup", _Spy)
    RestartInjectionComposer(line_utils).compose(
        source_text, role=role, totals=TOTALS
    )
    assert seen["config"].is_usable()


#
# Refusal
#
def test_a_retrieval_program_is_returned_unchanged(composer, source_text, role):
    text, messages = composer.compose(
        source_text, role=role, program_kind=PROGRAM_KIND_RETRIEVAL
    )
    assert text == source_text
    assert any(NOT_APPLICABLE_REASONS["retrieval"] in m for m in messages)


def test_a_missing_role_is_refused(composer, source_text):
    """How the pipeline says 'this is not a restart program'."""
    text, messages = composer.compose(source_text, role=None)
    assert text == source_text
    assert any(NOT_APPLICABLE_REASONS["dclgen_unresolved"] in m for m in messages)


def test_a_role_with_no_token_falls_back_to_the_text(composer, prepared_lines, role):
    """A role carrying no restart-table token cannot establish
    applicability, so the text scan decides - and refuses."""
    table = str(role.table_name).upper()
    stripped = "\n".join(
        line for line in prepared_lines if table not in str(line).upper()
    )
    tokenless = types.SimpleNamespace(
        table_name="",
        include_name="",
        host_record="",
        host_record_name="",
    )
    text, messages = composer.compose(stripped, role=tokenless)
    assert text == stripped
    assert any(NOT_APPLICABLE_REASONS["no_restart_table"] in m for m in messages)


def test_a_resolved_role_overrides_a_missing_text_reference(
    composer, prepared_lines, role
):
    """The fix. The role is the authority; the text has not been written
    yet. The decision is reported, never silent."""
    table = str(role.table_name).upper()
    stripped = "\n".join(
        line for line in prepared_lines if table not in str(line).upper()
    )
    text, messages = composer.compose(stripped, role=role, totals=TOTALS)
    assert text != stripped
    assert any("restart control applies" in m for m in messages)
    assert not any(
        NOT_APPLICABLE_REASONS["no_restart_table"] in m for m in messages
    )


def test_an_unusable_config_leaves_the_source_untouched(
    composer, prepared_lines, role
):
    """Cripple a PROGRAM-owned name.

    WS-TELLER no longer works here: the commit counter is
    GENERATOR-owned and is supplied from the catalogue. The SQLERROR
    include is owned by the program, so removing it genuinely makes the
    config unusable.
    """
    crippled = "\n".join(
        line for line in prepared_lines if "INCLUDE SQLERROR" not in str(line)
    )
    text, messages = composer.compose(crippled, role=role, totals=TOTALS)
    assert text == crippled
    assert any("error_paragraph" in message for message in messages)


def test_a_role_without_retention_emits_no_paragraph(
    composer, source_text, role
):
    bare = dataclasses.replace(role, retention_days=0)
    text, messages = composer.compose(source_text, role=bare, totals=TOTALS)
    assert text == source_text
    assert any("retention" in message for message in messages)


def test_initialisation_before_open_input_survives(
    composer, prepared_lines, role
):
    """The flow template begins at OPEN INPUT.

    Everything ahead of it is the program's own initialisation. Deleting
    it took DA-DD-MM-CCYY with it - the checkpoint run-date key - so the
    restart row was written for 00.00.0000 on every run.
    """
    marker = "MOVE DATE8-LS TO DATE-DMY8."
    seeded: list[str] = []
    placed = False
    for line in prepared_lines:
        if not placed and "OPEN INPUT" in str(line).upper():
            seeded.append(f"000999     {marker}")
            placed = True
        seeded.append(line)
    assert placed, "fixture has no OPEN INPUT to seed against"

    text, messages = composer.compose(
        "\n".join(seeded), role=role, totals=TOTALS
    )
    assert marker in text
    assert any("preserved" in message for message in messages)


def test_the_flow_still_starts_at_open_input(
    composer, line_utils, source_text, role
):
    """Preserving the prefix must not duplicate the OPEN."""
    text, _messages = composer.compose(source_text, role=role, totals=TOTALS)
    body = _logical(line_utils, text)
    assert len([l for l in body if l.startswith("OPEN INPUT")]) == 1
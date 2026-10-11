# LOCATION: tests/restart/test_m10c_golden_output.py
# ACTION: REPLACE ENTIRE FILE
"""M10c - the generated program is free of every recorded defect.

TWO HALVES, AND THE SECOND IS THE IMPORTANT ONE

  1. the converted fixture produces NO findings
  2. each defect, injected deliberately, IS found

Half 1 alone proves nothing: a checklist with every check commented out
passes it. Half 2 is what makes half 1 mean something.

CORRECTION - role constants were imported inline

Two assertions carried __import__("rules.restart_standard_rules", ...)
mid-expression. A test that cannot be read at a glance is a test nobody
re-reads when it fails. Both now import at the top like everything else.

A REAL ARTEFACT CAN BE INSPECTED TOO

Set RESTART_GOLDEN_PATH to a generated program and the same checklist
runs against it. Absent, that test SKIPS with a reason - it never
silently passes.
"""

from __future__ import annotations

import os
import pathlib

import pytest

from converter.composers.restart.restart_injection_composer import (
    RestartInjectionComposer,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_name_resolver import (
    RestartNameResolver,
)
from rules.restart_standard_rules import ROLE_COMMIT, ROLE_CONTROL
from tests.restart._checklist import RestartChecklist

TOTALS = ("           DISPLAY 'TOTAL INPUT RECORDS : ' WS-TOTALS-LINE.",)
LEGACY_TOKENS = ("CTR-REC", "SW-RECAB", "STOP01")
BANNED_TEXTS = ("DB2 GENERATED WORKING STORAGE",)
WORKING_STORAGE = "WORKING-STORAGE SECTION"
INCLUDE_TEMPLATE = "           EXEC SQL INCLUDE {name} END-EXEC."
GOLDEN_ENV = "RESTART_GOLDEN_PATH"
CHECK_IDS = [
    "C1", "C2", "C3", "C4", "C5", "C6",
    "B1", "B2", "B3", "B5", "B6",
    "S1", "S2", "S3", "S4", "S5", "S6",
]


#
# Fixtures
#
@pytest.fixture
def prepared_lines(source_lines, role):
    table = str(role.table_name).upper()
    out = list(source_lines)
    if not any(table in str(line).upper() for line in out):
        for index, line in enumerate(out):
            if WORKING_STORAGE in str(line).upper():
                out.insert(index + 1, INCLUDE_TEMPLATE.format(name=table))
                break
    return out


@pytest.fixture
def resolved(line_utils, prepared_lines, role):
    names, _report = RestartNameResolver(line_utils).resolve(prepared_lines)
    return RestartConfig.build(role, names)


@pytest.fixture
def generated(line_utils, prepared_lines, role):
    text, _messages = RestartInjectionComposer(line_utils).compose(
        "\n".join(prepared_lines), role=role, totals=TOTALS
    )
    return text


@pytest.fixture
def checklist(line_utils, resolved):
    return RestartChecklist(
        line_utils,
        config=resolved,
        legacy_tokens=LEGACY_TOKENS,
        banned_texts=BANNED_TEXTS,
    )


#
# Injection helpers
#
def _inject(text: str, statement: str) -> str:
    """Put one bad line immediately after PROCEDURE DIVISION."""
    out = []
    for line in text.splitlines():
        out.append(line)
        if "PROCEDURE DIVISION" in line.upper():
            out.append(f"           {statement}")
    return "\n".join(out)


def _inject_into(text: str, paragraph: str, statement: str) -> str:
    """Put one bad line immediately after a paragraph header."""
    header = f"{str(paragraph).upper()}."
    out = []
    for line in text.splitlines():
        out.append(line)
        if line.strip().upper().endswith(header):
            out.append(f"           {statement}")
    return "\n".join(out)


#
# Half 1 - the generated program is clean
#
def test_the_generated_program_has_no_findings(checklist, generated):
    findings = checklist.inspect(generated)
    assert findings == [], "\n".join(findings)


@pytest.mark.parametrize("prefix", CHECK_IDS)
def test_no_single_defect_class_is_present(checklist, generated, prefix):
    """One assertion per checklist line, so a failure names the defect."""
    hits = [f for f in checklist.inspect(generated) if f.startswith(prefix)]
    assert hits == [], "\n".join(hits)


#
# Half 2 - the inspector actually inspects
#
@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        ("END-EXEC.008300", "C1"),
        ("MOVE 0 TO WS-TELLER..", "C2"),
        ("END-IF", "C3"),
        ("MOVE 'X' TO SQL-LOCATION", "S1"),
        ("PERFORM VERWERKING UNTIL SW-EOF = 'Y'", "S2"),
        ("MOVE A OF B OF C TO D", "S4"),
        ("DISPLAY CTR-REC", "S6"),
        ("DISPLAY 'DB2 GENERATED WORKING STORAGE'", "C6"),
    ],
)
def test_an_injected_defect_is_detected(checklist, generated, statement, expected):
    findings = checklist.inspect(_inject(generated, statement))
    assert any(f.startswith(expected) for f in findings), findings


def test_a_per_record_commit_is_detected(checklist, generated, resolved):
    """The defect is a COMMIT STATEMENT inside the business paragraph."""
    polluted = _inject_into(
        generated,
        resolved.names.process_paragraph,
        "EXEC SQL COMMIT END-EXEC.",
    )
    assert any(f.startswith("B5") for f in checklist.inspect(polluted))


def test_performing_the_commit_paragraph_is_not_a_commit(
    checklist, generated, resolved
):
    """M7's tail performs a paragraph whose NAME contains COMMIT.

    Matching the token instead of the statement flagged correct output.
    """
    assert f"PERFORM {resolved.paragraph(ROLE_COMMIT)}" in generated.upper()
    assert not any(f.startswith("B5") for f in checklist.inspect(generated))


def test_a_removed_stop_run_is_detected(checklist, generated):
    stripped = "\n".join(
        line for line in generated.splitlines() if "STOP RUN" not in line.upper()
    )
    assert any(f.startswith("B3") for f in checklist.inspect(stripped))


def test_a_removed_control_perform_is_detected(checklist, generated, resolved):
    control = resolved.paragraph(ROLE_CONTROL)
    stripped = "\n".join(
        line
        for line in generated.splitlines()
        if f"PERFORM {control}" not in line.upper()
    )
    assert any(f.startswith("B1") for f in checklist.inspect(stripped))


def test_a_missing_config_is_reported_not_passed(line_utils, generated):
    """A skipped check must never read as a clean bill of health."""
    bare = RestartChecklist(line_utils)
    assert any(f.startswith("B0") for f in bare.inspect(generated))


#
# A real artefact, when one is available
#
def test_a_generated_artefact_passes_the_checklist(checklist):
    path = os.environ.get(GOLDEN_ENV, "")
    if not path:
        pytest.skip(f"{GOLDEN_ENV} is not set; no generated artefact to inspect")
    source = pathlib.Path(path)
    if not source.exists():
        pytest.skip(f"{GOLDEN_ENV} points at a missing file: {path}")

    findings = checklist.inspect(source.read_text(encoding="utf-8", errors="replace"))
    assert findings == [], "\n".join(findings)
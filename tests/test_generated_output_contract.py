# LOCATION: tests/test_generated_output_contract.py
# ACTION: REPLACE ENTIRE FILE

"""Asserts the three fixes against the ACTUAL generated .cbl.

Unit tests prove the builders are right. This proves the builders are
the ones reaching the output - the failure mode that cost several runs
when an unwired generator produced a parallel, unused implementation.

Skips when nothing has been generated yet, so a clean checkout still
passes.

CORRECTION 1 - the output folder is a RUNTIME decision, not a constant.

This module read DEFAULT_RETRIEVAL_OUTPUT_DIR unconditionally. That
folder is only the live one when the input layout is NOT flat.
config/path_settings.py says so itself:

    "Creating Output\\Retrieval in flat mode would leave an empty folder
     beside the real output and invite the next reader to look in the
     wrong place."

That is exactly what happened. In flat layout the build lands in
DEFAULT_OUTPUT_DIR while Output\\Retrieval keeps a stale orphan, so the
contract was asserted against a file no current run had produced. Every
candidate folder is now considered and the NEWEST artifact across all of
them wins, which is the same question the pipeline answers at run time.

CORRECTION 2 - a stale artifact FAILED instead of SKIPPING.

An artifact older than the generator that produced it cannot speak for
the current code. It reported a defect that had already been fixed:
ENFORCE_FETCH_PROLOGUE was False in rules/cursor_paragraph_rules.py
while the .cbl on disk still carried INITIALIZE DCLDZBFASTV.

A test that cannot answer must say so. Staleness is now a SKIP carrying
both timestamps and the regenerate instruction, never a failure.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from config import path_settings

COBOL_GLOB = "*.cbl"

# Source trees whose edits invalidate a generated artifact.
WATCHED_SOURCE_DIRS = ("converter", "rules", "patterns", "catalogs")
SOURCE_GLOB = "*.py"


def _candidate_output_dirs() -> list[Path]:
    """Every folder a run could legitimately have written to.

    Read through the module rather than by named import, so a layout
    constant that is absent in an older checkout degrades to "not
    considered" instead of ImportError at collection time.
    """
    names = (
        "DEFAULT_OUTPUT_DIR",
        "DEFAULT_RETRIEVAL_OUTPUT_DIR",
        "DEFAULT_UPDATE_OUTPUT_DIR",
    )

    folders: list[Path] = []
    seen: set[str] = set()

    for name in names:
        folder = getattr(path_settings, name, None)
        if folder is None:
            continue
        path = Path(folder)
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        folders.append(path)

    return folders


def _newest_generated_cbl() -> Path | None:
    """The most recent .cbl across every candidate output folder."""
    newest: Path | None = None

    for folder in _candidate_output_dirs():
        if not folder.exists() or not folder.is_dir():
            continue
        for path in folder.glob(COBOL_GLOB):
            if not path.is_file():
                continue
            if newest is None or path.stat().st_mtime > newest.stat().st_mtime:
                newest = path

    return newest


def _newest_source_mtime() -> float:
    """Most recent edit across the generator source trees."""
    root = Path(getattr(path_settings, "PROJECT_ROOT", Path.cwd()))
    newest = 0.0

    for name in WATCHED_SOURCE_DIRS:
        folder = root / name
        if not folder.exists():
            continue
        for path in folder.rglob(SOURCE_GLOB):
            if not path.is_file():
                continue
            newest = max(newest, path.stat().st_mtime)

    return newest


@pytest.fixture(scope="module")
def generated_bodies() -> list[str]:
    artifact = _newest_generated_cbl()

    if artifact is None:
        searched = ", ".join(str(f) for f in _candidate_output_dirs()) or "(none)"
        pytest.skip(f"No generated .cbl found. Searched: {searched}")

    artifact_mtime = artifact.stat().st_mtime
    source_mtime = _newest_source_mtime()

    if source_mtime and artifact_mtime < source_mtime:
        pytest.skip(
            "Generated artifact is older than the generator source.\n"
            f"  artifact : {artifact}\n"
            f"  generated: {_stamp(artifact_mtime)}\n"
            f"  source   : {_stamp(source_mtime)}\n"
            "Regenerate the program, then re-run this module."
        )

    text = artifact.read_text(encoding="utf-8", errors="replace")

    # Columns 8-72 only: sequence areas are not under test.
    return [
        line[7:72].strip()
        for line in text.splitlines()
        if line[7:72].strip()
    ]


def _stamp(mtime: float) -> str:
    from datetime import datetime

    return datetime.fromtimestamp(mtime).strftime("%d-%m-%Y %H:%M:%S")


def test_every_fetch_paragraph_does_not_initialize_its_host_group(generated_bodies):
    fetches = [
        index
        for index, body in enumerate(generated_bodies)
        if re.match(r"^\d{3,6}-FETCH-[A-Z0-9-]+\.$", body)
    ]

    assert fetches, "no generated FETCH paragraph found"

    for index in fetches:
        window = generated_bodies[index : index + 4]
        assert not any(b.startswith("INITIALIZE DCL") for b in window), window


def test_generated_program_has_centralized_initialize(generated_bodies):
    assert any(body == "100-INITIALIZE." for body in generated_bodies)
    assert any(body.startswith("INITIALIZE DCL") for body in generated_bodies)


def test_every_error_branch_sets_sql_location(generated_bodies):
    """Only EVALUATE SQLCODE error branches must set SQL-LOCATION.

    EVALUATE TRUE date-realignment blocks also carry a WHEN OTHER whose
    first statement is MOVE CCYY OF DA-DD-MM-CCYY TO CCYY OF
    DA-CCYYMMDD-R. That branch is not an SQL error branch and must not
    be measured by this contract.
    """
    in_sqlcode_evaluate = False
    checked = 0

    for index, body in enumerate(generated_bodies):
        text = body.strip().upper()

        if text.startswith("EVALUATE SQLCODE"):
            in_sqlcode_evaluate = True
            continue

        if text.startswith("EVALUATE"):
            in_sqlcode_evaluate = False
            continue

        if text.startswith("END-EVALUATE"):
            in_sqlcode_evaluate = False
            continue

        if not in_sqlcode_evaluate:
            continue

        if text != "WHEN OTHER":
            continue

        assert generated_bodies[index + 1].strip().endswith("TO SQL-LOCATION"), (
            f"SQLCODE error branch at body index {index} does not set "
            f"SQL-LOCATION: {generated_bodies[index + 1]!r}"
        )
        checked += 1

    assert checked > 0, "No EVALUATE SQLCODE error branch was found to verify."


def test_every_declare_carries_a_queryno(generated_bodies):
    declares = [b for b in generated_bodies if b.startswith("DECLARE ")]
    querynos = [b for b in generated_bodies if b.startswith("QUERYNO ")]

    assert declares, "no DECLARE CURSOR found"
    assert len(querynos) == len(declares)


def test_no_empty_initialize_statement(generated_bodies):
    assert "INITIALIZE ." not in generated_bodies
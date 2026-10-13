# LOCATION: tests/restart/test_every_tested_88_is_set.py
# ACTION: CREATE NEW FILE
"""
Generic guard for NEW-2 and its whole class: an 88-level condition
that is TESTED (PERFORM ... UNTIL <cond>. / IF <cond>) but never SET
anywhere in the program is a guaranteed runtime hang or dead branch.

This does not assume VMDZ1567, VMBD205I or any specific record name —
it is a structural property any generated program must satisfy.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

TEST_PATTERN = re.compile(
    r"\b(?:PERFORM\s+\S+\s+UNTIL|IF)\s+(?P<cond>[A-Z0-9][A-Z0-9-]*-(?:NOT-)?EOF)\b",
    re.IGNORECASE,
)
SET_PATTERN = re.compile(
    r"\bSET\s+(?P<cond>[A-Z0-9][A-Z0-9-]*-(?:NOT-)?EOF)\s+TO\s+TRUE\b",
    re.IGNORECASE,
)


def _fresh_update_outputs() -> list[Path]:
    out_dir = Path("mainframe/workspace/Output")
    logic_files = list(Path(".").rglob("converter/**/*.py")) + \
        list(Path(".").rglob("rules/**/*.py")) + \
        list(Path(".").rglob("patterns/**/*.py")) + \
        list(Path(".").rglob("catalogs/**/*.py"))
    newest_logic = max((f.stat().st_mtime for f in logic_files), default=0)
    return [
        f for f in out_dir.glob("*.cbl")
        if f.stat().st_mtime > newest_logic
    ]


@pytest.mark.parametrize("cbl", _fresh_update_outputs(), ids=lambda p: p.name)
def test_every_tested_eof_condition_is_set(cbl: Path):
    text = cbl.read_text(encoding="utf-8", errors="ignore")

    tested = {m.group("cond").upper() for m in TEST_PATTERN.finditer(text)}
    set_ = {m.group("cond").upper() for m in SET_PATTERN.finditer(text)}

    never_set = tested - set_
    assert not never_set, (
        f"{cbl.name}: condition(s) {sorted(never_set)} are TESTED "
        f"(PERFORM...UNTIL / IF) but never SET anywhere — infinite "
        f"loop / dead branch at runtime. Declared switches present: "
        f"{sorted(tested | set_)}"
    )
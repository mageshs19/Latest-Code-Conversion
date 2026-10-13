# LOCATION: tests/restart/test_every_tested_88_is_set.py
# ACTION: REPLACE ENTIRE FILE
"""Structural guards on generated COBOL switch logic.

CORRECTION - the first cut matched by NAME SHAPE, not by language

It collected any token ending "-EOF" / "-NOT-EOF" as an 88 condition
name and accepted only `SET <name> TO TRUE` as a write. Both
assumptions are wrong, and both produced false failures on correct
artefacts:

  VM4BD302   03  SW-EOF  PIC 9  VALUE 0.
             AT END MOVE 1 TO SW-EOF
             PERFORM VERWERK-EMISSIONS UNTIL SW-EOF = 1.

             SW-EOF is a DATA ITEM compared relationally, not a
             condition name, and it is written by MOVE. Correct COBOL,
             reported as an infinite loop.

  VM1BD526   02  SW-VMDZ205I  PIC X  VALUE 'N'.
                 88  VMDZ205I-NOT-EOF  VALUE 'N'.
                 88  VMDZ205I-EOF      VALUE 'Y'.
             AT END SET VMDZ205I-EOF TO TRUE.
             IF VMDZ205I-NOT-EOF

             NOT-EOF is primed by the VALUE clause and falsified when
             its SIBLING is set: the switch is ONE storage position, so
             writing either 88 writes both. Correct COBOL, reported as
             a dead branch.

Two properties are asserted separately, because they fail for different
reasons and carry different severity:

  A1  COMPILE  every condition-name REFERENCE resolves to a declared
               88. An undefined condition name does not compile. This
               is the property that caught NEW-2 - VMBD205I-EOF tested
               while only VMDZ205I-EOF was declared.

  A2  LOGIC    every tested 88 belongs to a switch that is WRITTEN
               somewhere - by SET of any 88 subordinate to that switch,
               or by a MOVE to the switch itself. A switch that is
               never written cannot terminate a loop.

A relational test is NOT a condition-name reference and is excluded
from both: `UNTIL SW-EOF = 1`, `IF CO-ID-RS = '1'`, `IF WS-TELLER > 99`.

The guards are self-verified by test_guard_detects_the_new2_shape,
which runs the analysis over an inline program carrying the NEW-2
defect, so the guards cannot silently stop guarding when no artefact
happens to be fresh.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

BODY_START = 7
BODY_END = 72

LEVEL_88 = re.compile(r"^88\s+(?P<name>[A-Z][A-Z0-9-]*)")
DATA_ITEM = re.compile(r"^(?P<level>\d\d)\s+(?P<name>[A-Z][A-Z0-9-]*)")
PROCEDURE_DIVISION = re.compile(r"^PROCEDURE\s+DIVISION")

CONDITION_REF = re.compile(r"\b(?:IF|UNTIL)\s+(?P<name>[A-Z][A-Z0-9-]*)")
SET_TRUE = re.compile(r"\bSET\s+(?P<name>[A-Z][A-Z0-9-]*)\s+TO\s+TRUE\b")
MOVE_TO = re.compile(r"\bMOVE\s+.+?\s+TO\s+(?P<name>[A-Z][A-Z0-9-]*)\b")

# What may follow a name and still leave it a CONDITION NAME rather than
# the left side of a relational condition.
RELATIONAL_HEAD = re.compile(r"^(?:=|<|>|NOT\b|IS\b|EQUAL\b|GREATER\b|LESS\b)")
QUALIFIER = re.compile(r"^(?:OF|IN)\s+[A-Z][A-Z0-9-]*\s*")
# COBOL words that are never user condition names.
RESERVED = {
    "ALL", "FALSE", "HIGH-VALUE", "HIGH-VALUES", "LOW-VALUE", "LOW-VALUES",
    "NOT", "OTHER", "SPACE", "SPACES", "TRUE", "ZERO", "ZEROES", "ZEROS",
}


def _is_comment(line: str) -> bool:
    text = line.rstrip("\n")
    return len(text) > 6 and text[6:7] in {"*", "/", "D", "d"}


def _body(line: str) -> str:
    text = line.rstrip("\n")
    if len(text) >= BODY_END and text[:6].strip().isdigit():
        return text[BODY_START:BODY_END]
    if len(text) > BODY_START and text[:6].strip().isdigit():
        return text[BODY_START:]
    return text


def _logical_lines(text: str) -> list[str]:
    out: list[str] = []
    for raw in text.splitlines():
        if _is_comment(raw):
            continue
        body = " ".join(_body(raw).upper().split())
        if body:
            out.append(body)
    return out


def _declared_conditions(lines: list[str]) -> dict[str, str]:
    """88 condition name -> the switch it is subordinate to."""
    conditions: dict[str, str] = {}
    parent = ""
    for body in lines:
        if PROCEDURE_DIVISION.match(body):
            break
        match88 = LEVEL_88.match(body)
        if match88:
            if parent:
                conditions[match88.group("name")] = parent
            continue
        item = DATA_ITEM.match(body)
        if item:
            parent = item.group("name")
    return conditions


def _condition_references(lines: list[str]) -> set[str]:
    """Names used where a CONDITION NAME is required - IF x / UNTIL x.

    A name is NOT a condition name when what follows it is a relational
    operator, a subscript, or a qualification leading to one. All three
    appear in generated output:

        IF CO-ID-RS IN DCLDZ01RSTV = '1'   qualified comparison
        UNTIL SW-EOF = 1                   plain comparison
        IF TAB-ENTRY (I) = SPACES          subscripted comparison

    Only a bare name - optionally qualified, then ending or continuing
    with AND / OR / THEN - is a condition name.
    """
    found: set[str] = set()
    for body in lines:
        for match in CONDITION_REF.finditer(body):
            name = match.group("name")
            if name in RESERVED:
                continue

            tail = body[match.end():].lstrip()
            while QUALIFIER.match(tail):
                tail = QUALIFIER.sub("", tail, count=1).lstrip()

            if tail.startswith("("):
                continue
            if RELATIONAL_HEAD.match(tail):
                continue

            found.add(name)
    return found


def _written_switches(lines: list[str], conditions: dict[str, str]) -> set[str]:
    """Every switch some statement writes."""
    written: set[str] = set()
    for body in lines:
        for match in SET_TRUE.finditer(body):
            parent = conditions.get(match.group("name"))
            if parent:
                written.add(parent)
        for match in MOVE_TO.finditer(body):
            written.add(match.group("name"))
    return written


def _fresh_update_outputs() -> list[Path]:
    out_dir = Path("mainframe/workspace/Output")
    logic_files = (
        list(Path(".").rglob("converter/**/*.py"))
        + list(Path(".").rglob("rules/**/*.py"))
        + list(Path(".").rglob("patterns/**/*.py"))
        + list(Path(".").rglob("catalogs/**/*.py"))
    )
    newest_logic = max((f.stat().st_mtime for f in logic_files), default=0)
    return [
        f for f in out_dir.glob("*.cbl")
        if f.stat().st_mtime > newest_logic
    ]


FRESH = _fresh_update_outputs()


@pytest.mark.parametrize("cbl", FRESH, ids=lambda p: p.name)
def test_a1_every_condition_name_reference_is_declared(cbl: Path):
    """COMPILE: an undefined condition name does not assemble."""
    lines = _logical_lines(cbl.read_text(encoding="utf-8", errors="ignore"))
    conditions = _declared_conditions(lines)
    undefined = sorted(_condition_references(lines) - set(conditions))

    assert not undefined, (
        f"{cbl.name}: condition name(s) {undefined} are used in "
        f"IF / PERFORM ... UNTIL but are declared by no 88 level - the "
        f"program does not compile. Declared 88s: {sorted(conditions)}"
    )


@pytest.mark.parametrize("cbl", FRESH, ids=lambda p: p.name)
def test_a2_every_tested_switch_is_written(cbl: Path):
    """LOGIC: a switch no statement writes cannot end a loop."""
    lines = _logical_lines(cbl.read_text(encoding="utf-8", errors="ignore"))
    conditions = _declared_conditions(lines)
    written = _written_switches(lines, conditions)

    tested = _condition_references(lines) & set(conditions)
    stuck = sorted(
        name for name in tested if conditions[name] not in written
    )

    assert not stuck, (
        f"{cbl.name}: condition(s) {stuck} are tested, but the switch "
        f"they belong to is never written by SET or MOVE - infinite "
        f"loop or dead branch at runtime. Switches written: "
        f"{sorted(written)}"
    )


NEW2_SHAPE = """\
000540     02  SW-VMDZ205I            PIC X     VALUE 'N'.
000550         88  VMDZ205I-NOT-EOF       VALUE 'N'.
000560         88  VMDZ205I-EOF           VALUE 'Y'.
000590 PROCEDURE DIVISION.
002150     PERFORM VERWERKING UNTIL VMBD205I-EOF.
002840        AT END SET VMDZ205I-EOF TO TRUE.
"""

RELATIONAL_SHAPE = """\
000830     03  SW-EOF                    PIC 9       VALUE 0.
000840 PROCEDURE DIVISION.
002730        AT END MOVE 1 TO SW-EOF
002760     PERFORM VERWERK-EMISSIONS UNTIL SW-EOF = 1.
"""

SIBLING_SHAPE = """\
000550     02  SW-VMDZ205I            PIC X     VALUE 'N'.
000560         88  VMDZ205I-NOT-EOF       VALUE 'N'.
000570         88  VMDZ205I-EOF           VALUE 'Y'.
000580 PROCEDURE DIVISION.
002330     PERFORM 200-VERWERK-INFIL UNTIL VMDZ205I-EOF.
003740        AT END SET VMDZ205I-EOF TO TRUE.
003760        IF VMDZ205I-NOT-EOF
"""


def test_guard_detects_the_new2_shape():
    """A1 must still catch the defect it was created for."""
    lines = _logical_lines(NEW2_SHAPE)
    conditions = _declared_conditions(lines)
    assert "VMBD205I-EOF" in (_condition_references(lines) - set(conditions))


def test_a_relational_test_is_not_a_condition_name():
    """VM4BD302: UNTIL SW-EOF = 1 is a comparison, not a condition."""
    lines = _logical_lines(RELATIONAL_SHAPE)
    assert "SW-EOF" not in _condition_references(lines)


def test_a_sibling_set_writes_the_whole_switch():
    """VM1BD526: one storage position; setting EOF falsifies NOT-EOF."""
    lines = _logical_lines(SIBLING_SHAPE)
    conditions = _declared_conditions(lines)
    written = _written_switches(lines, conditions)
    tested = _condition_references(lines) & set(conditions)
    assert not [n for n in tested if conditions[n] not in written]
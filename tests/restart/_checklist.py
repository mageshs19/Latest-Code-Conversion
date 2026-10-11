# LOCATION: tests/restart/_checklist.py
# ACTION: REPLACE ENTIRE FILE
"""The VMDZ1567 verification checklist, as executable assertions.

Leading underscore so pytest does not collect it, matching
tests/cursor_where/_fixtures.py.

    RestartChecklist(line_utils, config=...).inspect(text) -> list[str]

An EMPTY list means the generated program carries none of the defects
the handover recorded. Every finding is "ID: what is wrong", so a
failure names the defect rather than a line number that moves.

SHAPE FIRST, NAMES SECOND

Checks that need no site name run on every program. Checks that need
one - is the control paragraph performed? - are reported as SKIPPED
when no config is supplied, never silently passed. A skipped check that
reads as a pass is how a checklist rots.

CORRECTION - B5 matched a NAME, not a STATEMENT

The per-record COMMIT check was `"COMMIT" in body`. M7's repaired
business paragraph legitimately ends with

    IF <counter> > <threshold>
        PERFORM <nnn>-PROCESS-COMMIT
    END-IF.

so the check fired on CORRECT output: it matched the paragraph NAME.
The defect being hunted is a COMMIT STATEMENT inside the paragraph -
the EXEC SQL block M7's _strip_inline_commit removes. COMMIT_STATEMENT
is therefore ANCHORED at the start of the logical body, where PERFORM
cannot reach it. This is the third defect this session caused by a
substring standing in for the real question; the first two were
END-EXEC. read as a paragraph header and a collaborator arity caught
from a TypeError.

DELIBERATELY NOT CHECKED HERE

  undeclared data names   needs a full DATA DIVISION symbol table
  CHAR literal quoting    needs the DCLGEN column type

Both belong to the review engine, which already owns a symbol view.
Claiming them here would mean two half-implementations.
"""

from __future__ import annotations

import re

from converter.composers.restart.restart_injection_composer import (
    NON_PARAGRAPH_WORDS,
)
from rules.restart_standard_rules import ROLE_COMMIT, ROLE_CONTROL

HEADER = re.compile(r"^(?P<name>[A-Z0-9][A-Z0-9-]*)\s*[.]\s*$", re.IGNORECASE)
DATA_ENTRY = re.compile(
    r"^(?P<level>0?[1-9]|[1-4][0-9]|66|77)\s+(?P<name>[A-Z0-9][A-Z0-9-]*)",
    re.IGNORECASE,
)
SEQUENCE_LEAK = re.compile(r"[.]\d{6,8}\b")
QUERYNO = re.compile(r"\bQUERYNO\s+(?P<number>\d+)", re.IGNORECASE)
DOUBLE_QUALIFIED = re.compile(r"\bOF\s+\S+\s+OF\s+\S+", re.IGNORECASE)
QUOTED_LOCATION = re.compile(r"MOVE\s+'[^']*'\s+TO\s+SQL-LOCATION", re.IGNORECASE)
LITERAL_LOOP = re.compile(r"\bUNTIL\b[^']*=\s*'", re.IGNORECASE)

# A COMMIT STATEMENT, not the word COMMIT. Anchored, so the REQUIRED
# "PERFORM <nnn>-PROCESS-COMMIT" tail can never match.
COMMIT_STATEMENT = re.compile(r"^(?:EXEC\s+SQL\s+)?COMMIT\b", re.IGNORECASE)

OPENERS = ("IF ", "EVALUATE ")
CLOSERS = ("END-IF", "END-EVALUATE")


class RestartChecklist:
    """Reads generated COBOL. Changes nothing."""

    def __init__(
        self,
        line_utils,
        *,
        config=None,
        legacy_tokens=(),
        banned_texts=(),
    ) -> None:
        self.line_utils = line_utils
        self.config = config
        self.legacy_tokens = tuple(legacy_tokens or ())
        self.banned_texts = tuple(banned_texts or ())

    #
    # Public surface
    #
    def inspect(self, text: str) -> list[str]:
        bodies = self._bodies(text)
        findings: list[str] = []
        findings.extend(self._compile_blockers(bodies))
        findings.extend(self._behaviour(bodies))
        findings.extend(self._standards(bodies))
        return findings

    #
    # Compile blockers
    #
    def _compile_blockers(self, bodies: list[str]) -> list[str]:
        out: list[str] = []

        for body in bodies:
            if SEQUENCE_LEAK.search(body):
                out.append(f"C1: a sequence number leaked into the body: {body}")
            if ".." in body:
                out.append(f"C2: double sentence terminator: {body}")

        out.extend(self._orphan_terminators(bodies))
        out.extend(self._duplicate_declarations(bodies))
        out.extend(self._value_in_file_section(bodies))

        for banned in self.banned_texts:
            if any(banned.upper() in body for body in bodies):
                out.append(f"C6: non-COBOL text survived: {banned}")
        return out

    @staticmethod
    def _orphan_terminators(bodies: list[str]) -> list[str]:
        depth = 0
        for body in bodies:
            if body.startswith(OPENERS):
                depth += 1
            elif body.startswith(CLOSERS):
                depth -= 1
                if depth < 0:
                    return [f"C3: orphan scope terminator: {body}"]
        return []

    @staticmethod
    def _duplicate_declarations(bodies: list[str]) -> list[str]:
        """A name declared twice where qualification cannot save it.

        Subordinate names MAY repeat - DD, MM and YY appear under every
        date group in the manual reference - because each reference is
        qualified. Flagging them reported legal COBOL as a defect.

        What cannot repeat is a name at 01 or 77: those are the
        qualification roots. SW-EOF declared as an 02 AND as a 77 is the
        real case, and it is caught because the 77 collides.
        """
        roots: set[str] = set()
        out: list[str] = []
        for body in bodies:
            match = DATA_ENTRY.match(body)
            if not match:
                continue
            level = match.group("level").lstrip("0") or "0"
            if level not in ("1", "77"):
                continue
            name = match.group("name").upper()
            if name in roots:
                out.append(f"C4: data name declared twice: {name}")
            roots.add(name)
        return out
    
    @staticmethod
    def _value_in_file_section(bodies: list[str]) -> list[str]:
        """VALUE is illegal in the FILE SECTION - a hard compile error."""
        inside = False
        for body in bodies:
            if body.startswith("FILE SECTION"):
                inside = True
                continue
            if body.startswith(("WORKING-STORAGE", "LINKAGE", "PROCEDURE")):
                inside = False
                continue
            if inside and " VALUE " in f" {body} ":
                return [f"C5: VALUE clause inside the FILE SECTION: {body}"]
        return []

    #
    # Behaviour
    #
    def _behaviour(self, bodies: list[str]) -> list[str]:
        out: list[str] = []
        stops = [b for b in bodies if b.startswith("STOP RUN")]
        if len(stops) != 1:
            out.append(f"B3: expected one STOP RUN, found {len(stops)}")

        if self.config is None:
            return out + ["B0: no config supplied; name-driven checks skipped"]

        control = self.config.paragraph(ROLE_CONTROL)
        commit = self.config.paragraph(ROLE_COMMIT)
        if not self._performs(bodies, control):
            out.append(f"B1: {control} is never performed")
        if not self._performs(bodies, commit):
            out.append(f"B2: {commit} is never performed")

        paragraphs = self._paragraphs(bodies)
        business = paragraphs.get(self.config.names.process_paragraph.upper(), [])
        if any(COMMIT_STATEMENT.match(body) for body in business):
            out.append("B5: the business paragraph still commits per record")
        if not paragraphs:
            out.append("B6: no paragraph was declared at all")
        return out

    @staticmethod
    def _performs(bodies: list[str], paragraph: str) -> bool:
        target = f"PERFORM {paragraph.upper()}"
        return any(body.startswith(target) for body in bodies)

    #
    # Standards
    #
    def _standards(self, bodies: list[str]) -> list[str]:
        out: list[str] = []

        numbers = [m.group("number") for b in bodies for m in [QUERYNO.search(b)] if m]
        if len(numbers) != len(set(numbers)):
            out.append(f"S3: a QUERYNO is reused: {sorted(numbers)}")

        for body in bodies:
            if QUOTED_LOCATION.search(body):
                out.append(f"S1: SQL-LOCATION carries a literal, not a number: {body}")
            if LITERAL_LOOP.search(body):
                out.append(f"S2: a loop tests a literal instead of an 88-level: {body}")
            if DOUBLE_QUALIFIED.search(body):
                out.append(f"S4: double-qualified reference: {body}")

        out.extend(self._totals(bodies))
        for token in self.legacy_tokens:
            if any(token.upper() in body for body in bodies):
                out.append(f"S6: legacy declaration retained: {token}")
        return out

    @staticmethod
    def _totals(bodies: list[str]) -> list[str]:
        for index, body in enumerate(bodies):
            if not body.startswith("STOP RUN"):
                continue
            window = bodies[max(0, index - 6) : index]
            if not any(b.startswith("DISPLAY") for b in window):
                return ["S5: no end-of-run totals before STOP RUN"]
        return []

    #
    # Reading
    #
    def _bodies(self, text: str) -> list[str]:
        out: list[str] = []
        for raw in str(text or "").splitlines():
            body = str(self.line_utils.logical(raw) or "").strip()
            if not body or self.line_utils.is_comment(body):
                continue
            out.append(" ".join(body.upper().split()))
        return out

    @staticmethod
    def _paragraphs(bodies: list[str]) -> dict[str, list[str]]:
        found: dict[str, list[str]] = {}
        current = ""
        for body in bodies:
            match = HEADER.match(body)
            if match and match.group("name").upper() not in NON_PARAGRAPH_WORDS:
                current = match.group("name").upper()
                found[current] = []
                continue
            if current:
                found[current].append(body)
        return found


__all__ = ["RestartChecklist"]
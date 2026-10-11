# LOCATION: converter/composers/counter_declaration_composer.py
# ACTION: REPLACE ENTIRE FILE

"""Counter declaration composer.

Declares every row counter the PROCEDURE DIVISION increments but
WORKING-STORAGE does not define, and appends the end-of-run totals.

    10  WS-NB-BFAS-COUNT       PIC 9(7)  COMP-3 VALUE ZEROES.
    10  WS-NB-OUTPUT-COUNT     PIC 9(7)  COMP-3 VALUE ZEROES.

    DISPLAY 'TOTAL BFAS RECORDS   : ' WS-NB-BFAS-COUNT
    DISPLAY 'TOTAL OUTPUT RECORDS : ' WS-NB-OUTPUT-COUNT
    STOP RUN.

REFERENCE-DRIVEN, NOT TABLE-DRIVEN

The composer declares exactly the counters the PROCEDURE DIVISION
actually increments. It can therefore never declare an unused field,
and never miss one.


CORRECTION 1 - the stage aborted on a missing helper

    [error] declare_counters: AttributeError:
    'CounterDeclarationComposer' object has no attribute
    '_procedure_division_index'

_referenced_counters called a method that was never declared, so the
whole stage raised and NOTHING was declared and NO totals were emitted.
That is worse than the defect it was added to fix: the generated
program increments fields WORKING-STORAGE does not define, and does not
compile. The helper is declared below.


CORRECTION 2 - a counter was declared for a table never read

    10 WS-NB-EVEF-COUNT   PIC 9(7) COMP-3 VALUE ZEROES.
    DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT

always zero, and misleading in the job log. The scan is now bounded to
the PROCEDURE DIVISION and skips comment, debug and continuation lines,
so a counter named in a DISPLAY literal or in a commented-out block is
never mistaken for an increment.


RESPONSIBILITY SPLIT

This class decides WHAT to declare and WHAT to display.
CounterDeclarationWriter decides WHERE to put it, which is where the
record-corruption defect lived.


CLEAN ARCHITECTURE

- Constants live in rules/counter_declaration_rules.py and
  rules/structural_safety_rules.py.
- Regex lives in patterns/counter_declaration_patterns.py.
- No program, record, table, cursor or host variable name is hardcoded.
"""

from __future__ import annotations

from converter.composers.counter_declaration_writer import (
    CounterDeclarationWriter,
)
from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.counter_declaration_patterns import (
    COUNTER_INCREMENT_PATTERN,
    DATA_ENTRY_PATTERN,
)
from rules.counter_declaration_rules import (
    COUNTER_DECLARATION_MESSAGES,
    EMIT_COUNTER_TOTALS,
    ENFORCE_COUNTER_DECLARATION,
)

NOT_FOUND = -1

# A division header is Area A text. Matched on the logical body, so no
# indicator or sequence area reaches this comparison.
PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"


class CounterDeclarationComposer:
    """Declares referenced row counters and emits end-of-run totals."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
        writer: CounterDeclarationWriter | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.writer = writer or CounterDeclarationWriter(
            fixed_format=self.fixed_format,
        )
        self.messages: list[str] = []

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def compose(self, text: str) -> str:
        self.messages = []

        if not text or not ENFORCE_COUNTER_DECLARATION:
            return str(text or "")

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        referenced = self._referenced_counters(lines)

        if not referenced:
            # Not a refusal. Either no pass emitted an increment, or
            # this is a second idempotent run. Say which, rather than
            # returning in silence.
            self.messages.append(
                COUNTER_DECLARATION_MESSAGES["no_references"].format(
                    examined=len(lines),
                )
            )
            return "\n".join(lines).rstrip() + "\n"

        declared = self._declared_names(lines)
        missing = [name for name in referenced if name not in declared]

        if missing:
            lines = self.writer.declare(lines=lines, missing=missing)
            self.messages.extend(self.writer.messages)

        if EMIT_COUNTER_TOTALS:
            # REFERENCED, not MISSING. A counter already declared in the
            # source is still incremented and still belongs in the
            # totals; displaying only the newly declared ones would drop
            # it from the job log.
            lines = self.writer.append_totals(
                lines=lines,
                counters=referenced,
            )
            self.messages.extend(self.writer.messages)

        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------
    def _procedure_division_index(self, lines: list[str]) -> int:
        """Index of the PROCEDURE DIVISION header, or NOT_FOUND.

        CORRECTION 1 declared this. Without it the whole stage raised
        AttributeError and no counter was declared at all.

        An ADD outside the PROCEDURE DIVISION is not an increment - it
        is a DISPLAY literal, a comment, or documentation. Scanning the
        whole file is how a counter for an unread table entered the set.
        """
        for index, line in enumerate(lines):
            if self._is_skippable(line):
                continue
            logical = self._logical(line).upper()
            if logical.startswith(PROCEDURE_DIVISION_TOKEN):
                return index
        return NOT_FOUND

    def _referenced_counters(self, lines: list[str]) -> list[str]:
        """Counter names the PROCEDURE DIVISION actually increments.

        The ONLY admissible source. A cursor spec, a table list or a
        DCLGEN group must never seed this set: each would declare a
        counter for a table this program does not read.

        Order is first-seen and never sorted, so the totals block reads
        in the order the program counts.
        """
        found: list[str] = []
        seen: set[str] = set()

        start = self._procedure_division_index(lines)
        if start == NOT_FOUND:
            return found

        for line in lines[start:]:
            if self._is_skippable(line):
                continue

            match = COUNTER_INCREMENT_PATTERN.match(self._logical(line))
            if not match:
                continue

            name = self._matched_name(match).upper()
            if name and name not in seen:
                seen.add(name)
                found.append(name)

        return found

    def _declared_names(self, lines: list[str]) -> set[str]:
        """Every data-name declared in the source, upper-cased.

        Read through DATA_ENTRY_PATTERN rather than a substring test: a
        DISPLAY literal mentioning the name is not a declaration, and
        declaring an existing name twice is a compile error.
        """
        names: set[str] = set()

        for line in lines:
            if self._is_skippable(line):
                continue

            match = DATA_ENTRY_PATTERN.match(self._logical(line))
            if match:
                name = self._matched_name(match)
                if name:
                    names.add(name.upper())

        return names

    # ------------------------------------------------------------------
    # Line helpers
    # ------------------------------------------------------------------
    def _logical(self, line: str) -> str:
        """Columns 8-72, stripped. Never raises on a malformed line."""
        try:
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:                       # noqa: BLE001
            return str(line or "").strip()

    def _is_skippable(self, line: str) -> bool:
        """Comment, page-eject, debug or continuation line."""
        try:
            return bool(
                self.fixed_format.is_comment_or_control_line(line)
            )
        except Exception:                       # noqa: BLE001
            return str(line or "").lstrip().startswith(("*", "/"))

    @staticmethod
    def _matched_name(match) -> str:
        """The 'name' group, or the last group the pattern exposes.

        Tolerates a pattern that uses a positional group, so a pattern
        file that has not been updated degrades to "works" rather than
        to IndexError in the middle of a conversion.
        """
        try:
            return str(match.group("name") or "").strip()
        except (IndexError, KeyError):
            groups = [g for g in match.groups() if g]
            return str(groups[-1]).strip() if groups else ""


__all__ = ["CounterDeclarationComposer"]
# LOCATION: converter/generators/restart/restart_main_flow_builder.py
# ACTION: CREATE NEW FILE
"""Builds the mainline statement block of an update program.

    OPEN INPUT <file>.
    PERFORM <control>.
    PERFORM <reader>.
    PERFORM <process> UNTIL <eof>.
    PERFORM <commit>.
    <end-of-run totals>
    CLOSE <file>.
    STOP RUN.

WHAT THIS MODULE FIXES

The generated mainline read:

    OPEN INPUT OPERATIES.
    IF NOT SW-EOF = 'Y'  PERFORM READ-FLAT-FILE  END-IF.
    PERFORM VERWERKING UNTIL SW-EOF = 'Y'.
    CLOSE OPERATIES.
    EXEC SQL COMMIT END-EXEC.

Three defects in five lines:

    1. the control paragraph was never performed, so the restart table
       was never touched,
    2. the commit paragraph was never performed, so no checkpoint was
       ever written,
    3. there was no STOP RUN, so after the final COMMIT the program fell
       THROUGH into 700-RESTART-CONTROL and executed every restart
       paragraph in source order.

The template this builder renders cannot express any of those: the order
is fixed, and STOP RUN is the last line.

TOTALS ARE NOT OURS

End-of-run counter totals are already produced by the shared counter
composer the retrieval path uses - "declare referenced row counters and
emit end-of-run totals". This builder accepts those lines and splices
them in. It never authors a DISPLAY, because a second author means two
sets of totals that disagree.

REFUSAL

A config that is not usable produces NO mainline. A partial mainline is
worse than none: it would perform paragraphs that were never written.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

from typing import Sequence

from converter.generators.restart.restart_config import RestartConfig
from rules.restart_standard_rules import (
    ROLE_COMMIT,
    ROLE_CONTROL,
)
from rules.restart_statement_templates import MAIN_FLOW_TEMPLATE

TOTALS_MARKER = "{totals_block}"
STOP_RUN = "STOP RUN."
OPEN_PREFIX = "OPEN INPUT"
CLOSE_PREFIX = "CLOSE"


class RestartMainFlowBuilder:
    """Renders the mainline between OPEN INPUT and STOP RUN."""

    def __init__(self, config: RestartConfig) -> None:
        self.config = config
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def build(
        self,
        totals: Sequence[str] = (),
        *,
        suppress_open: bool = False,
        suppress_prime_read: bool = False,
    ) -> tuple[str, ...]:
        """The mainline lines, or an empty tuple when refused.

        `totals` are the end-of-run DISPLAY lines produced by the
        shared counter composer. They are spliced in unchanged.

        SUPPRESSION

        The template is the SHAPE of a mainline, not a claim about what
        the program lacks. When OPEN INPUT or the priming PERFORM of
        the reader already exist OUTSIDE the region the composer is
        replacing - typically in an initialisation paragraph - writing
        them again opens the file twice and reads the first record
        twice. The caller measures; this method obeys and reports.
        """
        self.messages = []

        if not self._usable():
            return ()

        values = self.config.placeholders()
        prime_read = f"PERFORM {self.config.names.read_paragraph}."
        lines: list[str] = []
        dropped: list[str] = []

        for raw in MAIN_FLOW_TEMPLATE:
            if raw.strip() == TOTALS_MARKER:
                lines.extend(str(line) for line in totals)
                continue

            rendered = raw.format(**values)
            body = " ".join(rendered.strip().upper().split())

            if suppress_open and body.startswith(OPEN_PREFIX):
                dropped.append(rendered.strip())
                continue
            if suppress_prime_read and body == prime_read.upper():
                dropped.append(rendered.strip())
                continue

            lines.append(rendered)

        lines = self._collapse_blanks(lines)

        for statement in dropped:
            self.messages.append(
                f"Restart main flow: suppressed '{statement}'; the "
                "program already carries it outside the replaced region."
            )

        self._report(lines, totals)
        return tuple(lines)

    @staticmethod
    def _collapse_blanks(lines: list[str]) -> list[str]:
        """One separator, never two.

        Dropping a statement leaves its blank behind. The template's
        separator count is part of its contract, so it is restored
        here rather than left to drift.
        """
        out: list[str] = []
        for line in lines:
            if not line.strip() and (not out or not out[-1].strip()):
                continue
            out.append(line)
        while out and not out[-1].strip():
            out.pop()
        return out
    
    def statements(self, totals: Sequence[str] = ()) -> tuple[str, ...]:
        """The mainline with blank separator lines removed."""
        return tuple(
            line.strip() for line in self.build(totals) if line.strip()
        )

    # -----------------------------------------------------------------
    # Gate
    # -----------------------------------------------------------------

    def _usable(self) -> bool:
        if self.config.is_usable():
            return True

        for name in self.config.missing():
            self.messages.append(
                f"Restart main flow: {name} unresolved; mainline not built."
            )
        if self.config.retention_days <= 0:
            self.messages.append(
                "Restart main flow: the restart role carries no retention "
                "value; mainline not built."
            )
        return False

    # -----------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------

    def _report(self, lines: list[str], totals: Sequence[str]) -> None:
        names = self.config.names
        self.messages.append(
            "Restart main flow: performed "
            f"{self.config.paragraph(ROLE_CONTROL)} before the first read."
        )
        self.messages.append(
            "Restart main flow: performed "
            f"{self.config.paragraph(ROLE_COMMIT)} before CLOSE "
            f"{names.file_name}."
        )
        self.messages.append(
            f"Restart main flow: {STOP_RUN} is the last statement."
        )
        if totals:
            self.messages.append(
                f"Restart main flow: spliced {len(totals)} totals line(s) "
                "from the shared counter composer."
            )
        else:
            self.messages.append(
                "Restart main flow: no totals supplied; none written."
            )


__all__ = [
    "CLOSE_PREFIX",
    "OPEN_PREFIX",
    "STOP_RUN",
    "TOTALS_MARKER",
    "RestartMainFlowBuilder",
]
# LOCATION: converter/composers/counter_declaration_writer.py
# ACTION: REPLACE ENTIRE FILE
"""Facade over the counter declaration package.

Keeps a single import path for CounterDeclarationComposer while the
placement, rendering and totals logic lives in focused modules:

    counter_declaration/counter_line_factory.py     rendering
    counter_declaration/counter_anchor.py           anchor model + lookup
    counter_declaration/counter_anchor_resolver.py  safety-first placement
    counter_declaration/counter_totals_writer.py    end-of-run totals

This class contains no COBOL knowledge of its own.


CORRECTION - a counter was declared and displayed for a table the
PROCEDURE DIVISION never increments:

    10 WS-NB-EVEF-COUNT          PIC 9(7) COMP-3 VALUE ZEROES.
    DISPLAY 'TOTAL EVEF RECORDS   : ' WS-NB-EVEF-COUNT

always zero, misleading in the job log, and a direct breach of the
stated contract:

    "Declaration is REFERENCE-DRIVEN, not table-driven: the composer
     declares exactly the counters the PROCEDURE DIVISION actually
     increments. It can therefore never declare an unused field."

The composer computes that set. This class is the LAST gate before the
line is written, so it no longer trusts the list it is handed:

  * a name that is not counter-shaped is refused,
  * a name already declared in the DATA DIVISION is refused,
  * the totals pass may only display names this class actually
    declared, or that the program already declares - it can never
    WIDEN the set,
  * every refusal is reported. A silent drop is how the opposite
    defect - a missing counter - would hide.


MESSAGE CONTRACT - read before changing

Both public methods RESET self.messages. That is deliberate and matches
the composer, which drains after each call:

    lines = self.writer.declare(lines=lines, missing=missing)
    self.messages.extend(self.writer.messages)
    lines = self.writer.append_totals(lines=lines, counters=...)
    self.messages.extend(self.writer.messages)

Accumulating instead would emit every declaration message TWICE. If a
caller ever stops draining between calls, change the caller - not this.
"""

from __future__ import annotations

from converter.composers.counter_declaration import (
    CounterAnchorResolver,
    CounterLineFactory,
    CounterTotalsWriter,
)
from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.counter_declaration_patterns import DATA_ENTRY_PATTERN
from rules.counter_declaration_rules import (
    COUNTER_DECLARATION_MESSAGES,
    COUNTER_DECLARATION_TEMPLATE,
    COUNTER_NAME_PREFIX,
    COUNTER_NAME_SUFFIX,
    COUNTER_PICTURE,
    ENFORCE_COUNTER_NAME_SHAPE,
    ENFORCE_TOTALS_SUBSET_OF_DECLARED,
)


class CounterDeclarationWriter:
    """Writes counter declarations and end-of-run totals."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
        resolver: CounterAnchorResolver | None = None,
        totals_writer: CounterTotalsWriter | None = None,
    ) -> None:
        self.line_factory = CounterLineFactory(
            fixed_format=fixed_format or FixedFormatLineService(),
        )
        self.resolver = resolver or CounterAnchorResolver(
            line_factory=self.line_factory,
        )
        self.totals_writer = totals_writer or CounterTotalsWriter(
            line_factory=self.line_factory,
        )
        self.messages: list[str] = []

        # Names this instance declared on the LAST declare() call.
        # append_totals() may not display anything outside this set
        # plus whatever the program already declares.
        self._declared: list[str] = []

    # ---------------------------------------------------------- public
    def declare(self, lines: list[str], missing: list[str]) -> list[str]:
        self.messages = []
        self._declared = []

        if not missing:
            return lines

        existing = self._declared_names(lines)
        admissible = self._admissible(missing, existing)

        if not admissible:
            # Every candidate was refused. Say so; do not return in
            # silence, which reads identically to "nothing to do".
            return lines

        lines, anchor = self.resolver.resolve(lines)
        self.messages.extend(self.resolver.messages)

        if anchor is None or not anchor.is_usable:
            self.messages.append(
                COUNTER_DECLARATION_MESSAGES["skipped_no_group"].format(
                    count=len(admissible),
                )
            )
            return lines

        block: list[str] = []
        for name in admissible:
            body = anchor.indent + COUNTER_DECLARATION_TEMPLATE.format(
                level=anchor.level,
                name=name,
                picture=COUNTER_PICTURE,
            )
            block.append(
                self.line_factory.statement(anchor.template_line, body)
            )
            self._declared.append(name)
            self.messages.append(
                COUNTER_DECLARATION_MESSAGES["declared"].format(
                    name=name,
                    group=anchor.group,
                )
            )

        index = anchor.insert_index
        return lines[:index] + block + lines[index:]

    def append_totals(
        self,
        lines: list[str],
        counters: list[str],
    ) -> list[str]:
        self.messages = []

        allowed = self._allowed_for_totals(lines, counters)
        if not allowed:
            return lines

        lines = self.totals_writer.append(lines, allowed)
        self.messages.extend(self.totals_writer.messages)
        return lines

    # --------------------------------------------------------- private
    def _admissible(
        self,
        candidates: list[str],
        existing: set[str],
    ) -> list[str]:
        """Candidates this class is willing to declare.

        Two gates, both REFUSING rather than guessing:

        shape      a name that is not WS-NB-<token>-COUNT must not be
                   rendered with COUNTER_PICTURE. Declaring an unknown
                   name as PIC 9(7) COMP-3 is a silent type change.

        duplicate  a name already declared anywhere in the DATA
                   DIVISION must not be declared again. A duplicate
                   data-name is a compile error, and the composer's
                   filter is not the only possible caller.
        """
        admissible: list[str] = []
        seen: set[str] = set()

        for raw in candidates:
            name = str(raw or "").strip().upper()
            if not name or name in seen:
                continue
            seen.add(name)

            if ENFORCE_COUNTER_NAME_SHAPE and not self._is_counter(name):
                self.messages.append(
                    COUNTER_DECLARATION_MESSAGES["refused_shape"].format(
                        name=name,
                        prefix=COUNTER_NAME_PREFIX,
                        suffix=COUNTER_NAME_SUFFIX,
                    )
                )
                continue

            if name in existing:
                self.messages.append(
                    COUNTER_DECLARATION_MESSAGES[
                        "refused_duplicate"
                    ].format(name=name)
                )
                continue

            admissible.append(name)

        return admissible

    def _allowed_for_totals(
        self,
        lines: list[str],
        counters: list[str],
    ) -> list[str]:
        """Names the totals pass may display.

        A total line is a promise that the field is maintained. A
        counter that is never incremented displays zero for the life of
        the program and sends the operator looking for a data problem
        that does not exist.

        The admissible set is therefore what THIS pass declared, union
        what the program already declares. It is never widened by the
        argument alone.
        """
        if not ENFORCE_TOTALS_SUBSET_OF_DECLARED:
            return list(counters)

        known = {n.upper() for n in self._declared}
        known |= self._declared_names(lines)

        allowed: list[str] = []
        for raw in counters:
            name = str(raw or "").strip().upper()
            if not name:
                continue
            if name in known:
                allowed.append(name)
                continue
            self.messages.append(
                COUNTER_DECLARATION_MESSAGES["refused_total"].format(
                    name=name,
                )
            )

        return allowed

    def _declared_names(self, lines: list[str]) -> set[str]:
        """Every data-name declared in the source, upper-cased.

        Read through DATA_ENTRY_PATTERN rather than a substring test:
        a DISPLAY literal mentioning the name is not a declaration.
        """
        names: set[str] = set()

        for line in lines:
            if self.line_factory.is_skippable(line):
                continue
            match = DATA_ENTRY_PATTERN.match(
                self.line_factory.logical(line)
            )
            if match:
                names.add(match.group("name").upper())

        return names

    @staticmethod
    def _is_counter(name: str) -> bool:
        """WS-NB-<token>-COUNT, with a non-empty token."""
        text = str(name or "").strip().upper()
        if not text.startswith(COUNTER_NAME_PREFIX):
            return False
        if not text.endswith(COUNTER_NAME_SUFFIX):
            return False
        token = text[
            len(COUNTER_NAME_PREFIX): -len(COUNTER_NAME_SUFFIX)
        ].strip("-")
        return bool(token)


__all__ = ["CounterDeclarationWriter"]
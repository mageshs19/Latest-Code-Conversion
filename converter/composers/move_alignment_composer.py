# LOCATION: converter/composers/move_alignment_composer.py
# ACTION: CREATE NEW FILE
"""Aligns the TO keyword across runs of MOVE statements.

Three stages, in order:

  1. PARSE   every MOVE into (indent, source, receivers), joining a
             statement that the generator split across two lines.
  2. RUN     group consecutive single-receiver MOVEs at one indent.
  3. RENDER  pad each source to the run's widest, then emit.

Nothing is reordered, added or removed. The only characters this pass
writes are blanks between an existing source and an existing TO.

Every rendered line is width-checked. A run whose aligned form will not
fit columns 8-72 is emitted unaligned and reported, because a truncated
data-name is far worse than an unaligned one.

Sequence areas are borrowed from the line being replaced.
FinalSequenceResequencerService rewrites columns 1-6 and 73-80
afterwards, so borrowed numbers are placeholders.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from rules.move_alignment_rules import (
    BLANK_LINE_BREAKS_RUN,
    ENFORCE_MOVE_ALIGNMENT,
    MAX_ALIGN_PADDING,
    MIN_GAP_BEFORE_TO,
    MIN_RUN_SIZE,
    MOVE_ALIGNMENT_MESSAGES,
    MULTI_RECEIVER_STANDS_ALONE,
    QUOTE_CHARACTERS,
    RECEIVER_OFFSET,
    SENTENCE_TERMINATOR,
    SKIPPABLE_INDICATORS,
    SQL_BLOCK_END,
    SQL_BLOCK_START,
    STATEMENT_OPENERS,
    TOKEN_TO,
    VERB_MOVE,
)

MASK_CHARACTER = "\x00"
BLANK_INDICATOR = " "


@dataclass
class MoveStatement:
    """One MOVE, however many physical lines carried it."""

    indent: str = ""
    source: str = ""
    receivers: list[str] = field(default_factory=list)
    terminator: str = ""
    templates: list[str] = field(default_factory=list)

    @property
    def is_single_receiver(self) -> bool:
        return len(self.receivers) == 1

    @property
    def prefix(self) -> str:
        return f"{self.indent}{VERB_MOVE} {self.source}"


@dataclass
class Passthrough:
    """Any line this pass does not own."""

    line: str = ""


class MoveAlignmentComposer:
    """Aligns TO across runs of MOVE statements."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

    #
    # Public entry point
    #
    def compose(self, text: str) -> str:
        self.messages = []

        if not text or not ENFORCE_MOVE_ALIGNMENT:
            return str(text or "")

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        items, joined = self._parse(lines)
        rendered = self._render(items)

        if joined:
            self.messages.append(
                MOVE_ALIGNMENT_MESSAGES["joined"].format(count=joined)
            )

        return "\n".join(rendered).rstrip() + "\n"

    #
    # Stage 1 - parse
    #
    def _parse(self, lines: list[str]) -> tuple[list, int]:
        items: list = []
        joined = 0
        index = 0
        in_sql = False

        while index < len(lines):
            line = lines[index]
            in_sql = self._track_sql(line, in_sql)

            if in_sql or self._is_skippable(line):
                items.append(Passthrough(line))
                index += 1
                continue

            body = self._body(line)
            if not self._opens_move(body):
                items.append(Passthrough(line))
                index += 1
                continue

            statement, consumed = self._collect(lines, index)
            if statement is None:
                items.append(Passthrough(line))
                index += 1
                continue

            if consumed > 1 and statement.is_single_receiver:
                joined += 1

            items.append(statement)
            index += consumed

        return items, joined

    def _collect(
        self,
        lines: list[str],
        start: int,
    ) -> tuple[MoveStatement | None, int]:
        """Gather one MOVE, following its continuation lines."""
        body = self._body(lines[start])
        indent = self._indent(body)
        collected = body.strip()
        templates = [lines[start]]
        consumed = 1

        # Follow continuations: a line that is not a new statement and
        # not a paragraph header belongs to this MOVE.
        while start + consumed < len(lines):
            nxt = lines[start + consumed]
            if self._is_skippable(nxt):
                break
            if not self.fixed_format.is_fixed_line(nxt):
                break

            follower = self._body(nxt)
            if not follower.strip():
                break
            if self._opens_statement(follower):
                break
            if not self._indent(follower):
                break  # Area A - a paragraph header

            collected = f"{collected} {follower.strip()}"
            templates.append(nxt)
            consumed += 1

            if collected.rstrip().endswith(SENTENCE_TERMINATOR):
                break

        parsed = self._split_move(collected)
        if parsed is None:
            return None, consumed

        source, receivers, terminator = parsed

        return (
            MoveStatement(
                indent=indent,
                source=source,
                receivers=receivers,
                terminator=terminator,
                templates=templates,
            ),
            consumed,
        )

    def _split_move(self, text: str) -> tuple[str, list[str], str] | None:
        """'MOVE a TO b c' -> ('a', ['b', 'c'], '')."""
        body = str(text or "").strip()
        terminator = ""

        if body.endswith(SENTENCE_TERMINATOR):
            body = body[: -len(SENTENCE_TERMINATOR)].rstrip()
            terminator = SENTENCE_TERMINATOR

        masked = self._mask_literals(body)
        tokens = self._tokens(masked)

        if len(tokens) < 4:
            return None
        if tokens[0][0].upper() != VERB_MOVE:
            return None

        to_index = -1
        for position, (word, _start, _end) in enumerate(tokens):
            if position == 0:
                continue
            if word.upper() == TOKEN_TO:
                to_index = position
                break

        if to_index < 2 or to_index == len(tokens) - 1:
            return None

        source_start = tokens[1][1]
        source_end = tokens[to_index - 1][2]
        source = body[source_start:source_end].strip()

        receiver_text = body[tokens[to_index + 1][1]:].strip()
        receivers = self._receivers(receiver_text)

        if not source or not receivers:
            return None

        return source, receivers, terminator

    @staticmethod
    def _receivers(text: str) -> list[str]:
        """Split a receiver list on qualification boundaries.

        'A OF B C OF D' is two receivers. A bare run of names with no
        OF / IN is one receiver per name.
        """
        words = str(text or "").split()
        if not words:
            return []

        receivers: list[str] = []
        current: list[str] = []
        index = 0

        while index < len(words):
            word = words[index]
            upper = word.upper()

            if upper in ("OF", "IN") and current and index + 1 < len(words):
                current.extend([word, words[index + 1]])
                index += 2
                continue

            if current:
                receivers.append(" ".join(current))
            current = [word]
            index += 1

        if current:
            receivers.append(" ".join(current))

        return receivers

    #
    # Stage 2 and 3 - run formation and rendering
    #
    def _render(self, items: list) -> list[str]:
        output: list[str] = []
        runs = 0
        statements = 0
        index = 0

        while index < len(items):
            item = items[index]

            if not isinstance(item, MoveStatement):
                output.append(item.line)
                index += 1
                continue

            run, consumed = self._run_from(items, index)

            if len(run) >= MIN_RUN_SIZE:
                lines = self._render_run(run)
                if lines is not None:
                    output.extend(lines)
                    runs += 1
                    statements += len(run)
                    index += consumed
                    continue

            for statement in run:
                output.extend(self._render_plain(statement))

            index += consumed

        if runs:
            self.messages.append(
                MOVE_ALIGNMENT_MESSAGES["aligned"].format(
                    runs=runs, statements=statements
                )
            )

        return output

    def _run_from(self, items: list, start: int) -> tuple[list, int]:
        """The longest alignable run beginning at `start`."""
        first = items[start]

        if MULTI_RECEIVER_STANDS_ALONE and not first.is_single_receiver:
            return [first], 1

        run = [first]
        consumed = 1

        while start + consumed < len(items):
            candidate = items[start + consumed]

            if isinstance(candidate, Passthrough):
                if BLANK_LINE_BREAKS_RUN and not self._body(
                    candidate.line
                ).strip():
                    break
                # A line at a DIFFERENT indent - WHEN, ELSE, a nested
                # condition - does not interrupt the table.
                if self._interrupts(candidate.line, first.indent):
                    break
                run.append(candidate)
                consumed += 1
                continue

            if candidate.indent != first.indent:
                break
            if not candidate.is_single_receiver:
                break

            run.append(candidate)
            consumed += 1

        while run and isinstance(run[-1], Passthrough):
            run.pop()
            consumed -= 1

        return run, consumed

    def _interrupts(self, line: str, indent: str) -> bool:
        """True when `line` is an executable statement at `indent`."""
        if self._is_skippable(line):
            return False
        body = self._body(line)
        if not body.strip():
            return True
        if self._indent(body) != indent:
            return False
        return self._opens_statement(body)

    def _render_run(self, run: list) -> list[str] | None:
        moves = [item for item in run if isinstance(item, MoveStatement)]
        if len(moves) < MIN_RUN_SIZE:
            return None

        widest = max(len(move.prefix) for move in moves)
        to_column = widest + MIN_GAP_BEFORE_TO

        padding = to_column - min(len(move.prefix) for move in moves)
        if padding > MAX_ALIGN_PADDING:
            self.messages.append(
                MOVE_ALIGNMENT_MESSAGES["refused_padding"].format(
                    padding=padding, limit=MAX_ALIGN_PADDING
                )
            )
            return None

        rendered: list[str] = []

        for item in run:
            if isinstance(item, Passthrough):
                rendered.append(item.line)
                continue

            body = self._aligned_body(item, to_column)
            if not self._fits(body):
                self.messages.append(
                    MOVE_ALIGNMENT_MESSAGES["refused_width"]
                )
                return None

            line = self._clone(item.templates[0], body)
            if line is None:
                return None
            rendered.append(line)

        return rendered

    @staticmethod
    def _aligned_body(move: MoveStatement, to_column: int) -> str:
        return (
            move.prefix.ljust(to_column)
            + f"{TOKEN_TO} {move.receivers[0]}"
            + move.terminator
        )

    def _render_plain(self, move: MoveStatement) -> list[str]:
        """One MOVE, unaligned. Multi-receiver spills to further lines."""
        head = (
            f"{move.prefix} {TOKEN_TO} {move.receivers[0]}"
            + (move.terminator if move.is_single_receiver else "")
        )

        if not self._fits(head):
            return [line for line in move.templates]

        lines: list[str] = []
        first = self._clone(move.templates[0], head)
        if first is None:
            return [line for line in move.templates]
        lines.append(first)

        receiver_column = len(move.prefix) + 1 + RECEIVER_OFFSET

        for position, receiver in enumerate(move.receivers[1:], start=1):
            tail = receiver + (
                move.terminator
                if position == len(move.receivers) - 1
                else ""
            )
            body = " " * receiver_column + tail
            if not self._fits(body):
                return [line for line in move.templates]

            template = (
                move.templates[position]
                if position < len(move.templates)
                else move.templates[-1]
            )
            built = self._clone(template, body)
            if built is None:
                return [line for line in move.templates]
            lines.append(built)

        return lines

    #
    # Helpers
    #
    @staticmethod
    def _mask_literals(text: str) -> str:
        """Blank out quoted literals, preserving length and offsets."""
        out: list[str] = []
        quote = ""

        for character in str(text or ""):
            if quote:
                out.append(MASK_CHARACTER if character != quote else character)
                if character == quote:
                    quote = ""
                continue

            if character in QUOTE_CHARACTERS:
                quote = character
                out.append(character)
                continue

            out.append(character)

        return "".join(out)

    @staticmethod
    def _tokens(text: str) -> list[tuple[str, int, int]]:
        """(word, start, end) for every whitespace-delimited token."""
        tokens: list[tuple[str, int, int]] = []
        start = -1

        for position, character in enumerate(str(text or "")):
            if character.isspace():
                if start >= 0:
                    tokens.append((text[start:position], start, position))
                    start = -1
                continue
            if start < 0:
                start = position

        if start >= 0:
            tokens.append((text[start:], start, len(text)))

        return tokens

    def _opens_move(self, body: str) -> bool:
        words = str(body or "").split()
        return bool(words) and words[0].upper() == VERB_MOVE

    def _opens_statement(self, body: str) -> bool:
        words = str(body or "").split()
        if not words:
            return False
        return words[0].upper().rstrip(SENTENCE_TERMINATOR) in STATEMENT_OPENERS

    def _body(self, line: str) -> str:
        try:
            _left, _indicator, body, _right = self.fixed_format.split(line)
        except Exception:  # noqa: BLE001
            return ""
        return str(body or "").rstrip()

    def _clone(self, template: str, body: str) -> str | None:
        try:
            left, indicator, _old, right = self.fixed_format.split(template)
        except Exception:  # noqa: BLE001
            return None
        return self.fixed_format.build_or_none(
            left, indicator or BLANK_INDICATOR, body, right
        )

    def _fits(self, body: str) -> bool:
        try:
            return bool(self.fixed_format.body_fits(body))
        except Exception:  # noqa: BLE001
            return len(str(body or "")) <= 65

    @staticmethod
    def _indent(body: str) -> str:
        text = str(body or "")
        return text[: len(text) - len(text.lstrip())]

    def _is_skippable(self, line: str) -> bool:
        text = str(line or "")
        if not text.strip():
            return True
        if not self.fixed_format.is_fixed_line(text):
            return True
        indicator = text[6] if len(text) > 6 else " "
        return indicator in SKIPPABLE_INDICATORS

    @staticmethod
    def _track_sql(line: str, in_sql: bool) -> bool:
        upper = str(line or "").upper()
        if SQL_BLOCK_START in upper:
            return True
        if in_sql and SQL_BLOCK_END in upper:
            return False
        return in_sql


__all__ = ["MoveAlignmentComposer", "MoveStatement"]
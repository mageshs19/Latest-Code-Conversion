# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_lrf_scanner.py
# ACTION: REPLACE ENTIRE FILE
"""Reads the generated LRF expansion comments back out of the program.

LrfPathExpander rewrites Logical Record Facility syntax into classic
IDMS and leaves a marker comment behind. This scanner recovers which
records came from an LRF path, so the spec builder can report it.

CORRECTION 1 - the continuation was matched against the RAW record.

    record_match = re.search(r"\\*?\\s+(\\w+)", next_line)

ran on the un-stripped line, so the sequence number was inside the
search space. Every line is reduced to its body first, exactly like
every other scan in this package.

CORRECTION 2 - ONE WRAP SHAPE WAS HANDLED, AND THERE ARE TWO

The marker body occupies columns 8-72, a 65-character window. Where it
wraps depends on the LENGTH OF THE NAMES IN IT, and a single character
changes the shape. VM4BD310 produces BOTH in the same program:

    SHAPE A - 'FIRST' is 5 chars, the arrow will not fit:

        *DB2: Expanded LRF FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF
        *  -> VMBEVEF WITHIN VMBEFF-VMBEVEF.

    SHAPE B - 'NEXT' is 4 chars, the body lands on exactly 65 and the
    arrow is the last token:

        *DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->
        *  VMBEVEF WITHIN VMBEFF-VMBEVEF.

LRF_EXPANSION_WRAPPED_PATTERN describes SHAPE B. Shape A had no
handler, so the FIRST marker was invisible and the record's mode was
recovered from the NEXT marker instead - the prime access and the
advance access became indistinguishable downstream.

Teaching the regex a third physical shape would fail again on the next
record name that is one character longer. The scanner now ASSEMBLES the
marker from its logical bodies and matches the assembled text, so where
the wrap falls stops mattering. The two physical patterns are retained
as a fallback for any shape the join does not cover.

THE DEEPER POINT, recorded so it is not lost: join metadata travels
downstream through a COLUMN-LIMITED COMMENT. Any name long enough to
push the marker past column 72 silently changes the generated SQL. This
fix makes the channel robust; it does not make it a good channel.
"""

from __future__ import annotations

from dataclasses import dataclass

from converter.generators.db2_infrastructure.spec_builder.spec_fixed_format import (
    bodies_of,
)
from converter.services.name_normalizer import NameNormalizer
from patterns.cursor_spec import (
    LRF_CONTINUATION_RECORD_PATTERN,
    LRF_EXPANSION_PATTERN,
    LRF_EXPANSION_WRAPPED_PATTERN,
)

# Head of every expansion marker. Belongs in rules/ beside
# EXPANDED_OBTAIN_TEMPLATE, which is what produces it; kept here while
# this package owns no rules module of its own.
MARKER_HEAD = "EXPANDED LRF"

# The emitter wraps at word boundaries inside a 65-column window, so a
# marker occupies at most this many physical lines. Bounded so a scan
# can never run away across a paragraph.
try:  # pragma: no cover - import-time fallback
    from rules.lrf_conversion_rules import LRF_MARKER_CONTINUATION_LINES
except ImportError:  # pragma: no cover
    LRF_MARKER_CONTINUATION_LINES = 2

JOIN_SEPARATOR = " "


@dataclass(frozen=True)
class LrfCursor:
    """One record reached through an LRF path."""

    record: str = ""
    mode: str = ""
    subschema: str = ""
    sweep_condition: str = ""


class SpecLrfScanner:
    """Recovers LRF expansion markers. Read-only."""

    def cursors(self, cobol_text: str) -> dict[str, LrfCursor]:
        """record name -> LrfCursor. First marker for a record wins."""
        output: dict[str, LrfCursor] = {}
        bodies = bodies_of(cobol_text)

        for index, body in enumerate(bodies):
            if not body:
                continue

            entry = (
                self._single_line(body)
                or self._joined(bodies, index)
                or self._wrapped(bodies, index)
            )
            if entry is None:
                continue

            if entry.record and entry.record not in output:
                output[entry.record] = entry

        return output

    # ---- forms
    @staticmethod
    def _single_line(body: str) -> LrfCursor | None:
        """The marker fitted on one line: arrow and record together."""
        match = LRF_EXPANSION_PATTERN.search(body)
        if not match:
            return None
        return LrfCursor(
            record=NameNormalizer.normalize(match.group("record")),
            mode=match.group("mode").upper(),
            subschema=match.group("subschema").upper(),
            sweep_condition=match.group("sweep").upper(),
        )

    @classmethod
    def _joined(cls, bodies: list[str], index: int) -> LrfCursor | None:
        """Assemble the marker from its logical bodies, then match.

        Wrap-shape independent: whether the arrow ends line 1 or opens
        the continuation, the assembled text reads the same.
        """
        head = bodies[index]
        if MARKER_HEAD not in head.upper():
            return None

        limit = min(index + 1 + LRF_MARKER_CONTINUATION_LINES, len(bodies))
        parts = [head]

        for following in range(index + 1, limit):
            nxt = bodies[following]
            if not nxt:
                break
            # A second marker starts a new record; never absorb it.
            if MARKER_HEAD in nxt.upper():
                break
            parts.append(nxt)

            assembled = JOIN_SEPARATOR.join(parts)
            match = LRF_EXPANSION_PATTERN.search(assembled)
            if match:
                return LrfCursor(
                    record=NameNormalizer.normalize(match.group("record")),
                    mode=match.group("mode").upper(),
                    subschema=match.group("subschema").upper(),
                    sweep_condition=match.group("sweep").upper(),
                )

        return None

    @staticmethod
    def _wrapped(bodies: list[str], index: int) -> LrfCursor | None:
        """Shape B fallback: arrow ends line 1, record opens line 2."""
        match = LRF_EXPANSION_WRAPPED_PATTERN.search(bodies[index])
        if not match or index + 1 >= len(bodies):
            return None

        continuation = LRF_CONTINUATION_RECORD_PATTERN.match(
            bodies[index + 1]
        )
        if not continuation:
            return None

        return LrfCursor(
            record=NameNormalizer.normalize(continuation.group("record")),
            mode=match.group("mode").upper(),
            subschema=match.group("subschema").upper(),
            sweep_condition=match.group("sweep").upper(),
        )


__all__ = ["SpecLrfScanner", "LrfCursor"]
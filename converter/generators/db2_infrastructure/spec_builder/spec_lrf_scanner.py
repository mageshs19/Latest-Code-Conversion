# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_lrf_scanner.py
# ACTION: CREATE NEW FILE
"""Reads the generated LRF expansion comments back out of the program.

LrfPathExpander rewrites Logical Record Facility syntax into classic
IDMS and leaves a marker comment behind. This scanner recovers which
records came from an LRF path, so the spec builder can report it.

CORRECTION - the continuation was matched against the RAW record.

    record_match = re.search(r"\\*?\\s+(\\w+)", next_line)

ran on the un-stripped line, so the sequence number was inside the
search space. It happened to work on '002220*  VMBEVEF' because two
spaces follow the indicator, and would capture the wrong token the
moment a shop wrote '002220*VMBEVEF'. Every line is reduced to its body
first, exactly like every other scan in this package.
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

            entry = self._single_line(body) or self._wrapped(bodies, index)
            if entry is None:
                continue

            if entry.record and entry.record not in output:
                output[entry.record] = entry

        return output

    # ---- forms
    @staticmethod
    def _single_line(body: str) -> LrfCursor | None:
        match = LRF_EXPANSION_PATTERN.search(body)
        if not match:
            return None
        return LrfCursor(
            record=NameNormalizer.normalize(match.group("record")),
            mode=match.group("mode").upper(),
            subschema=match.group("subschema").upper(),
            sweep_condition=match.group("sweep").upper(),
        )

    @staticmethod
    def _wrapped(bodies: list[str], index: int) -> LrfCursor | None:
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
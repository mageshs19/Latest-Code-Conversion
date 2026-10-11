# LOCATION: converter/resolvers/program_kind_resolver.py
# ACTION: CREATE NEW FILE

"""Decides whether a program is an UPDATE program, and says why.

The decision is MEASURED from the source. The conversion input may
promote a program to UPDATE; it may never demote one whose source proves
otherwise.

Measurement happens on the EXPANDED source, before statement
transformation: by the time the converter has run, the write verbs have
been rewritten or commented out and the evidence is gone.

No program, record, table, DCLGEN or host variable name is hardcoded.
"""

from __future__ import annotations

from typing import Any

from patterns.program_kind_patterns import (
    CONVERTED_WRITE_MARKER_PATTERN,
    IDMS_WRITE_LRF_PATTERN,
    IDMS_WRITE_VERB_PATTERN,
    KEEP_WRITE_MARKER_PATTERN,
)
from patterns.sequence_patterns import is_fixed_format_line, logical_body
from rules.program_kind_rules import (
    EVIDENCE_SAMPLE_LIMIT,
    INPUT_MAY_PROMOTE_ONLY,
    KIND_RETRIEVAL,
    KIND_UPDATE,
    MEASURE_KIND_FROM_SOURCE,
    PROGRAM_KIND_MESSAGES,
)

# A commented-out verb still proves the program writes. Detection only.
_MARKER_PATTERNS = (
    CONVERTED_WRITE_MARKER_PATTERN,
    KEEP_WRITE_MARKER_PATTERN,
)

# A live verb. The LRF form is checked first: it is the stricter match.
_VERB_PATTERNS = (
    IDMS_WRITE_LRF_PATTERN,
    IDMS_WRITE_VERB_PATTERN,
)


class ProgramKindResolver:
    """Source text in, program kind out, with evidence."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------
    def resolve(
        self,
        source_text: str,
        input_says_update: Any = None,
    ) -> tuple[str, list[str]]:
        """Return (kind, messages). Never raises."""
        self.messages = []

        declared = self._declared(input_says_update)

        if not MEASURE_KIND_FROM_SOURCE:
            self._say("measurement_disabled")
            return (KIND_UPDATE if declared else KIND_RETRIEVAL), list(
                self.messages
            )

        lines = self._logical_lines(source_text)
        if not lines:
            self._say("empty_source")
            return (KIND_UPDATE if declared else KIND_RETRIEVAL), list(
                self.messages
            )

        evidence = self._write_evidence(lines)

        if evidence:
            self._report_evidence(evidence, len(lines))
            if declared is False:
                self._say("input_disagrees", count=len(evidence))
            return KIND_UPDATE, list(self.messages)

        if declared and INPUT_MAY_PROMOTE_ONLY:
            self._say("promoted_by_input")
            return KIND_UPDATE, list(self.messages)

        self._say("measured_retrieval", lines=len(lines))
        return KIND_RETRIEVAL, list(self.messages)

    def is_update(
        self,
        source_text: str,
        input_says_update: Any = None,
    ) -> tuple[bool, list[str]]:
        kind, messages = self.resolve(source_text, input_says_update)
        return kind == KIND_UPDATE, messages

    # -----------------------------------------------------------------
    # Measurement
    # -----------------------------------------------------------------
    @staticmethod
    def _declared(value: Any) -> bool | None:
        if value is None:
            return None
        return bool(value)

    @staticmethod
    def _logical_lines(source_text: str) -> list[tuple[int, str]]:
        raw = str(source_text or "").replace("\r\n", "\n").replace("\r", "\n")
        out: list[tuple[int, str]] = []
        for number, line in enumerate(raw.split("\n"), start=1):
            body = (
                logical_body(line)
                if is_fixed_format_line(line)
                else line.strip()
            )
            # logical_body() drops the indicator, so a marker comment
            # must be read from the raw line instead.
            candidate = body or str(line).strip()
            if candidate:
                out.append((number, " ".join(candidate.upper().split())))
        return out

    @staticmethod
    def _write_evidence(
        lines: list[tuple[int, str]],
    ) -> list[tuple[int, str]]:
        found: list[tuple[int, str]] = []
        for number, body in lines:
            if any(p.match(body) for p in _MARKER_PATTERNS):
                found.append((number, body))
                continue
            if any(p.match(body) for p in _VERB_PATTERNS):
                found.append((number, body))
        return found

    # -----------------------------------------------------------------
    # Diagnostics
    # -----------------------------------------------------------------
    def _report_evidence(
        self,
        evidence: list[tuple[int, str]],
        examined: int,
    ) -> None:
        self._say("measured_update", count=len(evidence))
        for number, body in evidence[:EVIDENCE_SAMPLE_LIMIT]:
            self._say("evidence", line=number, body=body)

    def _say(self, key: str, **values: Any) -> None:
        template = PROGRAM_KIND_MESSAGES.get(key, "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(template)


__all__ = ["ProgramKindResolver"]
# LOCATION: converter/analyzers/program_flow/flow_write_scanner.py
# ACTION: CREATE NEW FILE
"""Finds output WRITE statements and IDMS update verbs.

CORRECTION 1 - a paragraph header was counted as a write.

    any(upper.startswith(token) for token in WRITE_TOKENS)

matches the PARAGRAPH HEADER

    WRITE-UITRECORD.

because it starts with "WRITE". The record name then came back empty,
so the analysis reported an output write to nowhere. The verb must be a
WHOLE first token.

CORRECTION 2 - IDMS update verbs inflated the output-write count.

STORE, MODIFY and ERASE are IDMS database updates, not output file
writes. They are collected separately so neither number is misleading.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import LogicalLine, OutputWrite
from converter.services.name_normalizer import NameNormalizer
from rules.program_flow_rules import (
    IDMS_WRITE_VERBS,
    STATEMENT_TERMINATOR,
    WRITE_VERBS,
)


class FlowWriteScanner:
    """Separates file writes from IDMS update verbs."""

    def scan(
        self,
        lines: list[LogicalLine],
        paragraph_by_line: dict[int, str],
    ) -> tuple[list[OutputWrite], list[OutputWrite]]:
        writes: list[OutputWrite] = []
        idms_writes: list[OutputWrite] = []

        for line in lines or []:
            if line.is_comment:
                continue

            words = line.upper.split()
            if not words:
                continue

            verb = words[0].rstrip(STATEMENT_TERMINATOR)

            if verb in WRITE_VERBS:
                target = writes
            elif verb in IDMS_WRITE_VERBS:
                target = idms_writes
            else:
                continue

            target.append(
                OutputWrite(
                    output_record=self._operand(words),
                    paragraph_name=paragraph_by_line.get(line.number, ""),
                    write_line=line.number,
                    verb=verb,
                )
            )

        return writes, idms_writes

    @staticmethod
    def _operand(words: list[str]) -> str:
        """The record name after the verb, in COBOL form."""
        if len(words) < 2:
            return ""
        name = words[1].rstrip(STATEMENT_TERMINATOR)
        return NameNormalizer.to_cobol(NameNormalizer.normalize(name))


__all__ = ["FlowWriteScanner"]
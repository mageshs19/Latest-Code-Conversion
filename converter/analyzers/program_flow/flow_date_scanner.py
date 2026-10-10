# LOCATION: converter/analyzers/program_flow/flow_date_scanner.py
# ACTION: CREATE NEW FILE
"""Finds lines that touch a date or timestamp.

CORRECTION - substring matching made the count meaningless.

    any(token in upper for token in DATE_TOKENS)

with DATE in the token set matches:

    UPDATE          <- contains DATE
    CANDIDATE       <- contains DATE
    DATE-WRITTEN    <- a header, not a usage

and "TS-" matched RESULTS-TOTAL. Every UPDATE statement in an update
program was therefore reported as a DB2 date usage.

Matching is now on WHOLE hyphen-delimited tokens, with an explicit
prefix list for the host-field conventions (TS-, DA-, DT-). No regex:
the line is split on its delimiters and the tokens are compared.
"""

from __future__ import annotations

from converter.analyzers.program_flow.flow_models import DateUsage, LogicalLine
from rules.program_flow_rules import (
    DATE_TOKEN_PREFIXES,
    DATE_TOKENS,
    TOKEN_DELIMITERS,
    USAGE_TYPE_DATE_TOKEN,
)


class FlowDateScanner:
    """Reports date/timestamp touches, one entry per line."""

    def usages(self, lines: list[LogicalLine]) -> list[DateUsage]:
        output: list[DateUsage] = []

        for line in lines or []:
            if line.is_comment:
                continue

            token = self._first_date_token(line.upper)
            if not token:
                continue

            output.append(
                DateUsage(
                    host_field=token,
                    line_number=line.number,
                    line_text=line.raw,
                    usage_type=USAGE_TYPE_DATE_TOKEN,
                )
            )

        return output

    @classmethod
    def _first_date_token(cls, upper_body: str) -> str:
        for token in cls._tokens(upper_body):
            if token in DATE_TOKENS:
                return token
            if token.startswith(DATE_TOKEN_PREFIXES):
                return token
        return ""

    @staticmethod
    def _tokens(upper_body: str) -> list[str]:
        """Split on COBOL word delimiters. Hyphens are part of a name."""
        text = str(upper_body or "")
        for delimiter in TOKEN_DELIMITERS:
            text = text.replace(delimiter, " ")
        return [word for word in text.split() if word]


__all__ = ["FlowDateScanner"]
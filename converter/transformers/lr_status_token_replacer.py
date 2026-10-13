# LOCATION: converter/transformers/lr_status_token_replacer.py
# ACTION: REPLACE ENTIRE FILE
"""Turns the DB-REC-FOUND token LrfPathExpander emits into a DB2 condition.

WHY THIS EXISTS

LrfPathExpander rewrites an LR-STATUS literal test into an IDMS status
token, because every downstream pass already understands classic IDMS:

    IF LR-STATUS = 'VMBFAS-EOA'        ->   IF DB-END-OF-SET
    IF LR-STATUS NOT = 'LR-FOUND'      ->   IF NOT DB-REC-FOUND

Of the three tokens it can emit, two already have an owner:

    DB-END-OF-SET        IDMS statement transformer,
    DB-REC-NOT-FOUND     via SQLCODE_END_TOKEN_REPLACEMENT and
                         ON_DB_REC_NOT_FOUND_PATTERN

DB-REC-FOUND has none. It is a CONDITION NAME whose defining copybook
(COPY IDMS SUBSCHEMA-LR-CTRL) is removed by the declarative converter,
so left alone it reaches the compiler undefined and CHK-31 reports it as
residual IDMS. This pass exists for that one token.

SCOPE - why it is not all three
--------------------------------
An earlier version mapped all three. VM4BD420 then logged

    LR-STATUS tokens: replaced 4 IDMS status token(s)

while logging NO "LRF expansion:" line at all. Its source carried, in
classic IDMS, four conditions this pass had no business touching:

    UNTIL DB-END-OF-SET.      (x2)
    IF NOT DB-END-OF-SET
    IF DB-END-OF-SET

This pass runs BEFORE the statement transformer, so claiming those
tokens made it the de-facto owner of a rewrite it was never designed
for. No damage was found on the current program set - LEGACY_EOC_
CONDITIONS accepts both the IDMS and the SQLCODE spelling, and VM4BD420
carries no ON-clause - but a program with

    ON DB-REC-NOT-FOUND MOVE +1 TO SW-X

would have lost it: once the line reads "ON SQLCODE = 100",
ON_DB_REC_NOT_FOUND_PATTERN no longer matches and the IDMS ON clause
survives into the output.

The mapping in rules/ is the single source of scope. This module reads
it and the pattern is built from it, so neither can drift.

NO-TOKEN CONTRACT

A program carrying no DB-REC-FOUND is returned byte-for-byte. This pass
is a no-op on every non-LRF program and on every LRF program whose
status literals resolved to end-of-set or not-found.

POLARITY

The expander already emitted the negation as a separate word:

    NOT DB-REC-FOUND     ->    NOT SQLCODE = 0

This module never inverts anything; it substitutes a token for a
condition and nothing else.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.lrf_program_patterns import (
    LR_STATUS_TOKEN_REPLACEMENT_PATTERN,
)
from rules.lrf_conversion_rules import (
    ENABLE_LR_STATUS_TOKEN_REPLACEMENT,
    LR_STATUS_TOKEN_MESSAGES,
    LR_STATUS_TOKEN_SQLCODE,
    RECORD_FOUND_TOKEN,
)

PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"
COMMENT_INDICATORS = ("*", "/", "D", "-")
DEFAULT_INDENT = "    "


class LrStatusTokenReplacer:
    """Replaces the generated DB-REC-FOUND token with its SQLCODE test."""

    def __init__(
        self,
        *,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

    # ---------------------------------------------------------- public
    def apply(self, cobol_text: str) -> str:
        self.messages = []

        text = str(cobol_text or "")
        if not text.strip() or not ENABLE_LR_STATUS_TOKEN_REPLACEMENT:
            return text

        if not LR_STATUS_TOKEN_REPLACEMENT_PATTERN.search(text):
            return text

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        output: list[str] = []
        in_procedure = False
        replaced = 0
        unmapped: set[str] = set()

        for line in lines:
            logical = self._logical(line)

            if PROCEDURE_DIVISION_TOKEN in logical.upper():
                in_procedure = True
                output.append(line)
                continue

            if not in_procedure or self._is_comment(line) or not logical:
                output.append(line)
                continue

            new_logical, hits, missing = self._replace_tokens(logical)
            unmapped.update(missing)

            if hits and new_logical != logical:
                replaced += hits
                output.append(self._replace_body(line, new_logical))
            else:
                output.append(line)

        # Reported BEFORE the summary so a gap is never buried under a
        # success line.
        for token in sorted(unmapped):
            self.messages.append(
                LR_STATUS_TOKEN_MESSAGES["unmapped"].format(token=token)
            )

        if not replaced:
            self.messages.append(LR_STATUS_TOKEN_MESSAGES["none"])
            return text

        self.messages.append(
            LR_STATUS_TOKEN_MESSAGES["replaced"].format(
                count=replaced,
                token=RECORD_FOUND_TOKEN,
            )
        )
        return "\n".join(output).rstrip() + "\n"

    # --------------------------------------------------------- replace
    @staticmethod
    def _replace_tokens(logical: str) -> tuple[str, int, set[str]]:
        """Substitute every mapped token. An unmapped token is LEFT.

        DEFENSIVE, NOT DEAD. LR_STATUS_TOKEN_REPLACEMENT_PATTERN is built
        FROM the keys of LR_STATUS_TOKEN_SQLCODE, so today a match cannot
        be unmapped. The guard exists for the day someone hand-writes the
        pattern or widens it: deleting an unrecognised token, or guessing
        a condition for it, would hide the gap behind code that compiles.
        """
        hits = 0
        missing: set[str] = set()

        def _replace(match) -> str:
            nonlocal hits

            token = str(match.group("token") or "").upper()
            condition = LR_STATUS_TOKEN_SQLCODE.get(token)

            if condition is None:
                missing.add(token)
                return match.group(0)

            hits += 1
            return condition

        new_logical = LR_STATUS_TOKEN_REPLACEMENT_PATTERN.sub(
            _replace, logical
        )
        return new_logical, hits, missing

    # --------------------------------------------------------- helpers
    def _logical(self, line: str) -> str:
        try:
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:  # noqa: BLE001
            return str(line or "").strip()

    def _is_fixed(self, line: str) -> bool:
        try:
            return bool(self.fixed_format.is_fixed_line(line))
        except Exception:  # noqa: BLE001
            return False

    def _body_indent(self, line: str) -> str:
        if not self._is_fixed(line):
            text = str(line or "")
            return " " * (len(text) - len(text.lstrip(" ")))
        try:
            _l, _i, body, _r = self.fixed_format.split(line)
            return " " * (len(body) - len(body.lstrip(" ")))
        except Exception:  # noqa: BLE001
            return DEFAULT_INDENT

    def _replace_body(self, line: str, new_body: str) -> str:
        indent = self._body_indent(line)
        text = f"{indent}{new_body.strip()}"
        if not self._is_fixed(line):
            return text
        try:
            return self.fixed_format.replace_body(line, text)
        except Exception:  # noqa: BLE001
            return line

    @staticmethod
    def _is_comment(line: str) -> bool:
        text = str(line or "")
        if len(text) >= 7 and text[:6].strip().isdigit():
            return text[6] in COMMENT_INDICATORS
        return text.lstrip().startswith(COMMENT_INDICATORS)


__all__ = ["LrStatusTokenReplacer"]
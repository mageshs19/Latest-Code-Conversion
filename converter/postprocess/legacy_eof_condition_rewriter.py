# LOCATION: converter/postprocess/legacy_eof_condition_rewriter.py
# ACTION: CREATE NEW FILE
"""Point surviving legacy EOF tests at the condition the generator writes.

THE DEFECT THIS PASS EXISTS FOR

VM1BD526 declared ONE end-of-file switch and used it correctly:

    05  SW-EOF  VALUE +0  PIC S9  COMP.
        88 EOF  VALUE +1.
    ...
    AT END MOVE +1 TO SW-EOF.
    PERFORM 200-VERWERK-INFIL UNTIL EOF.
    IF EOF
       PERFORM STOP01.

The restart family then did two things, each correct on its own:

  - replace_legacy_restart_main_flow REGENERATED the mainline, so the
    driving loop came back as UNTIL VMDZ205I-EOF,
  - ensure_read_flat_file REPLACED the reader, which deleted the only
    MOVE into SW-EOF.

What survived was the business text OUTSIDE the replaced region:

    110-POSITIONEREN-INFIL.
        ADD +1 TO TELLER.
        PERFORM 900-LEES-INFIL.
        IF EOF
           PERFORM STOP01.

SW-EOF is now written by nothing, so IF EOF is permanently FALSE. That
branch is the restart-replay guard: when the file ends early during
repositioning the program must abend. It can no longer do so, and a
short input file is processed silently. The program still terminates -
the loop tests the new switch - so this is a DEAD BRANCH, not a hang,
and no compiler will report it.

WHY THIS IS A SEPARATE MODULE

RestartNameResolver was deliberately stopped from deriving names - see
CORRECTION D there - and RestartStorageBuilder owns composition of the
generated identifiers. Neither may reach into business text. The reader
replacement caused the orphan but owns paragraph generation, not
statement rewriting. The capability was already half-built: the legacy
name is resolved by UpdateCobolFileResolver.resolve_legacy_eof_switch,
carried on UpdateProgramContext.legacy_eof_switch, and consumed by
nothing. This module is that missing consumer.

THE LIVE CONDITION IS READ, NEVER RECOMPOSED

<record>-EOF is already composed in two places. Adding a third is the
defect NEW-2 was. The replacement name is taken from the generated
reader's own AT END SET ... TO TRUE, so it cannot disagree with what the
program actually writes.

SCOPED TO THE PROCEDURE DIVISION

Renaming the DATA DIVISION declaration would produce a second
88 VMDZ205I-EOF and the program would not compile. The DATA DIVISION is
never touched; the orphaned declaration is left in place, unreferenced
and harmless.

REFUSAL IS A NORMAL OUTCOME, AND IT IS ALWAYS REPORTED

No legacy name, no generated condition, a legacy name that is still
written, or no occurrence in the procedure - each returns the text
unchanged WITH a reason. A silent return reads identically to success.

No program, record, table, DCLGEN, paragraph or host variable name is
hardcoded. Regex lives in patterns/dynamic_metadata_patterns.py.
"""

from __future__ import annotations

import re

from patterns.dynamic_metadata_patterns import (
    AT_END_SET_TRUE_RE,
    CONDITION_WORD_TEMPLATE,
    PROCEDURE_DIVISION_RE,
    WRITE_TO_NAME_TEMPLATE,
)

BODY_START = 7
BODY_END = 72
BODY_WIDTH = BODY_END - BODY_START


class LegacyEofConditionRewriter:
    """Rewrites surviving legacy EOF condition tests to the live one."""

    def apply(
        self,
        text: str,
        *,
        legacy_condition: str,
        diagnostics: list[str] | None = None,
    ) -> str:
        if not text:
            return text or ""

        legacy = str(legacy_condition or "").strip().upper()

        if not legacy:
            self._say(
                diagnostics,
                "Legacy EOF: no legacy condition was resolved; "
                "nothing to rewrite.",
            )
            return text

        live = self._live_condition(text)

        if not live:
            self._say(
                diagnostics,
                f"Legacy EOF: '{legacy}' survives, but the generated "
                "reader declares no AT END SET ... TO TRUE, so the live "
                "condition could not be read. Left unchanged.",
            )
            return text

        if live == legacy:
            self._say(
                diagnostics,
                f"Legacy EOF: '{legacy}' is already the condition the "
                "reader writes; nothing to rewrite.",
            )
            return text

        if self._is_written(text, legacy):
            self._say(
                diagnostics,
                f"Legacy EOF: '{legacy}' is still written by a MOVE or "
                "SET, so it is live. Left unchanged.",
            )
            return text

        return self._rewrite(
            text=text,
            legacy=legacy,
            live=live,
            diagnostics=diagnostics,
        )

    #
    # Rewrite
    #
    def _rewrite(
        self,
        *,
        text: str,
        legacy: str,
        live: str,
        diagnostics: list[str] | None,
    ) -> str:
        pattern = re.compile(
            CONDITION_WORD_TEMPLATE.format(name=re.escape(legacy)),
            flags=re.IGNORECASE,
        )

        lines = (
            str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
        )

        output: list[str] = []
        in_procedure = False
        changed = 0
        refused = 0

        for line in lines:
            if self._is_comment_or_debug(line):
                output.append(line)
                continue

            body = self._body(line)

            if not in_procedure:
                if PROCEDURE_DIVISION_RE.match(body):
                    in_procedure = True
                output.append(line)
                continue

            new_body, count = pattern.subn(live, body)

            if not count:
                output.append(line)
                continue

            if len(new_body.rstrip()) > BODY_WIDTH:
                refused += 1
                output.append(line)
                continue

            changed += count
            output.append(self._replace_body(line, new_body))

        if changed:
            self._say(
                diagnostics,
                f"Legacy EOF: rewrote {changed} reference(s) to "
                f"'{legacy}' as '{live}' in the PROCEDURE DIVISION. The "
                "generated reader writes the latter; the former was "
                "left unwritten when the legacy reader was replaced.",
            )
        else:
            self._say(
                diagnostics,
                f"Legacy EOF: '{legacy}' is not referenced in the "
                "PROCEDURE DIVISION; nothing to rewrite.",
            )

        if refused:
            self._say(
                diagnostics,
                f"Legacy EOF: {refused} line(s) would exceed column "
                f"{BODY_END} after the rename and were left unchanged. "
                "They still test a condition nothing writes.",
            )

        return "\n".join(output)

    #
    # Reading the program
    #
    @staticmethod
    def _live_condition(text: str) -> str:
        match = AT_END_SET_TRUE_RE.search(str(text or ""))
        return match.group("name").strip().upper() if match else ""

    @staticmethod
    def _is_written(text: str, name: str) -> bool:
        pattern = re.compile(
            WRITE_TO_NAME_TEMPLATE.format(name=re.escape(name)),
            flags=re.IGNORECASE,
        )
        return bool(pattern.search(str(text or "")))

    #
    # Fixed-format helpers
    #
    @staticmethod
    def _is_comment_or_debug(line: str) -> bool:
        text = str(line or "").rstrip("\n")

        if len(text) >= 7 and text[:6].strip().isdigit():
            return text[6:7] in {"*", "/", "D", "d"}

        stripped = text.strip()

        return (
            stripped.startswith("*")
            or stripped.startswith("/")
            or stripped.upper().startswith("D ")
        )

    @staticmethod
    def _body(line: str) -> str:
        text = str(line or "").rstrip("\n")

        if len(text) >= BODY_END and text[:6].strip().isdigit():
            return text[BODY_START:BODY_END].rstrip()

        if len(text) > BODY_START and text[:6].strip().isdigit():
            body = text[BODY_START:]

            if len(body) >= 8 and body[-8:].strip().isdigit():
                body = body[:-8]

            return body.rstrip()

        return text.rstrip()

    @staticmethod
    def _replace_body(line: str, body: str) -> str:
        text = str(line or "").rstrip("\n")
        clean = str(body or "")[:BODY_WIDTH].ljust(BODY_WIDTH)

        if len(text) >= BODY_END and text[:6].strip().isdigit():
            left = text[:6]
            right = text[BODY_END:80] if len(text) >= 80 else ""
            return f"{left} {clean}{right}"

        if len(text) > 6 and text[:6].strip().isdigit():
            return f"{text[:6]} {clean.rstrip()}"

        return clean.rstrip()

    @staticmethod
    def _say(diagnostics: list[str] | None, message: str) -> None:
        if diagnostics is not None:
            diagnostics.append(message)


__all__ = ["LegacyEofConditionRewriter"]
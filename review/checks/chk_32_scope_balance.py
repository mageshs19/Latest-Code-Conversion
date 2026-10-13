"""CHK-32 Scope terminator balance.

Every IF and EVALUATE opened inside a paragraph must be closed inside the
same paragraph, and no END-IF / END-EVALUATE may appear with nothing open.

WHY THIS CHECK EXISTS

VMDZ1567 was generated with

    002390     .
    002400     END-IF.          <- nothing is open
    002460     IF WS-TELLER > 99 ... END-IF.

The restart injector removed the legacy commit test IF and its body but
left the terminator behind. The compiler rejects the program, and the
review accepted it, because every existing check inspects geometry,
statements or SQL -- none walks scope depth.

Conservative by design: only IF and EVALUATE are counted. PERFORM, READ
and STRING have OPTIONAL scope terminators, so counting them would drift
the depth positive and let a genuine orphan through.
"""

from __future__ import annotations

from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std

# Verbs whose scope terminator is MANDATORY once the scope is opened.
SCOPED_VERBS = ("IF", "EVALUATE")

ORPHAN_NOTE = "{terminator} closes a scope that was never opened"
UNCLOSED_NOTE = "{paragraph} ends with {count} unclosed {verb} scope(s)"


class ScopeBalanceCheck(Check):
    CHECK_ID = "CHK-32"
    TITLE = "Scope terminator balance (IF / EVALUATE)"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 320

    def review(self, ctx, view, record) -> None:
        orphans, unclosed = self._walk(view)

        record.expect_all(
            "01",
            "No END-IF or END-EVALUATE without a matching opener",
            [
                f"line {line.number}: "
                + ORPHAN_NOTE.format(terminator=terminator)
                for line, terminator in orphans
            ],
        )

        record.expect_all(
            "02",
            "Every paragraph closes every scope it opens",
            [
                UNCLOSED_NOTE.format(
                    paragraph=paragraph, count=count, verb=verb,
                )
                for paragraph, verb, count in unclosed
            ],
        )

    # ---- walk ------------------------------------------------------------
    def _walk(self, view):
        """One pass over the PROCEDURE DIVISION, depth per paragraph."""
        orphans = []
        unclosed = []

        paragraph = ""
        depth = {verb: 0 for verb in SCOPED_VERBS}

        for line in view.lines:
            body = self._body(line)
            if not body:
                continue

            if self._is_paragraph_header(body):
                unclosed.extend(self._drain(paragraph, depth))
                paragraph = body.rstrip(".")
                depth = {verb: 0 for verb in SCOPED_VERBS}
                continue

            verb = self._opens(body)
            if verb:
                depth[verb] += 1
                continue

            verb = self._closes(body)
            if not verb:
                continue
            if depth[verb] <= 0:
                orphans.append((line, f"END-{verb}"))
            else:
                depth[verb] -= 1

        unclosed.extend(self._drain(paragraph, depth))
        return orphans, unclosed

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _body(line) -> str:
        """The logical body, uppercased, comments and blanks dropped."""
        text = str(getattr(line, "logical", "") or "").strip().upper()
        return " ".join(text.split())

    @staticmethod
    def _opens(body: str) -> str:
        for verb in SCOPED_VERBS:
            if body == verb or body.startswith(verb + " "):
                return verb
        return ""

    @staticmethod
    def _closes(body: str) -> str:
        bare = body.rstrip(".").strip()
        for verb in SCOPED_VERBS:
            if bare == f"END-{verb}":
                return verb
        return ""

    @staticmethod
    def _is_paragraph_header(body: str) -> bool:
        if not body.endswith("."):
            return False
        word = body.rstrip(".").strip()
        if not word or " " in word:
            return False
        if word in std.NON_PARAGRAPH_WORDS:
            return False
        return word[0].isalnum()

    @staticmethod
    def _drain(paragraph: str, depth: dict) -> list:
        if not paragraph:
            return []
        return [
            (paragraph, verb, count)
            for verb, count in sorted(depth.items())
            if count > 0
        ]
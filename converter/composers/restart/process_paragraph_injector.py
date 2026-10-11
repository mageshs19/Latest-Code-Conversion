# LOCATION: converter/composers/restart/process_paragraph_injector.py
# ACTION: REPLACE ENTIRE FILE
"""Repairs the business processing paragraph of an update program.

FIVE THINGS IT DOES, IN ORDER

    1. remove a per-record inline COMMIT
    2. remove an orphan scope terminator
    3. refuse to act twice
    4. remove a trailing reader PERFORM the tail is about to re-supply
    5. append the commit test and the tail read

CORRECTION 1 - the paragraph was read as LOGICAL TEXT

    _logical() was " ".join(line.upper().split()) - no sequence area
    stripped, no indicator column read. Every fixture in the M7 tests is
    a bare statement, so the suite was green while production saw:

        "002550 EXEC SQL 02550000"   -> no EXEC SQL match
        "002580 END-IF. 02580000"    -> no orphan match
        "002610 PERFORM READ... 026" -> no tail match

    All three passes therefore did nothing to a real program. The line
    utility is now a collaborator, defaulted so every existing caller
    keeps working.

CORRECTION 2 - the tail read was duplicated

    _already_injected() compares the WHOLE tail. A paragraph that
    already ended with a bare

        PERFORM <reader>.

    matched nothing, so the tail was appended beside it and the reader
    ran TWICE per iteration - every second input record skipped. That is
    silent data loss, not a layout defect.

CORRECTION 3 - the orphan pass ran BEFORE the COMMIT pass

    A real orphan survived pass 1 and was removed on pass 2. The only
    difference between the passes was the COMMIT block sitting between
    the last balanced terminator and the orphan:

        END-EVALUATE
        .
        EXEC SQL        <- present on pass 1, gone by pass 2
        COMMIT
        END-EXEC.
        END-IF.         <- the orphan

    Scope depth must be counted over the lines that will REMAIN. The
    COMMIT block is on its way out, so it is removed first and the
    orphan pass reasons about the final shape of the paragraph. Needing
    two passes to converge is itself the evidence the order was wrong:
    one pass over settled text is the contract.

CONSERVATIVE BY DESIGN

Orphan detection covers IF and EVALUATE only. PERFORM and READ have
optional scope terminators, so counting them would make the depth drift
positive and let a genuine orphan through.

An EXEC SQL block is removed only when its sole statement is COMMIT.
Anything else is business SQL.

EVERY DECISION IS REPORTED

A terminator that is KEPT now reports the depth that justified keeping
it. A pass that silently retains a line cannot be reviewed, and that
silence is what made CORRECTION 3 take three runs to find.

IDEMPOTENT

Running twice does not append two tails.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Constants live in rules/, regex in patterns/.
"""

from __future__ import annotations

from converter.composers.restart.restart_line_utils import RestartLineUtils
from converter.generators.restart.restart_config import RestartConfig
from patterns.restart_patterns import ORPHAN_SCOPE_TERMINATOR_PATTERN
from rules.restart_standard_rules import COMMIT_BLOCK_SCAN_LIMIT
from rules.restart_statement_templates import PROCESS_TAIL_TEMPLATE

# Verbs whose scope terminator is MANDATORY once the scope is opened.
# PERFORM and READ are deliberately excluded - see the module docstring.
SCOPED_VERBS = ("IF", "EVALUATE")

EXEC_SQL_OPEN = "EXEC SQL"
EXEC_SQL_CLOSE = "END-EXEC"
COMMIT_VERB = "COMMIT"
PERFORM_VERB = "PERFORM"
PERIOD = "."


class ProcessParagraphInjector:
    """Cleans and completes the business processing paragraph."""

    def __init__(self, config: RestartConfig, line_utils=None) -> None:
        self.config = config
        # Defaulted so every existing caller keeps working, but NEVER
        # absent: without it this pass silently does nothing to a real
        # fixed-format program.
        self.line_utils = line_utils or RestartLineUtils()
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def inject(self, lines: list[str]) -> list[str]:
        """Return the repaired paragraph body."""
        self.messages = []

        if not self.config.is_usable():
            for name in self.config.missing():
                self.messages.append(
                    f"Process paragraph: {name} unresolved; "
                    "paragraph left unchanged."
                )
            return list(lines or [])

        # COMMIT removal FIRST - see CORRECTION 3. The orphan pass counts
        # scope depth over the lines that will remain, so it must not be
        # asked to reason about a block that is on its way out.
        body = self._strip_inline_commit(list(lines or []))
        body = self._strip_emptied_scopes(body)
        body = self._strip_orphan_terminators(body)

        tail = self.tail()
        if self._already_injected(body, tail):
            self.messages.append(
                "Process paragraph: the commit test and tail read are "
                "already present; nothing appended."
            )
            return body

        body = self._strip_tail_read(body)

        self.messages.append(
            "Process paragraph: appended the commit test and the tail "
            f"PERFORM {self.config.names.read_paragraph}."
        )
        return body + [""] + list(tail)

    def tail(self) -> tuple[str, ...]:
        """The commit test and the tail read, rendered."""
        values = self.config.placeholders()
        return tuple(line.format(**values) for line in PROCESS_TAIL_TEMPLATE)

    # -----------------------------------------------------------------
    # 1. Per-record inline COMMIT
    # -----------------------------------------------------------------

    def _strip_inline_commit(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        index = 0
        removed = 0

        while index < len(lines):
            span = self._commit_block_span(lines, index)
            if span is None:
                out.append(lines[index])
                index += 1
                continue
            index = span
            removed += 1

        if removed:
            self.messages.append(
                f"Process paragraph: removed {removed} per-record COMMIT "
                "block; the checkpoint paragraph owns the unit of work."
            )
        return out

    def _commit_block_span(self, lines: list[str], start: int) -> int | None:
        """Index after a bare COMMIT block starting at `start`, else None."""
        logical = self._logical(lines[start])

        if not logical.startswith(EXEC_SQL_OPEN):
            return None

        # One-line form: EXEC SQL COMMIT END-EXEC.
        tokens = logical.replace(PERIOD, " ").split()
        if EXEC_SQL_CLOSE in tokens:
            return start + 1 if COMMIT_VERB in tokens else None

        # Split form. Only a block whose sole statement is COMMIT.
        statements: list[str] = []
        limit = min(len(lines), start + 1 + COMMIT_BLOCK_SCAN_LIMIT)

        for cursor in range(start + 1, limit):
            inner = self._logical(lines[cursor])
            if not inner:
                continue
            if inner.startswith(EXEC_SQL_CLOSE):
                if statements == [COMMIT_VERB]:
                    return cursor + 1
                return None
            statements.append(inner.rstrip(PERIOD))

        return None

    # -----------------------------------------------------------------
    # 1b. Scopes this pass emptied
    # -----------------------------------------------------------------

    def _strip_emptied_scopes(self, lines: list[str]) -> list[str]:
        """Remove an IF / EVALUATE whose body this pass just deleted.

        The legacy cadence control wraps the per-record COMMIT:

            IF <legacy counter> > <n>
                EXEC SQL COMMIT END-EXEC.
            END-IF.

        _strip_inline_commit takes the three COMMIT lines and leaves an
        opener against its own terminator. An empty IF does not compile,
        and a later pass deleting the dead opener WITHOUT its terminator
        is what produced an orphan END-IF in generated output.

        Opener and terminator are therefore removed TOGETHER. The test
        is structural - nothing between them - so no counter name is
        needed and no legitimate statement can be caught: a scope with a
        body is never touched.
        """
        out: list[str] = []
        index = 0
        removed = 0

        while index < len(lines):
            closer = self._emptied_scope_end(lines, index)
            if closer is None:
                out.append(lines[index])
                index += 1
                continue
            index = closer + 1
            removed += 1

        if removed:
            self.messages.append(
                f"Process paragraph: removed {removed} scope(s) left empty "
                "by the COMMIT removal; an empty IF does not compile and a "
                "half-removed one orphans its terminator."
            )
        return out

    def _emptied_scope_end(self, lines: list[str], start: int) -> int | None:
        """Index of the terminator closing an EMPTY scope at `start`."""
        logical = self._logical(lines[start])
        tokens = logical.replace(PERIOD, " ").split()
        if not tokens or tokens[0] not in SCOPED_VERBS:
            return None

        terminator = f"END-{tokens[0]}"
        for cursor in range(start + 1, len(lines)):
            inner = self._logical(lines[cursor])
            if not inner:
                continue
            if inner.rstrip(PERIOD) == terminator:
                return cursor
            return None

        return None
    # -----------------------------------------------------------------
    # 2. Orphan scope terminators
    # -----------------------------------------------------------------

    def _strip_orphan_terminators(self, lines: list[str]) -> list[str]:
        depth = {verb: 0 for verb in SCOPED_VERBS}
        out: list[str] = []

        for line in lines:
            logical = self._logical(line)
            match = ORPHAN_SCOPE_TERMINATOR_PATTERN.match(logical)

            if match:
                verb = match.group("verb").upper()
                if verb not in depth:
                    self.messages.append(
                        f"Process paragraph: END-{verb} not tracked; "
                        "left unchanged."
                    )
                    out.append(line)
                    continue
                if depth[verb] <= 0:
                    self.messages.append(
                        f"Process paragraph: removed an orphan END-{verb}; "
                        "it had no matching opener."
                    )
                    continue
                self.messages.append(
                    f"Process paragraph: kept END-{verb}; "
                    f"{depth[verb]} scope(s) were open before it."
                )
                depth[verb] -= 1
                out.append(line)
                continue

            self._track(logical, depth)
            out.append(line)

        return out

    @staticmethod
    def _track(logical: str, depth: dict[str, int]) -> None:
        """Count openers only.

        Closers are handled by the pattern branch, which returns before
        reaching here. Counting them in both places let a real orphan
        look balanced: the branch decremented, then this method
        decremented again on a later line that merely MENTIONED the
        terminator, and the depth drifted positive.

        An opener STARTS the statement. "IF" appearing mid-line is part
        of a condition, not a new scope, so tokens.count() was wrong as
        well as doubled.
        """
        tokens = logical.replace(PERIOD, " ").split()
        if not tokens:
            return
        for verb in SCOPED_VERBS:
            if tokens[0] == verb:
                depth[verb] += 1

    # -----------------------------------------------------------------
    # 3. Idempotency
    # -----------------------------------------------------------------

    def _already_injected(
        self,
        body: list[str],
        tail: tuple[str, ...],
    ) -> bool:
        wanted = [self._logical(line) for line in tail if line.strip()]
        present = [
            self._logical(line) for line in body if self._logical(line)
        ]
        if not wanted or len(present) < len(wanted):
            return False
        return present[-len(wanted):] == wanted

    # -----------------------------------------------------------------
    # 4. The reader PERFORM the tail is about to re-supply
    # -----------------------------------------------------------------

    def _strip_tail_read(self, body: list[str]) -> list[str]:
        """Drop a trailing bare PERFORM of the reader.

        Only the LAST executable line is considered: a PERFORM of the
        reader in the MIDDLE of the paragraph is business logic and is
        left alone.
        """
        target = self._reader_perform()
        if not target:
            return body

        for index in range(len(body) - 1, -1, -1):
            logical = self._logical(body[index])
            if not logical:
                continue
            if logical.rstrip(PERIOD) != target:
                return body
            self.messages.append(
                "Process paragraph: removed the existing trailing "
                f"{target}; the appended tail supplies it. Leaving both "
                "would read two records per iteration."
            )
            return body[:index] + body[index + 1:]

        return body

    def _reader_perform(self) -> str:
        reader = str(self.config.names.read_paragraph or "").strip().upper()
        return f"{PERFORM_VERB} {reader}" if reader else ""

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    def _logical(self, line: str) -> str:
        """Columns 8-72, uppercased, whitespace collapsed.

        Routed through the shared line utility: a fixed-format record
        read as raw text matches none of this module's patterns.
        """
        body = str(self.line_utils.logical(line) or "")
        if self.line_utils.is_comment(body):
            return ""
        return " ".join(body.upper().split())


__all__ = [
    "ProcessParagraphInjector",
    "SCOPED_VERBS",
]
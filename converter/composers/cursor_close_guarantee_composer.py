# LOCATION: converter/composers/cursor_close_guarantee_composer.py
# ACTION: REPLACE ENTIRE FILE

"""Guarantees that every generated cursor is looped, driven and closed.

Runs AFTER CursorFlowComposer. A no-op for any cursor the INLINE or SPAN
strategy already handled, and a last-resort repair for every cursor they
could not correlate.

WHY THIS EXISTS
---------------
CursorFlowComposer recognises two driving-loop idioms. An LRF-expanded
program matches neither, so the program shipped as:

    PERFORM 710-OPEN-DZBFASC1.
    PERFORM 720-FETCH-DZBFASC1.        <- primes once, never loops
    ...
 BEHANDELING.
    PERFORM 720-FETCH-DZBFASC1.        <- orphan repeat fetch

with 730-CLOSE-DZBFASC1 declared but never performed and the FETCH
paragraph carrying WHEN ZERO / CONTINUE. The cursor is opened, read
twice, leaked, and no fetched row is ever processed. Required shape:

    PERFORM 710-OPEN-DZBFASC1.
    PERFORM 720-FETCH-DZBFASC1 UNTIL DZBFASC1-EOC.
    PERFORM 730-CLOSE-DZBFASC1.

with the FETCH paragraph driving the business paragraph:

    EVALUATE SQLCODE
      WHEN ZERO
           PERFORM BEHANDELING THRU BEHANDELING-EXIT

CORRECTION 1 - WHEN ZERO BINDING WAS PATH-DEPENDENT
----------------------------------------------------
bind_fetch_to_business was reachable only from CursorRepair.synthesise_loop,
which runs on Path C alone. A cursor that already had a driving loop took
Path A or B, both of which deliberately never touch the business
paragraph, so the FETCH kept CONTINUE and the business paragraph became
UNREACHABLE. The program fetched every row and wrote nothing. Nothing was
logged either, because business_paragraph_unknown was also raised only
inside the synthesiser.

Binding now happens ONCE, before path selection - EXCEPT on Path D.
See CORRECTION 2.

CORRECTION 2 - A FOURTH LOOP IDIOM REACHED PATH C AND WAS DESTROYED
---------------------------------------------------------------------
An LRF-expanded program drives its cursor with the loop it already had::

    PERFORM 710-OPEN-DZEVEFC1.
    PERFORM 720-FETCH-DZEVEFC1.            <- priming, correct
    ...
    PERFORM UNTIL SQLCODE = 100
               OR CT-EVENT OF VMBEVEF = '0092'
       PERFORM 720-FETCH-DZEVEFC1          <- the advance, correct
    END-PERFORM.

Both fetches are correct and nothing needs restructuring - only the
CLOSE is missing. But:

  * Path A tests the fetch PERFORM itself for UNTIL. The in-loop fetch
    is a BARE PERFORM; the UNTIL belongs to the enclosing block, so
    ``has_until`` is False and Path A is missed.
  * Path B tests for a loop driving a business PARAGRAPH. This loop
    drives the FETCH paragraph, so Path B is missed.
  * Path C therefore concluded "no loop at all", ``_repeat_fetches``
    classified the in-loop fetch as an ORPHAN REPEAT, synthesise_loop
    DELETED it, and rewrote the priming fetch into
    ``PERFORM 720-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC``.

The result::

    PERFORM 720-FETCH-DZEVEFC1 UNTIL DZEVEFC1-EOC.   <- drains the cursor
    PERFORM 730-CLOSE-DZEVEFC1.                      <- closes immediately
    ...
    PERFORM UNTIL SQLCODE = 100
               OR CT-EVENT OF VMBEVEF = '0092'.
    END-PERFORM.                                     <- EMPTY BODY

An empty loop whose condition nothing can change is an INFINITE LOOP at
run time. It compiles. It passes every static check. And the stray
period on the condition line is a second-order effect: once the body is
empty the sentence is unterminated, so the terminator pass punctuates
it and orphans the END-PERFORM.

PATH D recognises this shape and does the ONE thing that is missing -
guarantees the CLOSE after END-PERFORM. It touches nothing else.

PATH D IS CHECKED FIRST, BEFORE BINDING, for a second reason. The
program already performs its business paragraph from the mainline::

    PERFORM SEARCH-MUTATIES.
    PERFORM MOVE-MUTATIES.          <- driving edge 1

Binding WHEN ZERO -> PERFORM MOVE-MUTATIES would add a SECOND driving
edge. COBOL PERFORM holds one return address per paragraph, so the pair
can loop forever. Path D therefore suppresses binding and says so.

THE LOOP CONDITION IS NEVER REWRITTEN ON PATH D. Normalising it to
<cursor>-EOC would DELETE the program's own business exit - here
``OR CT-EVENT OF VMBEVEF = '0092'`` - and the loop would run to end of
set instead of stopping at the row the program wants.

FOUR REPAIR PATHS
-----------------
D. The fetch sits inside an inline PERFORM UNTIL ... END-PERFORM block
   -> the program already drives it. Guarantee the CLOSE, bind nothing,
   rewrite nothing. CHECKED FIRST.

A. A fetch PERFORM already carries UNTIL -> INLINE already ran.
   Normalise a legacy exit condition and guarantee the CLOSE.

B. A business loop drives the paragraph that held the OBTAIN NEXT
   -> SPAN shape. Normalise its exit condition and guarantee the CLOSE.
   The in-loop fetch is REQUIRED here and is never removed.

C. No loop at all -> synthesise the shape and remove the orphan repeat
   fetch.

RESPONSIBILITY
--------------
This class owns PATH SELECTION and nothing else:

    cursor_guarantee/cursor_models.py                regex, value objects, log
    cursor_guarantee/cursor_lines.py                 logical lines, paragraphs
    cursor_guarantee/cursor_scanner.py               discovery, read-only
    cursor_guarantee/cursor_repair.py                every mutation
    cursor_guarantee/business_paragraph_resolver.py  business paragraph, read-only

Path D's block detection is a LITERAL test on logical bodies, not a
regex, and it is self-contained here: it needs only "does this logical
line open an inline PERFORM block" and "does this one close it", which
no collaborator exposes today.

Concrete module imports, not the package: a stale or partially updated
__init__.py then cannot break this composer, which is precisely the
failure mode that produced

    ImportError: cannot import name 'CONTINUE_PATTERN' from partially
    initialized module 'patterns.cursor_close_guarantee_patterns'

No program, paragraph, record, table, cursor or host variable name is
hardcoded here.
"""

from __future__ import annotations

from converter.composers.cursor_guarantee.business_paragraph_resolver import (
    BusinessParagraphResolver,
)
from converter.composers.cursor_guarantee.cursor_lines import CursorLines
from converter.composers.cursor_guarantee.cursor_models import (
    CursorParagraphSet,
    CursorPerform,
    MessageLog,
)
from converter.composers.cursor_guarantee.cursor_repair import CursorRepair
from converter.composers.cursor_guarantee.cursor_scanner import CursorScanner
from rules.cursor_close_guarantee_rules import (
    ENFORCE_CURSOR_CLOSE_GUARANTEE,
    ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH,
    EOC_CONDITION_TEMPLATE,
    OPERATION_CLOSE,
    OPERATION_FETCH,
    OPERATION_OPEN,
    SYNTHESISE_MISSING_DRIVING_LOOP,
)

# Kill switch for Path D, for bisection. Defensive import so this module
# loads before the constant is added to rules/.
try:  # pragma: no cover - import-time fallback
    from rules.cursor_close_guarantee_rules import (
        RECOGNISE_INLINE_BLOCK_DRIVEN_CURSOR,
    )
except ImportError:  # pragma: no cover
    RECOGNISE_INLINE_BLOCK_DRIVEN_CURSOR = True

# Tokens for Path D's block detection. Literal COBOL vocabulary, not
# program data; they belong in rules/ once that module owns the inline
# block vocabulary.
TOKEN_PERFORM = "PERFORM"
TOKEN_UNTIL = "UNTIL"
TOKEN_END_PERFORM = "END-PERFORM"
SENTENCE_TERMINATOR = "."

UNMAPPED_DIAGNOSTIC_TEMPLATE = (
    "Cursor close guarantee: unmapped diagnostic '{key}' {values}"
)


class CursorCloseGuaranteeComposer:
    """Last-resort guarantee that a generated cursor loops and closes."""

    def __init__(self, line_formatter=None) -> None:
        self.log = MessageLog()
        self.lines_utils = CursorLines(line_formatter=line_formatter)
        self.scanner = CursorScanner(lines_utils=self.lines_utils)
        self.repair = CursorRepair(
            lines_utils=self.lines_utils,
            log=self.log,
        )
        # Business-paragraph resolution is needed on EVERY repair path, not
        # only on synthesis, so the composer owns it. It shares the one
        # MessageLog, per the cursor_models.py contract.
        self.business_resolver = BusinessParagraphResolver(
            lines_utils=self.lines_utils,
            log=self.log,
        )

    #
    # conversion_pipeline drains this after compose()
    #
    @property
    def messages(self) -> list[str]:
        return self.log.messages

    # =================================================================
    # Public entry point
    # =================================================================
    def compose(self, text: str) -> str:
        self.log.reset()

        if not text:
            return ""

        if not ENFORCE_CURSOR_CLOSE_GUARANTEE:
            return str(text)

        lines = self.lines_utils.normalize_line_endings(text).splitlines()

        if not lines:
            return ""

        cursor_sets = self.scanner.paragraph_sets(lines)

        # A program with no generated cursor is a legitimate outcome, but
        # it must be distinguishable from a pass that did not run at all.
        if not cursor_sets:
            self._report("no_cursor_paragraphs")
            return "\n".join(lines).rstrip() + "\n"

        for cursor in sorted(cursor_sets):
            cursor_set = cursor_sets[cursor]

            if not cursor_set.is_complete:
                self._report("incomplete_paragraph_set", cursor=cursor)
                continue

            lines = self._repair_cursor(lines, cursor_set)

        return "\n".join(lines).rstrip() + "\n"

    # =================================================================
    # Path selection
    # =================================================================
    def _repair_cursor(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
    ) -> list[str]:
        cursor = cursor_set.cursor
        eoc_condition = EOC_CONDITION_TEMPLATE.format(cursor=cursor)
        performs = self.scanner.performs(lines, cursor)
        opens = self.scanner.by_operation(performs, OPERATION_OPEN)

        if not opens:
            self._report("no_open_perform", cursor=cursor)
            return lines

        fetches = self.scanner.by_operation(performs, OPERATION_FETCH)
        closes = self.scanner.by_operation(performs, OPERATION_CLOSE)

        # ---- Path D: the program already drives this cursor from an
        # inline PERFORM UNTIL ... END-PERFORM block.
        #
        # CHECKED FIRST, and BEFORE binding. See CORRECTION 2: binding
        # here would give the business paragraph a second driving edge.
        span = self._inline_block_span(lines, fetches)

        if span is not None:
            start, end = span
            self._report(
                "inline_loop_found",
                cursor=cursor,
                line=start + 1,
            )
            self._report("inline_loop_business_not_bound", cursor=cursor)
            return self.repair.guarantee_close(
                lines=lines,
                after_index=end,
                cursor_set=cursor_set,
                close_performs=closes,
            )

        # Binding is PATH-INDEPENDENT for A, B and C. Paths A and B leave
        # the FETCH paragraph untouched by design, so binding there would
        # never happen and the business paragraph would stay unreachable.
        lines, business = self._bind_business_paragraph(
            lines=lines,
            cursor_set=cursor_set,
            fetches=fetches,
        )

        # ---- Path A: INLINE already produced a driving PERFORM ... UNTIL
        driving = self._driving_fetch(fetches)

        if driving is not None:
            return self._repair_inline(
                lines=lines,
                cursor_set=cursor_set,
                driving=driving,
                closes=closes,
                eoc_condition=eoc_condition,
            )

        # ---- Path B: a business loop drives the row paragraph (SPAN)
        loop = (
            self.scanner.find_business_loop(lines, business)
            if business
            else None
        )

        if loop is not None:
            return self._repair_span(
                lines=lines,
                cursor_set=cursor_set,
                loop=loop,
                closes=closes,
                eoc_condition=eoc_condition,
            )

        # ---- Path C: no loop at all
        if not SYNTHESISE_MISSING_DRIVING_LOOP:
            self._report("no_driving_loop", cursor=cursor)
            return lines

        return self.repair.synthesise_loop(
            lines=lines,
            cursor_set=cursor_set,
            priming=fetches[0] if fetches else opens[0],
            repeats=self._repeat_fetches(fetches),
            business=business,
            close_performs=closes,
            eoc_condition=eoc_condition,
        )

    # =================================================================
    # Path D - inline block detection
    # =================================================================
    def _inline_block_span(
        self,
        lines: list[str],
        fetches: list[CursorPerform],
    ) -> tuple[int, int] | None:
        """The inline PERFORM block that already drives a fetch, or None.

        Returns (start_index, end_index) of the INNERMOST
        ``PERFORM ... UNTIL ...`` / ``END-PERFORM`` block that contains a
        fetch PERFORM for this cursor.

        A PERFORM line that ENDS IN A PERIOD is an inline-statement
        PERFORM, not a block - it is Path A's or Path B's - so it never
        opens a block here.
        """
        if not RECOGNISE_INLINE_BLOCK_DRIVEN_CURSOR or not fetches:
            return None

        indexes = {perform.index for perform in fetches}
        stack: list[int] = []

        for index, line in enumerate(lines):
            if self._is_comment(line):
                continue

            body = self._logical(line).upper().strip()
            if not body:
                continue

            if body.startswith(TOKEN_END_PERFORM):
                if not stack:
                    continue
                start = stack.pop()
                if any(start < hit < index for hit in indexes):
                    return start, index
                continue

            if not body.startswith(TOKEN_PERFORM):
                continue
            if TOKEN_UNTIL not in body:
                continue
            if body.endswith(SENTENCE_TERMINATOR):
                # PERFORM <para> UNTIL <cond>.  - a statement, not a block
                continue

            stack.append(index)

        return None

    # =================================================================
    # WHEN ZERO binding - paths A, B and C
    # =================================================================
    def _bind_business_paragraph(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
        fetches: list[CursorPerform],
    ) -> tuple[list[str], str]:
        """Make the FETCH drive its business paragraph.

        NOT called on Path D: there the surrounding flow already performs
        the business paragraph, and a second edge recurses.

        Returns the updated lines and the resolved paragraph name, so the
        caller can hand the same name to the loop finder without resolving
        it a second time.

        Resolution order, highest confidence first:
          1. BusinessParagraphResolver - first non-generated paragraph
             after the one that performs the cursor OPEN, verified against
             the cursor's own DCLGEN group or a nested cursor OPEN.
          2. the paragraph that held the orphan repeat fetch.
        An unresolved cursor is reported and left unchanged. It is never
        guessed.
        """
        business = self.business_resolver.resolve(lines, cursor_set)

        if not business:
            business = self._business_paragraph(
                lines, self._repeat_fetches(fetches)
            )

        if not ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH:
            return lines, business

        if not business:
            self._report(
                "business_paragraph_unknown",
                cursor=cursor_set.cursor,
            )
            return lines, ""

        lines = self.repair.bind_fetch_to_business(
            lines=lines,
            fetch_paragraph=cursor_set.fetch_name,
            business=business,
        )
        return lines, business

    # =================================================================
    # Path A
    # =================================================================
    def _repair_inline(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
        driving: CursorPerform,
        closes: list[CursorPerform],
        eoc_condition: str,
    ) -> list[str]:
        """INLINE already ran: only the condition and the CLOSE remain."""
        lines = self.repair.normalise_perform_line(
            lines=lines,
            index=driving.index,
            condition=eoc_condition,
            cursor=cursor_set.cursor,
        )
        return self.repair.guarantee_close(
            lines=lines,
            after_index=driving.index,
            cursor_set=cursor_set,
            close_performs=closes,
        )

    # =================================================================
    # Path B
    # =================================================================
    def _repair_span(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
        loop,
        closes: list[CursorPerform],
        eoc_condition: str,
    ) -> list[str]:
        """SPAN shape: the in-loop fetch is REQUIRED and stays put.

        Removing it would leave SQLCODE unchanged and the loop would run
        forever - the exact defect CursorFlowComposer records as
        CORRECTION 2.
        """
        lines = self.repair.normalise_loop(
            lines=lines,
            loop=loop,
            condition=eoc_condition,
            cursor=cursor_set.cursor,
        )
        return self.repair.guarantee_close(
            lines=lines,
            after_index=loop.end_index,
            cursor_set=cursor_set,
            close_performs=closes,
        )

    # =================================================================
    # Helpers
    # =================================================================
    @staticmethod
    def _driving_fetch(
        fetches: list[CursorPerform],
    ) -> CursorPerform | None:
        """The fetch PERFORM that already carries an UNTIL clause.

        Only sees an UNTIL on the FETCH'S OWN LINE. A fetch nested inside
        an inline PERFORM block is invisible here, which is exactly why
        Path D runs first. See CORRECTION 2.
        """
        for perform in fetches:
            if perform.has_until:
                return perform
        return None

    @staticmethod
    def _repeat_fetches(
        fetches: list[CursorPerform],
    ) -> list[CursorPerform]:
        """Every fetch PERFORM after the priming one, none with UNTIL.

        A fetch that already loops is never an orphan, and the first plain
        fetch is the priming call Path C rewrites into the loop.

        An in-loop fetch never reaches here: Path D returns before Path C
        is considered.
        """
        plain = [item for item in fetches if not item.has_until]
        return plain[1:] if len(plain) > 1 else []

    def _business_paragraph(
        self,
        lines: list[str],
        repeats: list[CursorPerform],
    ) -> str:
        """The paragraph that used to carry the converted OBTAIN NEXT."""
        if not repeats:
            return ""

        headers = self.lines_utils.paragraph_headers(lines)
        return self.lines_utils.owner_paragraph(headers, repeats[0].index)

    def _logical(self, line: str) -> str:
        """Columns 8-72 of a fixed record, or the stripped line."""
        reader = getattr(self.lines_utils, "logical", None)
        if callable(reader):
            try:
                return str(reader(line) or "").strip()
            except Exception:  # noqa: BLE001
                pass
        return str(line or "").strip()

    def _is_comment(self, line: str) -> bool:
        reader = getattr(self.lines_utils, "is_comment", None)
        if callable(reader):
            try:
                return bool(reader(line))
            except Exception:  # noqa: BLE001
                pass
        text = str(line or "")
        if len(text) > 6:
            return text[6] in ("*", "/")
        return text.lstrip().startswith(("*", "/"))

    def _report(self, key: str, **fields) -> None:
        """Log one diagnostic. An unmapped key is REPORTED, not dropped.

        MessageLog resolves a key against the rules vocabulary and says
        nothing when the template is absent, so a new diagnostic produces
        silence until someone remembers to add the text. The message list
        is checked for growth and a fallback is appended when it did not.
        """
        before = len(self.log.messages)
        try:
            self.log.log(key, **fields)
        except Exception:  # noqa: BLE001
            pass

        if len(self.log.messages) == before:
            rendered = " ".join(
                f"{name}={value}" for name, value in sorted(fields.items())
            )
            self.log.messages.append(
                UNMAPPED_DIAGNOSTIC_TEMPLATE.format(key=key, values=rendered)
            )


__all__ = ["CursorCloseGuaranteeComposer"]
# LOCATION: converter/composers/cursor_guarantee/cursor_repair.py
# ACTION: REPLACE ENTIRE FILE

"""Every mutation this pass performs.

Four repairs, each independently safe to skip:

  normalise_perform_line   legacy exit test  -> cursor EOC flag
  normalise_loop           same, UNTIL on its own line
  guarantee_close          insert the missing PERFORM <close>
  synthesise_loop          build the whole driving shape from scratch

Nothing here decides WHICH repair a cursor needs - that is the
composer's single responsibility.

CORRECTION A - two shadowed NOT_FOUND imports
-----------------------------------------------
This module imported NOT_FOUND from mainframe.zowe_commands AND from
record_materialisation.record_sites, then defined its own. The local
assignment won, so the code worked by accident - but the first import
dragged the entire Zowe package (requests, urllib3, .env resolution)
into the converter's import graph from a module that converts COBOL.
Both imports are gone; the local constant stands.

CORRECTION B - double-drive recursion
---------------------------------------
bind_fetch_to_business writes PERFORM <business> [THRU <exit>] into the
FETCH paragraph's WHEN ZERO branch. That is correct for the
FETCH-DRIVEN idiom and WRONG for the MAINLINE-DRIVEN one:

  MAINLINE-DRIVEN   PERFORM <business> THRU <business>-EXIT
                            UNTIL <cursor>-EOC.
                    <business> performs <fetch> at its tail
                    <fetch> WHEN ZERO -> CONTINUE

Binding there produces BOTH edges. COBOL PERFORM holds ONE return
address per paragraph, so the nested call overwrites the outer one and
the pair loops forever. It compiles clean, hangs at run time, and every
static check passes - CHK-14.05 reported PASS on exactly such a program
and the review engine scored it ACCEPTED.

Measured on VMDZ7200: four PERFORM sites where three are correct.

The guard asks ONE question through ONE owner -
fetch_business_binder.already_externally_driven - and both halves must
hold: an external loop drives <business> on this cursor's EOC AND
<business> re-fetches at its own tail. An external driver with no tail
fetch still needs the bind, or nothing ever fetches and the recursion is
traded for a stall.

WHY THE IMPORT CROSSES PACKAGES

already_externally_driven is a pure function over a list of physical
lines. It imports nothing from either cursor package's internals, so it
is safe to call from here. Keeping the detection in one place is the
point: a second copy is the defect this guard exists to close.
"""

from __future__ import annotations

from converter.composers.cursor_close_guarantee.fetch_business_binder import (
    already_externally_driven,
)
from converter.composers.cursor_guarantee.cursor_lines import CursorLines
from converter.composers.cursor_guarantee.cursor_models import (
    CONTINUE_PATTERN,
    UNTIL_ONLY_PATTERN,
    WHEN_ZERO_PATTERN,
    CursorParagraphSet,
    CursorPerform,
    LoopShape,
    MessageLog,
)
from patterns.cursor_close_guarantee_patterns import (
    ANY_WHEN_PATTERN,
    END_EVALUATE_PATTERN,
)
from rules.cursor_close_guarantee_rules import (
    ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH,
    EXIT_PARAGRAPH_SUFFIX,
    PERFORM_BUSINESS_TEMPLATE,
    PERFORM_BUSINESS_THRU_TEMPLATE,
    PERFORM_CLOSE_TEMPLATE,
    PERFORM_FETCH_UNTIL_TEMPLATE,
    PREFER_THRU_EXIT_PARAGRAPH,
    STATEMENT_TERMINATOR,
    UNTIL_TEMPLATE,
)

NOT_FOUND = -1
ALREADY_BOUND = -2

# Operations that head a generated cursor paragraph, e.g.
# 720-FETCH-DZBFASC1. Used to recover the cursor name from the
# paragraph name, since bind_fetch_to_business is not given one.
CURSOR_PARAGRAPH_OPERATIONS = ("OPEN", "FETCH", "CLOSE")
CURSOR_PARAGRAPH_SEPARATOR = "-"
CURSOR_NAME_PART_INDEX = 2


class CursorRepair:
    """Rewrites, inserts and deletes. Owns no path selection."""

    def __init__(
        self,
        lines_utils: CursorLines | None = None,
        log: MessageLog | None = None,
    ) -> None:
        self.lines_utils = lines_utils or CursorLines()
        self.log = log or MessageLog()

    # =================================================================
    # Exit-condition normalisation
    # =================================================================
    def normalise_perform_line(
        self,
        lines: list[str],
        index: int,
        condition: str,
        cursor: str,
    ) -> list[str]:
        """Rewrite the UNTIL tail of a PERFORM <fetch> UNTIL <cond> line."""
        if not 0 <= index < len(lines):
            return lines

        logical = self.lines_utils.logical(lines[index])
        head, _separator, tail = self.lines_utils.partition_until(logical)

        if not tail:
            return lines

        current = tail.rstrip(STATEMENT_TERMINATOR).strip()

        if self.lines_utils.compress(current) == self.lines_utils.compress(
            condition
        ):
            return lines

        if not self.lines_utils.is_legacy_condition(current):
            return lines

        body = f"{head.rstrip()} {UNTIL_TEMPLATE.format(condition=condition)}"

        if logical.rstrip().endswith(STATEMENT_TERMINATOR):
            body = f"{body}{STATEMENT_TERMINATOR}"

        return self._rewrite(lines, index, body, cursor, condition)

    def normalise_loop(
        self,
        lines: list[str],
        loop: LoopShape,
        condition: str,
        cursor: str,
    ) -> list[str]:
        """Rewrite a legacy loop exit condition to the cursor EOC flag."""
        index = loop.until_index

        if not 0 <= index < len(lines):
            return lines

        if self.lines_utils.compress(loop.condition) == (
            self.lines_utils.compress(condition)
        ):
            return lines

        if not self.lines_utils.is_legacy_condition(loop.condition):
            return lines

        logical = self.lines_utils.logical(lines[index])

        if UNTIL_ONLY_PATTERN.match(logical):
            body = UNTIL_TEMPLATE.format(condition=condition)
        else:
            head, _separator, _tail = self.lines_utils.partition_until(logical)
            body = (
                f"{head.rstrip()} "
                f"{UNTIL_TEMPLATE.format(condition=condition)}"
            )

        if loop.terminated:
            body = f"{body}{STATEMENT_TERMINATOR}"

        return self._rewrite(lines, index, body, cursor, condition)

    def _rewrite(
        self,
        lines: list[str],
        index: int,
        body: str,
        cursor: str,
        condition: str,
    ) -> list[str]:
        output = list(lines)
        output[index] = self.lines_utils.format_like(output[index], body)
        self.log.log("condition_rewritten", cursor=cursor, condition=condition)
        return output

    # =================================================================
    # CLOSE guarantee
    # =================================================================
    def guarantee_close(
        self,
        lines: list[str],
        after_index: int,
        cursor_set: CursorParagraphSet,
        close_performs: list[CursorPerform],
    ) -> list[str]:
        if close_performs:
            self.log.log("close_present", close=cursor_set.close_name)
            return lines

        if not 0 <= after_index < len(lines):
            return lines

        close_line = self.lines_utils.format_like(
            lines[after_index],
            PERFORM_CLOSE_TEMPLATE.format(close=cursor_set.close_name),
        )

        output = list(lines)
        output.insert(after_index + 1, close_line)

        self.log.log(
            "close_inserted",
            close=cursor_set.close_name,
            cursor=cursor_set.cursor,
        )

        return output

    # =================================================================
    # Loop synthesis
    # =================================================================
    def synthesise_loop(
        self,
        lines: list[str],
        cursor_set: CursorParagraphSet,
        priming: CursorPerform,
        repeats: list[CursorPerform],
        business: str,
        close_performs: list[CursorPerform],
        eoc_condition: str,
    ) -> list[str]:
        """Build OPEN / FETCH-UNTIL / CLOSE and drive the business para.

        Step 2 runs before step 3 because deleting a line BELOW the
        priming fetch cannot move it, while inserting above it would
        move every repeat index.
        """
        output = list(lines)

        # 1. Bind the FETCH paragraph to the business paragraph.
        if business and ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH:
            output = self.bind_fetch_to_business(
                lines=output,
                fetch_paragraph=cursor_set.fetch_name,
                business=business,
            )
        elif not business:
            self.log.log("business_paragraph_unknown", cursor=cursor_set.cursor)

        # 2. Remove every orphan repeat fetch, highest index first.
        for repeat in sorted(repeats, key=lambda item: item.index, reverse=True):
            output = self.remove_statement(output, repeat.index)
            self.log.log("repeat_fetch_removed", fetch=repeat.paragraph)

        # 3. Replace the priming fetch with the loop, plus the CLOSE.
        if not 0 <= priming.index < len(output):
            return output

        reference = output[priming.index]

        replacement = [
            self.lines_utils.format_like(
                reference,
                PERFORM_FETCH_UNTIL_TEMPLATE.format(
                    fetch=cursor_set.fetch_name,
                    condition=eoc_condition,
                ),
            )
        ]

        if close_performs:
            self.log.log("close_present", close=cursor_set.close_name)
        else:
            replacement.append(
                self.lines_utils.format_like(
                    reference,
                    PERFORM_CLOSE_TEMPLATE.format(close=cursor_set.close_name),
                )
            )

        output[priming.index : priming.index + 1] = replacement

        self.log.log(
            "loop_synthesised",
            cursor=cursor_set.cursor,
            fetch=cursor_set.fetch_name,
            condition=eoc_condition,
            close=cursor_set.close_name,
        )

        return output

    # =================================================================
    # Business paragraph binding
    # =================================================================
    def bind_fetch_to_business(
        self,
        lines: list[str],
        fetch_paragraph: str,
        business: str,
    ) -> list[str]:
        """Rewrite WHEN ZERO / CONTINUE inside the FETCH paragraph.

        CORRECTION 1 - only the FIRST statement after WHEN ZERO was read

        next_executable_index() returns ONE index. The generated branch
        carries the row counter ahead of the CONTINUE:

            WHEN ZERO
                 ADD 1 TO WS-NB-BEFF-COUNT      <- returned
                 CONTINUE                       <- never examined

        CONTINUE_PATTERN failed against the ADD, the loop advanced, and
        the method returned the list unchanged. Every FETCH that carries
        a counter - which is every FETCH the body builder emits, and the
        shape the manual reference uses - was unbindable, so the business
        paragraph stayed unreachable and the program wrote nothing.

        The WHOLE branch is now scanned, bounded by the next WHEN or by
        END-EVALUATE, so a CONTINUE at any depth in the branch is found
        and a CONTINUE belonging to another branch never is.

        CORRECTION 2 - five exits, no diagnostics

        span not found, no CONTINUE, already bound, nothing bound: all
        returned in silence. A refusal with no diagnostic is worse than
        no guard at all - it cost a full debugging cycle to find this.
        Every exit now reports.

        CORRECTION 3 - the mainline-driven idiom must NOT be bound

        See CORRECTION B in the module docstring. The guard runs before
        any line is touched and reports its refusal, so a program that
        is left alone says why in the run log.
        """
        if not fetch_paragraph or not business:
            self.log.log(
                "bind_missing_argument",
                fetch=fetch_paragraph or "(none)",
                paragraph=business or "(none)",
            )
            return lines

        headers = self.lines_utils.paragraph_headers(lines)
        span = self.lines_utils.paragraph_span(
            headers, fetch_paragraph, len(lines)
        )

        if span is None:
            self.log.log("fetch_paragraph_not_found", fetch=fetch_paragraph)
            return lines

        start, end = span

        cursor = self._cursor_of(fetch_paragraph)

        if cursor and already_externally_driven(
            lines, cursor, business, fetch_paragraph
        ):
            self.log.log(
                "already_driven_by_span",
                paragraph=business,
                cursor=cursor,
                fetch=fetch_paragraph,
            )
            return lines

        body = self._business_body(headers, business)
        target_key = self._compress(body)

        output = list(lines)
        bound = 0
        index = start

        while index < end:
            logical = self.lines_utils.logical(output[index])

            if not WHEN_ZERO_PATTERN.match(logical):
                index += 1
                continue

            target = self._continue_in_branch(
                lines=output,
                start=index + 1,
                end=end,
                target_key=target_key,
            )

            if target == ALREADY_BOUND:
                self.log.log(
                    "business_paragraph_already_bound",
                    fetch=fetch_paragraph,
                    paragraph=business,
                )
                return lines

            if target == NOT_FOUND:
                index += 1
                continue

            output[target] = self.lines_utils.format_like(
                output[target], body
            )
            self.log.log(
                "business_paragraph_bound",
                fetch=fetch_paragraph,
                paragraph=business,
            )
            bound += 1
            index = target + 1

        if not bound:
            self.log.log("when_zero_not_bindable", fetch=fetch_paragraph)
            return lines

        return output

    def _continue_in_branch(
        self,
        lines: list[str],
        start: int,
        end: int,
        target_key: str,
    ) -> int:
        """Index of the CONTINUE inside one WHEN ZERO branch.

        Returns ALREADY_BOUND when the branch already performs the
        business paragraph, NOT_FOUND otherwise. Scanning stops at the
        next WHEN or at END-EVALUATE, so a CONTINUE belonging to WHEN 100
        or WHEN OTHER can never be claimed.
        """
        for index in range(max(0, start), min(end, len(lines))):
            logical = self.lines_utils.logical(lines[index])

            if not logical or self.lines_utils.is_comment(logical):
                continue

            if self._compress(logical) == target_key:
                return ALREADY_BOUND

            if ANY_WHEN_PATTERN.match(logical):
                return NOT_FOUND

            if END_EVALUATE_PATTERN.match(logical):
                return NOT_FOUND

            if CONTINUE_PATTERN.match(logical):
                return index

        return NOT_FOUND

    @staticmethod
    def _compress(text: str) -> str:
        """Whitespace-insensitive, case-insensitive comparison key."""
        return " ".join(str(text or "").split()).upper().rstrip(".")

    @staticmethod
    def _cursor_of(fetch_paragraph: str) -> str:
        """DZBFASC1 from 720-FETCH-DZBFASC1. Empty when not that shape.

        bind_fetch_to_business is not given a cursor name, and adding a
        parameter would change every call site. The generated paragraph
        name already carries it.
        """
        parts = str(fetch_paragraph or "").upper().split(
            CURSOR_PARAGRAPH_SEPARATOR
        )

        if len(parts) <= CURSOR_NAME_PART_INDEX:
            return ""

        if parts[1] not in CURSOR_PARAGRAPH_OPERATIONS:
            return ""

        return CURSOR_PARAGRAPH_SEPARATOR.join(
            parts[CURSOR_NAME_PART_INDEX:]
        )

    @staticmethod
    def _business_body(headers, business: str) -> str:
        body = PERFORM_BUSINESS_TEMPLATE.format(paragraph=business)

        if not PREFER_THRU_EXIT_PARAGRAPH:
            return body

        exit_name = f"{business}{EXIT_PARAGRAPH_SUFFIX}"

        if any(header.name == exit_name for header in headers):
            return PERFORM_BUSINESS_THRU_TEMPLATE.format(
                paragraph=business,
                through=exit_name,
            )

        return body

    # =================================================================
    # Statement removal
    # =================================================================
    def remove_statement(
        self,
        lines: list[str],
        index: int,
    ) -> list[str]:
        """Delete one statement without orphaning its COBOL sentence."""
        if not 0 <= index < len(lines):
            return lines

        removed = self.lines_utils.logical(lines[index])
        carried_period = removed.rstrip().endswith(STATEMENT_TERMINATOR)

        output = list(lines)
        del output[index]

        if not carried_period:
            return output

        previous = self.lines_utils.previous_executable_index(output, index - 1)

        if previous < 0:
            return output

        previous_logical = self.lines_utils.logical(output[previous])

        if previous_logical.rstrip().endswith(STATEMENT_TERMINATOR):
            return output

        output[previous] = self.lines_utils.format_like(
            output[previous],
            f"{previous_logical.rstrip()}{STATEMENT_TERMINATOR}",
        )

        return output


__all__ = ["CursorRepair"]
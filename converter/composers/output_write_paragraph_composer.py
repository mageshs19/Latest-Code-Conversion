# LOCATION: converter/composers/output_write_paragraph_composer.py
# ACTION: REPLACE ENTIRE FILE
"""Output write paragraph composer.

Lifts an inline output-record population block into its own paragraph and
replaces it with a PERFORM, matching the COBOL team's manual reference.

    HOOFDVERWERKING.                    HOOFDVERWERKING.
        IF WS-STATUS = 'C'                  IF WS-STATUS = 'C'
           INITIALIZE UITRECORD  ->            PERFORM WRITE-UITRECORD
           MOVE ... TO ...                     ADD 1 TO WS-NB-OUTPUT-COUNT
           WRITE UITRECORD                  END-IF.
        END-IF.                         /
                                        WRITE-UITRECORD.
                                            INITIALIZE UITRECORD
                                            MOVE ... TO ...
                                            WRITE UITRECORD.

Scope and safety
----------------
- PROCEDURE DIVISION only.
- Exactly ONE WRITE per block. Two writes is a business decision.
- REFUSES for the whole program when any guard condition spans lines.
- Lines are moved and re-indented, never edited.

Ordering
--------
AFTER composers["feedback_cleanup"] (relocates the guarded block) and
AFTER composers["fixed_format"] (so lines can clone a sequence area).
BEFORE FinalSequenceResequencerService.

Responsibility split
--------------------
    output_write/output_write_line_utils.py     line inspection
    output_write/output_write_scanner.py        boundaries
    output_write/output_write_guard.py          structural safety gate
    output_write/output_write_block_finder.py   candidate discovery
    output_write/output_write_eligibility.py    accept / refuse
    output_write/output_write_renderer.py       rendering
    output_write/output_write_extractor.py      line replacement

This class owns iteration and diagnostics. Nothing else.
"""

from __future__ import annotations

# Concrete module imports, not the package. A stale or partially updated
# __init__.py then cannot break this composer:
#
#   ImportError: cannot import name 'OutputWriteBlockFinder' from
#   'converter.composers.output_write'
#
from converter.composers.output_write.output_write_block_finder import (
    OutputWriteBlockFinder,
)
from converter.composers.output_write.output_write_eligibility import (
    OutputWriteEligibility,
)
from converter.composers.output_write.output_write_extractor import (
    OutputWriteExtractor,
)
from converter.composers.output_write.output_write_guard import (
    OutputWriteGuard,
)
from converter.composers.output_write.output_write_line_utils import (
    OutputWriteLineUtils,
)
from converter.composers.output_write.output_write_scanner import (
    OutputWriteScanner,
)
from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from rules.output_write_paragraph_rules import (
    EMIT_OUTPUT_COUNTER_INCREMENT,
    ENFORCE_OUTPUT_WRITE_PARAGRAPH,
    EXTRACTION_PASS_LIMIT,
    OUTPUT_COUNTER_NAME,
    OUTPUT_WRITE_PARAGRAPH_MESSAGES,
)
from rules.structural_safety_rules import (
    ENFORCE_CONDITION_INTEGRITY,
    STRUCTURAL_SAFETY_MESSAGES,
)


class OutputWriteParagraphComposer:
    """Extracts inline output write blocks into their own paragraphs."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.lines = OutputWriteLineUtils(
            fixed_format=fixed_format or FixedFormatLineService(),
        )
        scanner = OutputWriteScanner(self.lines)

        self.guard = OutputWriteGuard(self.lines)
        self.finder = OutputWriteBlockFinder(self.lines, scanner)
        self.eligibility = OutputWriteEligibility(self.lines, scanner)
        self.extractor = OutputWriteExtractor(self.lines, scanner=scanner)
        self.messages: list[str] = []

    # =================================================================
    # Public entry point
    # =================================================================
    def compose(self, text: str) -> str:
        """Extract every eligible output write block.

        CORRECTION - the structural guard was applied here, program-wide.

        _refused_by_guard() ran before any candidate was examined and
        abandoned the whole program when ANY PROCEDURE DIVISION IF
        carried a multi-line condition. In VMDZ4420 the offending
        conditions were business status tests; the write block's own
        guard, IF WS-STATUS = 'C', was a single line and safe.

        The guard is now evaluated PER CANDIDATE in _extract_once(),
        which already skips a refused candidate and tries the next.
        """
        self.messages = []

        if not text or not ENFORCE_OUTPUT_WRITE_PARAGRAPH:
            return str(text or "")

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        # Each success shifts every index after it, so the scan restarts.
        for _pass in range(EXTRACTION_PASS_LIMIT):
            if not self._extract_once(lines):
                break

        return "\n".join(lines).rstrip() + "\n"
    
    # =================================================================
    # Structural safety
    # =================================================================
    def _refused_by_guard(self, text: str) -> bool:
        """Never cut between an IF keyword and the end of its condition.

        The gate is deliberately program-wide: one multi-line guard
        anywhere refuses every extraction in the program. Refusing
        leaves working COBOL; guessing produces source the compiler
        rejects.
        """
        if not ENFORCE_CONDITION_INTEGRITY:
            return False
        if not self.guard.blocks_extraction(text):
            return False

        self.messages.append(
            STRUCTURAL_SAFETY_MESSAGES["extraction_refused"].format(
                count=self.guard.widest_condition(text),
            )
        )
        return True

    # =================================================================
    # One extraction
    # =================================================================
# LOCATION: converter/composers/output_write_paragraph_composer.py
# ACTION: REPLACE _extract_once

    def _extract_once(self, lines: list[str]) -> bool:
        """Extract the INNERMOST eligible block. True when one was taken.

        CORRECTION - the first eligible candidate was taken, and
        candidates arrive outermost first.

        Extraction moves the candidate's BODY, which starts at
        if_index + 1. Taking the outer guard therefore moved the inner
        guard into the new paragraph:

            IF NOT SW-STATUS-D = 'Y'
               PERFORM WRITE-UITRECORD
               ADD 1 TO WS-NB-OUTPUT-COUNT     <- fires unconditionally
            END-IF.

         WRITE-UITRECORD.
            IF WS-STATUS = 'C'                 <- the real write decision
               ...
               WRITE UITRECORD
            END-IF.

        The counter then measured ATTEMPTS, not writes, and
        output_write_paragraph_rules.py requires the opposite: the count
        is taken at the call site precisely so it reflects every guard
        decision.

        Every enclosing guard must stay at the call site. The innermost
        eligible candidate is the one whose body is pure population, so
        candidates are now ranked and the deepest is taken.

        Three gates, cheapest and least noisy first:

          1. ELIGIBILITY - exactly one WRITE. A block with none is an
             ordinary IF and is dismissed in silence.
          2. CONDITION INTEGRITY - this block's OWN guard must fit one
             line, because the cut is at if_index + 1.
          3. EXTRACT the deepest survivor.
        """
        existing = self.lines.paragraph_names(lines)
        accepted: list = []

        for block in self.finder.candidates(lines):
            plan, refusal = self.eligibility.assess(lines, block, existing)

            if plan is None:
                if refusal is not None and refusal.is_reportable:
                    self._log(refusal.key, **refusal.values)
                continue

            if self._condition_spans_lines(lines, block):
                continue

            accepted.append((block, plan))

        if not accepted:
            return False

        # Deepest candidate = highest if_index. Nested blocks are always
        # yielded after the block that encloses them.
        block, plan = max(accepted, key=lambda item: item[0].if_index)

        self.extractor.apply(lines, plan)
        self._log_success(block.source, plan.paragraph)
        return True
        
    # =================================================================
    # Diagnostics
    # =================================================================
    def _log_success(self, source: str, paragraph: str) -> None:
        self._log("extracted", source=source, paragraph=paragraph)

        if EMIT_OUTPUT_COUNTER_INCREMENT:
            self._log(
                "counter_added",
                counter=OUTPUT_COUNTER_NAME,
                paragraph=paragraph,
            )

    def _log(self, key: str, **values) -> None:
        template = OUTPUT_WRITE_PARAGRAPH_MESSAGES.get(key, "")
        if template:
            self.messages.append(template.format(**values))

    def _condition_spans_lines(self, lines: list[str], block) -> bool:
        """Refuse one candidate whose own IF condition spans lines."""
        if not ENFORCE_CONDITION_INTEGRITY:
            return False

        if not self.guard.blocks_candidate(lines, block.if_index):
            return False

        self.messages.append(
            STRUCTURAL_SAFETY_MESSAGES["extraction_refused_block"].format(
                source=block.source,
                count=self.guard.condition_size(lines, block.if_index),
            )
        )
        return True


__all__ = ["OutputWriteParagraphComposer"]
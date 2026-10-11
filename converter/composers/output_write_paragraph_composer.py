from __future__ import annotations

from converter.composers.output_write.output_write_block_finder import (
    OutputWriteBlockFinder,
)
from converter.composers.output_write.output_write_eligibility import (
    OutputWriteEligibility,
)
from converter.composers.output_write.output_write_extractor import (
    OutputWriteExtractor,
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

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.lines = OutputWriteLineUtils(
            fixed_format=fixed_format or FixedFormatLineService(),
        )
        scanner = OutputWriteScanner(self.lines)

        self.finder = OutputWriteBlockFinder(self.lines, scanner)
        self.eligibility = OutputWriteEligibility(self.lines, scanner)
        self.extractor = OutputWriteExtractor(self.lines, scanner=scanner)
        self.messages: list[str] = []

    def compose(self, text: str) -> str:
        self.messages = []

        if not text or not ENFORCE_OUTPUT_WRITE_PARAGRAPH:
            return str(text or "")

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        for _pass in range(EXTRACTION_PASS_LIMIT):
            if not self._extract_once(lines):
                break

        return "\n".join(lines).rstrip() + "\n"

    def _extract_once(self, lines: list[str]) -> bool:
        existing = self.lines.paragraph_names(lines)
        accepted: list = []

        for block in self.finder.candidates(lines):
            plan, refusal = self.eligibility.assess(lines, block, existing)

            if plan is None:
                if refusal is not None and refusal.is_reportable:
                    self._log(refusal.key, **refusal.values)
                continue

            if self._condition_unresolved(block):
                continue

            accepted.append((block, plan))

        if not accepted:
            return False

        block, plan = max(accepted, key=lambda item: item[0].if_index)

        self.extractor.apply(lines, plan)
        self._log_success(block.source, plan.paragraph)
        return True

    def _condition_unresolved(self, block) -> bool:
        if not ENFORCE_CONDITION_INTEGRITY:
            return False
        if block.has_resolved_condition:
            return False

        template = STRUCTURAL_SAFETY_MESSAGES.get(
            "extraction_condition_unresolved", ""
        )
        if template:
            self.messages.append(template.format(source=block.source))
        return True

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


__all__ = ["OutputWriteParagraphComposer"]
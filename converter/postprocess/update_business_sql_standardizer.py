from __future__ import annotations

from converter.postprocess.dynamic_metadata_resolver import UpdateProgramContext
from converter.postprocess.update_business_sql.update_business_sql_line_renderer import (
    UpdateBusinessSqlLineRenderer,
)
from converter.postprocess.update_business_sql.update_paragraph_normalizer import (
    UpdateParagraphNormalizer,
)
from converter.postprocess.update_business_sql.update_sql_block_extractor import (
    UpdateSqlBlockExtractor,
)
from converter.postprocess.update_postprocess_line_utils import (
    UpdatePostprocessLineUtils,
)
from patterns.update_business_sql_patterns import (
    CONVERTED_MODIFY_COMMENT_PATTERN,
    PERFORM_UPDATE_PARAGRAPH_PATTERN,
)
from patterns.update_main_flow_patterns import PERFORM_UNTIL_LINE_PATTERN
from rules.update_business_sql_rules import (
    DIAG_PROCESS_PARAGRAPH_NOT_FOUND_TEMPLATE,
    DIAG_PROCESS_PARAGRAPH_UNRESOLVED,
    LONE_PERIOD,
    NESTED_INDENT,
    READ_FLAT_FILE_PARAGRAPH,
    TOKEN_END_IF,
    TOKEN_IF,
    TOKEN_INITIALIZE_DCL,
    TOKEN_PERFORM,
)
from rules.update_restart_rules import (
    UPDATE_RESTART_DIAGNOSTICS,
    UPDATE_RESTART_WS_NAMES,
    UPDATE_SQL_PARAGRAPH_PREFIX,
)

from converter.postprocess.update_business_sql.update_counter_declarer import (
    UpdateCounterDeclarer,
)

class UpdateBusinessSqlStandardizer(
    UpdateBusinessSqlLineRenderer,
    UpdateParagraphNormalizer,
    UpdateSqlBlockExtractor,
):
    """Standardizes update-program business SQL structure.

    Update-postprocess only; does not touch retrieval. This facade holds the
    orchestration and small paragraph helpers. Fixed-format rendering,
    paragraph normalization, and block extraction are provided by mixins.
    All COBOL tokens and column geometry live in
    rules/update_business_sql_rules.py.
    """

    def __init__(self, *, line_utils: UpdatePostprocessLineUtils) -> None:
        self.line_utils = line_utils

    def standardize(
        self,
        cobol_text: str,
        context: UpdateProgramContext,
        diagnostics: list[str],
    ) -> str:
        if not context.restart_dclgen:
            diagnostics.append(
                "Update business SQL: context carries no restart DCLGEN; "
                "business SQL standardisation not attempted. "
                f"restart_dclgen={context.restart_dclgen!r} "
                f"input_record_name="
                f"{getattr(context, 'input_record_name', None)!r}"
            )
            return cobol_text

        lines = self.line_utils.lines(cobol_text)

        process_paragraph = self._resolve_process_paragraph(
            lines=lines,
            input_record_name=context.input_record_name,
            diagnostics=diagnostics,
        )
        if not process_paragraph:
            diagnostics.append(DIAG_PROCESS_PARAGRAPH_UNRESOLVED)
            return cobol_text

        paragraph_range = self.line_utils.find_paragraph_range(lines, process_paragraph)
        if not paragraph_range:
            diagnostics.append(
                DIAG_PROCESS_PARAGRAPH_NOT_FOUND_TEMPLATE.format(
                    paragraph=process_paragraph
                )
            )
            return cobol_text

        start, end = paragraph_range
        block_info = self._find_inline_update_block(lines=lines, start=start, end=end)

        if block_info:
            lines = self._extract_inline_update_block(
                lines=lines,
                process_paragraph=process_paragraph,
                block_info=block_info,
                diagnostics=diagnostics,
            )
        elif not self._paragraph_contains_update_perform(
            lines=lines, start=start, end=end
        ):
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["business_update_not_found"])
        lines = UpdateCounterDeclarer(self.line_utils).ensure(
            lines=lines, diagnostics=diagnostics
        )
        lines = self._cleanup_process_paragraph(
            lines=lines, process_paragraph=process_paragraph
        )
        lines = self._normalize_all_update_paragraphs(lines)

        return self.line_utils.join(lines)

    def _cleanup_process_paragraph(self, *, lines, process_paragraph):
        paragraph_range = self.line_utils.find_paragraph_range(lines, process_paragraph)
        if not paragraph_range:
            return lines

        start, end = paragraph_range
        output: list[str] = []

        for index, line in enumerate(lines):
            if not (start < index < end):
                output.append(line)
                continue

            logical = self._logical(line).strip()
            upper = logical.upper().rstrip(".")

            if upper.startswith(TOKEN_INITIALIZE_DCL) and self._is_comment_line(line):
                output.append(
                    self._active_line_like(reference_line=line, body=upper + ".")
                )
                continue

            if CONVERTED_MODIFY_COMMENT_PATTERN.match(logical):
                continue

            output.append(line)

        paragraph_range = self.line_utils.find_paragraph_range(output, process_paragraph)
        if not paragraph_range:
            return output

        start, end = paragraph_range
        return self._normalize_process_commit_block(lines=output, start=start, end=end)

    def _normalize_process_commit_block(self, *, lines, start, end):
        output = list(lines)
        index = start + 1

        while index < end:
            logical = self._logical(output[index]).upper().rstrip(".")

            if not logical.startswith(TOKEN_IF):
                index += 1
                continue
            if UPDATE_RESTART_WS_NAMES["commit_counter"] not in logical:
                index += 1
                continue

            block_end = self._find_end_if(lines=output, start=index, limit=end)
            if block_end < 0:
                index += 1
                continue

            for block_index in range(index, block_end + 1):
                body = self._logical(output[block_index]).strip()
                if not body:
                    continue
                if body.upper().startswith(TOKEN_PERFORM):
                    output[block_index] = self._active_line_like(
                        reference_line=output[block_index],
                        body=f"{NESTED_INDENT}{body.rstrip('.')}",
                    )
                else:
                    output[block_index] = self._active_line_like(
                        reference_line=output[block_index], body=body
                    )

            index = block_end + 1

        return output

    def _find_end_if(self, *, lines, start, limit):
        for index in range(start + 1, limit):
            logical = self._logical(lines[index]).upper().rstrip(".")
            if logical.startswith(TOKEN_END_IF):
                return index
        return -1

    def _resolve_process_paragraph(self, *, lines, input_record_name, diagnostics=None):
        """The driving paragraph of the record loop.

        CORRECTION - the match required <input_record_name>-EOF, and the
        record name was DERIVED by the metadata resolver while the EOF
        condition is written in the CODE. When the two disagree - and the
        same run reported "Legacy EOF switch not resolved" - this returned
        "" and the whole business SQL pass was skipped. The program kept
        its restart scaffolding and lost its UPDATE: it ran clean, wrote a
        checkpoint, committed, and changed no data.

        The exact match is still preferred. When it fails, ANY
        PERFORM <paragraph> UNTIL <something>-EOF is accepted and the
        disagreement is REPORTED with both names, because a silent empty
        return is indistinguishable from "there was nothing here".
        """
        record = str(input_record_name or "").strip().upper()
        target_eof = f"{record}-EOF" if record else ""
        fallback = ""
        fallback_condition = ""

        for line in lines:
            logical = self._logical(line).upper().rstrip(".")
            match = PERFORM_UNTIL_LINE_PATTERN.search(logical)
            if not match:
                continue

            paragraph = str(match.group("paragraph") or "").strip().upper()
            if not paragraph or paragraph == READ_FLAT_FILE_PARAGRAPH:
                continue

            if target_eof and target_eof in logical:
                return paragraph

            if not fallback and "-EOF" in logical:
                fallback = paragraph
                fallback_condition = logical

        if fallback:
            if diagnostics is not None:
                diagnostics.append(
                    "Update business SQL: the resolved input record "
                    f"'{record or '(none)'}' does not match the loop "
                    f"condition '{fallback_condition}'; used {fallback}. "
                    "Check the resolved copybook."
                )
            return fallback

        return ""
    
    def _paragraph_contains_update_perform(self, *, lines, start, end):
        for index in range(start + 1, end):
            if PERFORM_UPDATE_PARAGRAPH_PATTERN.match(self._logical(lines[index])):
                return True
        return False

    def _paragraph_exists(self, lines, paragraph_name):
        target = str(paragraph_name or "").strip().upper().rstrip(".")
        for line in lines:
            if self._logical(line).upper().rstrip(".") == target:
                return True
        return False

    def _update_paragraph_name(self, record_name):
        clean = str(record_name or "").strip().upper().replace("_", "-")
        return f"{UPDATE_SQL_PARAGRAPH_PREFIX}-{clean}"

    def _strip_existing_final_period(self, lines):
        output = list(lines)
        while output and not self._logical(output[-1]):
            output.pop()
        if output and self._logical(output[-1]) == LONE_PERIOD:
            output.pop()
        return output
# LOCATION: converter/composers/procedure_indent_normalizer.py
# ACTION: REPLACE ENTIRE FILE
"""Procedure Division indentation normalizer.

Runs late (before final resequence) to give PROCEDURE DIVISION
executable statements a consistent, DEPTH-AWARE Area-B indentation.

REFACTOR - one class became three.

    procedure_indent/indent_models.py     frames, stack, classification
    procedure_indent/indent_resolver.py   which indent, and why
    procedure_indent_normalizer.py        this file: walk and render

The public surface is UNCHANGED: compose(str) -> str plus `messages`.

Safe scope
----------
- Only PROCEDURE DIVISION.
- Never touches comments, debug lines, '-' continuations, Area-A
  headers, or the DATA and other divisions.
- Rewrites only columns 8-72; left seq (1-6) and right seq (73-80) are
  untouched.
- EXEC SQL bodies and word-boundary continuations keep their own
  alignment. See the two CORRECTIONs in the collaborator files.

CORRECTION - silent truncation
------------------------------
This class once carried a private copy of the fixed-format geometry
that had drifted from the shared service, and _rebuild truncated any
body past column 72 without saying so. Because this is the LAST content
pass, that is how

    MOVE NR-IDGOOD-479EVEF OF DCLDZEVEFTV    TO WS-NR-ID-GOOD

shipped as ... TO WS-NR-ID-GO, an undefined data name the compiler
rejects. Geometry is delegated entirely to FixedFormatLineService; a
re-indent that no longer fits is WRAPPED, and if even that fails the
original line is kept. A cosmetic pass must never destroy a statement.

TEMPORARY INSTRUMENTATION
-------------------------
DUMP_INTERMEDIATE writes the text this pass receives and returns. Set
it False, or delete the three marked blocks, once the upstream merge
that produced a two-line four-line condition is fixed.
"""

from __future__ import annotations

from pathlib import Path  # TEMP DEBUG

from converter.composers.procedure_indent.indent_models import (
    FrameStack,
    LineClassifier,
)
from converter.composers.procedure_indent.indent_resolver import (
    IndentResolver,
)
from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.procedure_indent_patterns import (
    OTHER_DIVISION_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
)
from rules.procedure_indent_rules import (
    AREA_A_INDENT,
    ENFORCE_PROCEDURE_INDENT,
    MAX_NESTING_DEPTH,
    PRESERVE_INDENT,
    PROCEDURE_INDENT_MESSAGES,
)

# TEMP DEBUG
DUMP_INTERMEDIATE = True
DUMP_IN = "debug_indent_in.txt"
DUMP_OUT = "debug_indent_out.txt"


class ProcedureIndentNormalizer:
    """Depth-aware Area-B re-indentation for the PROCEDURE DIVISION."""

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.classifier = LineClassifier(self.fixed_format)
        self.resolver = IndentResolver(self.classifier)
        self.messages: list[str] = []

    # =================================================================
    # Public entry point
    # =================================================================
    def compose(self, text: str) -> str:
        self.messages = []
        self._dump(DUMP_IN, text)  # TEMP DEBUG

        if not text or not ENFORCE_PROCEDURE_INDENT:
            return str(text or "")

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        output: list[str] = []
        stack = FrameStack()
        in_procedure = False
        previous_upper = ""
        counts = {"normalized": 0, "wrapped": 0, "preserved": 0}

        for number, line in enumerate(lines, start=1):
            if self.classifier.is_untouchable(line):
                output.append(line)
                continue

            logical = self.fixed_format.logical(line)
            if not logical:
                output.append(line)
                continue

            upper = logical.upper()

            if PROCEDURE_DIVISION_PATTERN.match(upper):
                in_procedure = True
                stack.clear()
                output.append(line)
                previous_upper = upper
                continue

            if OTHER_DIVISION_PATTERN.match(upper):
                in_procedure = False
                stack.clear()
                output.append(line)
                previous_upper = upper
                continue

            if not in_procedure:
                output.append(line)
                previous_upper = upper
                continue

            # ---- a continuation keeps the alignment it arrived with
            if self.classifier.is_continuation(upper, previous_upper):
                output.append(line)
                counts["preserved"] += 1
                previous_upper = upper
                continue

            if self.classifier.is_area_a_header(upper):
                stack.clear()
                self._emit(line, AREA_A_INDENT, logical, output, counts)
                previous_upper = upper
                continue

            if len(stack) > MAX_NESTING_DEPTH:
                self.messages.append(
                    PROCEDURE_INDENT_MESSAGES["skipped_depth"].format(
                        limit=MAX_NESTING_DEPTH,
                        line=number,
                    )
                )
                output.append(line)
                previous_upper = upper
                continue

            indent = self.resolver.resolve(upper, stack)

            if indent == PRESERVE_INDENT:
                output.append(line)
                counts["preserved"] += 1
            else:
                self._emit(line, indent, logical, output, counts)

            previous_upper = upper

        self._report(counts)
        result = "\n".join(output).rstrip() + "\n"
        self._dump(DUMP_OUT, result)  # TEMP DEBUG
        return result

    # =================================================================
    # Rendering
    # =================================================================
    def _emit(
        self,
        line: str,
        indent: int,
        logical: str,
        output: list[str],
        counts: dict[str, int],
    ) -> None:
        rendered = self._render(line, indent, logical)
        output.extend(rendered)

        if len(rendered) > 1:
            counts["wrapped"] += len(rendered) - 1
        if rendered[0] != line:
            counts["normalized"] += 1

    def _render(
        self,
        line: str,
        indent: int,
        logical: str,
    ) -> list[str]:
        """Re-indent one statement, wrapping instead of truncating.

        Returns the ORIGINAL line when the new body cannot be
        represented, so a cosmetic pass can never destroy code.
        """
        new_body = (" " * max(indent, 0)) + logical

        if new_body == self.fixed_format.body(line).rstrip():
            return [line]

        if self.fixed_format.body_fits(new_body):
            return [self.fixed_format.replace_body(line, new_body)]

        rendered = self.fixed_format.replace_body_wrapped(line, new_body)
        return rendered if rendered else [line]

    # =================================================================
    # Diagnostics
    # =================================================================
    def _report(self, counts: dict[str, int]) -> None:
        for key in ("normalized", "wrapped", "preserved"):
            if counts[key]:
                self.messages.append(
                    PROCEDURE_INDENT_MESSAGES[key].format(count=counts[key])
                )

    @staticmethod
    def _dump(name: str, text: str) -> None:  # TEMP DEBUG
        """Write one pipeline snapshot. Never raises, never blocks."""
        if not DUMP_INTERMEDIATE:
            return
        try:
            Path(name).write_text(str(text or ""), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


__all__ = ["ProcedureIndentNormalizer"]
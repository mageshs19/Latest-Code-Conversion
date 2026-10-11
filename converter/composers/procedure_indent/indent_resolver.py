# LOCATION: converter/composers/procedure_indent/indent_resolver.py
# ACTION: CREATE NEW FILE
"""Decides the body indent for one PROCEDURE DIVISION line.

One method, one question: given this line and the open blocks, how far
from column 8 does its body start? Returns PRESERVE_INDENT when the
line already carries an alignment this pass cannot improve on.

CORRECTION - the EXEC SQL body was flattened to one column.

    if stack and stack[-1].kind == BLOCK_KIND_SQL:
        return stack[-1].body_indent, stack

Every line inside EXEC SQL was forced to the frame's body indent, so

      INTO :DCLDZBEFFTV.CO-IDPRKSK-479BEFF        column 15
         , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF        column 18

both came out at column 14. SQL clause positions are fixed by the
manual reference and set by the generator; they are CLAUSE positions,
not nesting depth, and this pass has no way to reconstruct them. The
body is now preserved exactly as rendered.
"""

from __future__ import annotations

from patterns.procedure_indent_patterns import (
    ELSE_PATTERN,
    END_EXEC_PATTERN,
    EVALUATE_START_PATTERN,
    EXEC_SQL_START_PATTERN,
    IF_START_PATTERN,
    INLINE_PERFORM_PATTERN,
    LONE_PERIOD_PATTERN,
    SCOPE_TERMINATOR_PATTERN,
    SCOPED_OPENER_PATTERN,
    WHEN_PATTERN,
)
from rules.procedure_indent_rules import (
    AREA_B_INDENT,
    BLOCK_KIND_EVALUATE,
    BLOCK_KIND_IF,
    BLOCK_KIND_OTHER,
    BLOCK_KIND_PERFORM,
    BLOCK_KIND_SQL,
    LONE_PERIOD_INDENT,
    PRESERVE_INDENT,
    PRESERVE_SQL_BODY_INDENT,
    SCOPE_TERMINATORS,
    WHEN_OFFSET,
)

from converter.composers.procedure_indent.indent_models import (
    FrameStack,
    LineClassifier,
)


class IndentResolver:
    """Body indent for one line, given the open blocks."""

    def __init__(self, classifier: LineClassifier) -> None:
        self.classifier = classifier

    def resolve(self, upper: str, stack: FrameStack) -> int:
        """Indent for this line. Mutates `stack` as blocks open/close."""
        top = stack.top
        current = top.body_indent if top else AREA_B_INDENT

        # ---- END-EXEC closes the SQL frame and returns to its column
        if END_EXEC_PATTERN.match(upper):
            frame = stack.pop(BLOCK_KIND_SQL)
            return frame.own_indent if frame else current

        # ---- inside EXEC SQL the generator owns the clause columns
        if top is not None and top.kind == BLOCK_KIND_SQL:
            if PRESERVE_SQL_BODY_INDENT:
                return PRESERVE_INDENT
            return top.body_indent

        # ---- scope terminators
        terminator = SCOPE_TERMINATOR_PATTERN.match(upper)
        if terminator:
            token = terminator.group("token").upper()
            kind = SCOPE_TERMINATORS.get(token, BLOCK_KIND_OTHER)
            frame = stack.pop(kind)
            return frame.own_indent if frame else AREA_B_INDENT

        # ---- a lone period closes the paragraph sentence
        if LONE_PERIOD_PATTERN.match(upper):
            stack.clear()
            return LONE_PERIOD_INDENT

        # ---- ELSE aligns with its IF
        if ELSE_PATTERN.match(upper):
            frame = stack.peek(BLOCK_KIND_IF)
            return frame.own_indent if frame else AREA_B_INDENT

        # ---- WHEN aligns against its EVALUATE
        if WHEN_PATTERN.match(upper):
            frame = stack.peek(BLOCK_KIND_EVALUATE)
            if frame:
                return frame.when_indent
            return AREA_B_INDENT + WHEN_OFFSET

        # ---- openers render at the current indent, then push
        if EXEC_SQL_START_PATTERN.match(upper):
            stack.push(BLOCK_KIND_SQL, current)
            return current

        if EVALUATE_START_PATTERN.match(upper):
            stack.push(BLOCK_KIND_EVALUATE, current)
            return current

        if IF_START_PATTERN.match(upper):
            if not self.classifier.is_self_closing(upper):
                stack.push(BLOCK_KIND_IF, current)
            return current

        if INLINE_PERFORM_PATTERN.match(upper):
            if not self.classifier.is_self_closing(upper):
                stack.push(BLOCK_KIND_PERFORM, current)
            return current

        if SCOPED_OPENER_PATTERN.match(upper):
            if self.classifier.opens_scope(upper):
                stack.push(BLOCK_KIND_OTHER, current)
            return current

        # ---- ordinary statement
        return current


__all__ = ["IndentResolver"]
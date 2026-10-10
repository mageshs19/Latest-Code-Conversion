"""THE pipeline. The order in this file IS the execution order.

ADD a stage     -> add one line
REMOVE a stage  -> delete one line
REORDER         -> move one line
DISABLE         -> enabled=False (stays documented, stops running)

ORDERING CONSTRAINTS (previously buried in prose comments):
  - output_write_placement  AFTER  child_fetch_early_stop
  - output_write_placement  BEFORE initialize_before_output
  - paragraph_terminator    LAST of the cleanup group
  - fixed_format            BEFORE resequence
"""

from __future__ import annotations

from converter.pipeline.stage import Stage, composer_stage

# --- imports kept local to each factory so a broken pass cannot stop import


def _counter_declaration():
    from converter.composers.counter_declaration_composer import (
        CounterDeclarationComposer,
    )
    return CounterDeclarationComposer()


def _cursor_close_guarantee():
    from converter.composers.cursor_close_guarantee_composer import (
        CursorCloseGuaranteeComposer,
    )
    return CursorCloseGuaranteeComposer()


def _procedure_indent():
    from converter.composers.procedure_indent_normalizer import (
        ProcedureIndentNormalizer,
    )
    return ProcedureIndentNormalizer()


PIPELINE: tuple[Stage, ...] = (
    composer_stage(
        "guarantee_cursor_close",
        "Ensure every opened cursor is actually closed",
        _cursor_close_guarantee,
    ),
    composer_stage(
        "declare_counters",
        "Declare referenced row counters and emit end-of-run totals",
        _counter_declaration,
    ),
    composer_stage(
        "normalise_procedure_indent",
        "Move PROCEDURE DIVISION statements to Area B",
        _procedure_indent,
    ),
)


def describe() -> list[str]:
    """One readable line per stage. Used by tools/pipeline_doc.py."""
    return [
        f"{i + 1:>2}. {s.name:<32} {'' if s.enabled else '[DISABLED] '}{s.description}"
        for i, s in enumerate(PIPELINE)
    ]


__all__ = ["PIPELINE", "describe"]
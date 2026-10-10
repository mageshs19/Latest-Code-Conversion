"""THE pipeline. Order in this file IS execution order.

ADD     -> one line.      REMOVE -> delete one line.
REORDER -> move one line. DISABLE -> enabled=False.

ORDERING CONSTRAINTS (from the composers' own docstrings):
  output_write_placement  AFTER  child_fetch_early_stop
  output_write_placement  BEFORE initialize_before_output
  paragraph_terminator    LAST of the cleanup group
  normalise_indent        BEFORE resequence
  cleanup_final_comments  AFTER  resequence (operates on numbered lines)

STATUS
  [LIVE]    registered AND removed from conversion_pipeline.py
  [PARKED]  registered but NOT yet wired - direct call still active
  [PHASE 2] needs ConversionComponentFactory dependencies
"""

from __future__ import annotations

from converter.pipeline.stage import Stage, composer_stage


# ---------------------------------------------------------------- Class A

def _cursor_order_cleanup():
    from converter.composers.cursor_order_cleanup_composer import (
        CursorOrderCleanupComposer,
    )
    return CursorOrderCleanupComposer()


def _update_restart_skip():
    from converter.composers.update_restart_skip_composer import (
        UpdateRestartSkipComposer,
    )
    return UpdateRestartSkipComposer()


def _cursor_close_guarantee():
    from converter.composers.cursor_close_guarantee_composer import (
        CursorCloseGuaranteeComposer,
    )
    return CursorCloseGuaranteeComposer()


def _output_write_paragraph():
    from converter.composers.output_write_paragraph_composer import (
        OutputWriteParagraphComposer,
    )
    return OutputWriteParagraphComposer()


def _counter_declaration():
    from converter.composers.counter_declaration_composer import (
        CounterDeclarationComposer,
    )
    return CounterDeclarationComposer()


def _procedure_indent():
    from converter.composers.procedure_indent_normalizer import (
        ProcedureIndentNormalizer,
    )
    return ProcedureIndentNormalizer()


def _unnecessary_comments():
    from converter.composers.unnecessary_comments_cleanup_composer import (
        UnnecessaryCommentsCleanupComposer,
    )
    return UnnecessaryCommentsCleanupComposer()


# ---------------------------------------------------------------- pipeline

PIPELINE: tuple[Stage, ...] = (
    # ---- CLEANUP GROUP -------------------------------------------------
    composer_stage(
        "cursor_order_cleanup",
        "[PARKED] Remove ORDER BY from parent cursors when configured",
        _cursor_order_cleanup,
    ),
    composer_stage(
        "update_restart_skip",
        "[PARKED] Replace unmappable restart blocks with a comment + CONTINUE",
        _update_restart_skip,
    ),
    composer_stage(
        "guarantee_cursor_close",
        "[PARKED] Ensure every opened cursor is actually closed",
        _cursor_close_guarantee,
    ),

    # ---- LAYOUT GROUP --------------------------------------------------
    composer_stage(
        "extract_output_write_paragraph",
        "[PARKED] Lift a guarded WRITE out of the per-row paragraph",
        _output_write_paragraph,
    ),
    composer_stage(
        "declare_counters",
        "[PARKED] Declare referenced row counters and emit end-of-run totals",
        _counter_declaration,
    ),
    composer_stage(
        "normalise_procedure_indent",
        "[PARKED] Move PROCEDURE DIVISION statements to Area B",
        _procedure_indent,
    ),
    composer_stage(
        "cleanup_final_comments",
        "[PARKED] Remove unnecessary comment blocks from numbered output",
        _unnecessary_comments,
    ),

    # ---- PHASE 2 - need ConversionComponentFactory dependencies ---------
    # materialise_records          RecordMaterialisationComposer
    # comment_unmapped_blocks      UnmappedRecordBlockComposer
    # apply_structural_safety      StructuralSafetyComposer
    # apply_late_date_conversion   LateDb2DateComposer
    # apply_layout                 ManualLayoutComposer / ManualStylePreserver
    # resequence                   FinalSequenceResequencerService
    # format_fixed_format          FixedFormatComposer
    # cobol_cleanup                CobolCleanupComposer
)


def describe() -> list[str]:
    return [
        f"{i + 1:>2}. {s.name:<32} {'' if s.enabled else '[DISABLED] '}{s.description}"
        for i, s in enumerate(PIPELINE)
    ]


__all__ = ["PIPELINE", "describe"]
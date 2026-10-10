"""THE pipeline. Order in this file IS execution order.

ADD     -> one line.      REMOVE -> delete one line.
REORDER -> move one line. DISABLE -> enabled=False.

STATUS
  [LIVE]   the owning method delegates via run_stage(); composer is
           constructed here, not at the call site
  [PARKED] registered but disabled; the direct call is still active in
           conversion_pipeline.py

WARNING
  A stage marked [LIVE] whose call site delegates to run_stage() MUST
  be enabled. Disabling it makes the pass silently stop running, and
  the row/column baseline will not notice.
"""

from __future__ import annotations

from converter.pipeline.stage import Stage, composer_stage


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


PIPELINE: tuple[Stage, ...] = (
    # ---- still called directly in conversion_pipeline.py ---------------
    composer_stage(
        "cursor_order_cleanup",
        "[PARKED] Remove ORDER BY from parent cursors when configured",
        _cursor_order_cleanup,
        enabled=False,
    ),
    composer_stage(
        "update_restart_skip",
        "[PARKED] Replace unmappable restart blocks with a comment + CONTINUE",
        _update_restart_skip,
        enabled=False,
    ),
    composer_stage(
        "guarantee_cursor_close",
        "[PARKED] Ensure every opened cursor is actually closed",
        _cursor_close_guarantee,
        enabled=False,
    ),

    # ---- delegated via run_stage() - MUST stay enabled ------------------
    composer_stage(
        "extract_output_write_paragraph",
        "[LIVE] Lift a guarded WRITE out of the per-row paragraph",
        _output_write_paragraph,
    ),
    composer_stage(
        "declare_counters",
        "[LIVE] Declare referenced row counters and emit end-of-run totals",
        _counter_declaration,
    ),
    composer_stage(
        "normalise_procedure_indent",
        "[LIVE] Move PROCEDURE DIVISION statements to Area B",
        _procedure_indent,
    ),
    composer_stage(
        "cleanup_final_comments",
        "[LIVE] Remove unnecessary comment blocks from numbered output",
        _unnecessary_comments,
    ),
)


def describe() -> list[str]:
    return [
        f"{i + 1:>2}. {s.name:<32} {'' if s.enabled else '[DISABLED] '}{s.description}"
        for i, s in enumerate(PIPELINE)
    ]


__all__ = ["PIPELINE", "describe"]
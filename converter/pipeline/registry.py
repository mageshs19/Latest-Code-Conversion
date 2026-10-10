"""THE pipeline. Order in this file IS execution order.

ADD     -> one line.      REMOVE -> delete one line.
REORDER -> move one line. DISABLE -> enabled=False.

STATUS
  [LIVE]   runs through run_pipeline(); direct call removed
  [PARKED] registered but disabled; direct call still active
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
    composer_stage(
        "extract_output_write_paragraph",
        "[PARKED] Lift a guarded WRITE out of the per-row paragraph",
        _output_write_paragraph,
        enabled=False,
    ),
    composer_stage(
        "declare_counters",
        "[PARKED] Declare referenced row counters and emit end-of-run totals",
        _counter_declaration,
        enabled=False,
    ),
    composer_stage(
        "normalise_procedure_indent",
        "[PARKED] Move PROCEDURE DIVISION statements to Area B",
        _procedure_indent,
        enabled=False,
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
"""THE pipeline. Order in this file IS execution order.

ADD     -> one line.      REMOVE -> delete one line.
REORDER -> move one line. DISABLE -> enabled=False.

STATUS
  [LIVE]   the owning call site delegates via run_stage(); the composer
           is constructed HERE, not taken from the factory dict
  [PARKED] registered but disabled; a direct call is still active

WARNING
  A stage whose call site delegates to run_stage() MUST be enabled.
  Disabling it makes the pass silently stop running, and the row/column
  baseline will not notice. tools/baseline.ps1 guard 3 checks the log
  for evidence that key passes actually fired.

CURRENT STATE
  All eight stages are LIVE. Every direct composer call for these passes
  has been removed from conversion_pipeline.py and
  conversion_layout_steps.py.

ORDER NOTE
  While migrating, call POSITION is still owned by the call sites, so the
  order below is documentation rather than execution order. After the
  Phase B collapse - finish() replaced by a single run_pipeline() call -
  this tuple becomes the single source of truth for order as well.

DUPLICATE CALLS (pre-existing, behaviour preserved)
  'update_restart_skip'   runs twice: after statement transformation and
                          again in the cleanup group.
  'cursor_order_cleanup'  runs twice inside _apply_db2_infrastructure.
  Both composers are idempotent. Removing either call is a separate,
  baselined change.
"""

from __future__ import annotations

from converter.pipeline.stage import Stage, composer_stage


# ---------------------------------------------------------------------
# Factories. Imports are local so a broken composer cannot stop this
# module from importing, and so the registry stays cheap to load.
#
# A factory takes NO arguments and returns an object exposing
#   .compose(text) -> str
#   .messages      -> list[str]
# composer_stage() does the document plumbing.
# ---------------------------------------------------------------------

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


def _move_alignment():
    from converter.composers.move_alignment_composer import (
        MoveAlignmentComposer,
    )
    return MoveAlignmentComposer()


def _unnecessary_comments():
    from converter.composers.unnecessary_comments_cleanup_composer import (
        UnnecessaryCommentsCleanupComposer,
    )
    return UnnecessaryCommentsCleanupComposer()


# ---------------------------------------------------------------------
# The pipeline
# ---------------------------------------------------------------------

PIPELINE: tuple[Stage, ...] = (
    # ---- CONTENT PHASE - conversion_pipeline.py ------------------------
    composer_stage(
        "update_restart_skip",
        "[LIVE] Replace unmappable restart blocks with a comment + CONTINUE",
        _update_restart_skip,
    ),
    composer_stage(
        "cursor_order_cleanup",
        "[LIVE] Remove ORDER BY from parent cursors when configured",
        _cursor_order_cleanup,
    ),
    composer_stage(
        "guarantee_cursor_close",
        "[LIVE] Ensure every opened cursor is opened, driven and closed",
        _cursor_close_guarantee,
    ),

    # ---- FINISHING PHASE - conversion_layout_steps.py ------------------
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
    # Must follow normalise_procedure_indent: runs form on settled
    # indents. Must precede the resequence: joining a split MOVE removes
    # a physical line and leaves a gap in columns 1-6 / 73-80.
    composer_stage(
        "move_alignment",
        "[LIVE] Align TO across runs of MOVE statements",
        _move_alignment,
    ),
    composer_stage(
        "cleanup_final_comments",
        "[LIVE] Remove unnecessary comment blocks from numbered output",
        _unnecessary_comments,
    ),
)


def describe() -> list[str]:
    """One readable line per stage. Printed by tools/pipeline_doc.py."""
    return [
        f"{i + 1:>2}. {s.name:<32} {'' if s.enabled else '[DISABLED] '}{s.description}"
        for i, s in enumerate(PIPELINE)
    ]


__all__ = ["PIPELINE", "describe"]
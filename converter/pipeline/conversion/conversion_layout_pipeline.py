# LOCATION: converter/pipeline/conversion/conversion_layout_pipeline.py
# ACTION: REPLACE ENTIRE FILE

"""Finishing phase of the IDMS->DB2 conversion.

Takes converted COBOL whose CONTENT is final and decides how it is laid
out: sequencing, paragraph extraction, counters, restart control,
comment blocks, structural safety, Area-B indentation and the final
resequence.

This class owns the ORDERING CONTRACT only. Each pass lives in
ConversionLayoutSteps, so a pass can be tested in isolation and the order
can be read in one screen.

CORRECTION - inject_restart_control was called TWICE

    The pass ran once after declare_counters and again after
    normalize_indentation. The composer is idempotent so the text
    survived, but the second call violated the ordering contract: the
    generated paragraphs must be indented, separated and resequenced
    WITH everything else, not after the indent pass has already run.
    It also emitted every restart diagnostic twice, which makes a log
    unreadable and a duplicated defect look like two defects.
"""

from __future__ import annotations

from collections.abc import Callable

from converter.pipeline.conversion.conversion_layout_steps import (
    ConversionLayoutSteps,
)
from converter.generators.converter_pipeline_integration import (
    ConverterEnhancementPipeline,
)


class ConversionLayoutPipeline:
    """Runs the layout and finishing passes, in a fixed, load-bearing order.

    Pass-ordering contracts
    -----------------------
    2. ``fixed_format`` sequences every line, including generator-inserted
       blocks. It runs BEFORE any comment is emitted, so comment lines
       cannot be collapsed - at this point they do not exist yet.

    3. ``OutputWriteParagraphComposer`` extracts the record-population body
       into its own ``WRITE-<record>`` paragraph and replaces it with a
       PERFORM plus the output counter increment. It MUST run after:

         - the content phase's OutputWritePlacementCleanup, otherwise it
           extracts from the wrong paragraph and bakes in the
           once-per-child-row defect;
         - ``fixed_format``, otherwise it has no sequence area to clone
           when building the new paragraph header.

    4. ``LateDb2DateComposer`` re-runs the DB2 date and INITIALIZE passes.
       Those live inside ``feedback_cleanup`` and have already finished by
       the time step 3 moves the block into a brand new paragraph, so
       without this second run a DB2 date host field is moved straight into
       the output record, skipping the CCYYMMDD realignment. That is silent
       data corruption, not a formatting defect. Idempotent: a converted
       move carries no DCLGEN qualifier and cannot match again.

    5. ``CounterDeclarationComposer`` declares every ``WS-NB-*-COUNT`` the
       PROCEDURE DIVISION increments but WORKING-STORAGE does not define,
       and appends the end-of-run totals before STOP RUN. It MUST run after
       step 3, which is what emits the increment, and BEFORE step 7 so the
       generated DISPLAY lines are indented with everything else.

    5b. ``RestartStageAdapter`` injects the restart family into an UPDATE
       program that keeps a checkpoint: legacy cleanup, mainline, reader,
       business paragraph and the eight restart paragraphs.

       MUST run AFTER step 5 - the mainline splices the totals that pass
       produced. MUST run BEFORE step 7 - the generated paragraphs carry
       relative indent only and have to be aligned, separated and
       resequenced with everything else.

       EXACTLY ONCE. A second call re-runs the whole injection on
       already-laid-out text and duplicates every diagnostic.

       A retrieval program, a program with no checkpoint record, or one
       whose restart role is incomplete is returned unchanged WITH a
       reason. Half a restart family is worse than none.

    6. ``UnmappedRecordBlockComposer`` comments record-level blocks that
       have no usable DB2 column mapping. Runs after every content pass so
       it never comments code another pass still needs to read.

    6b. ``StructuralSafetyComposer`` is the LAST guard before indentation.
       It comments whole-record references whose IDMS layout no longer
       exists, and statements left unreachable after a paragraph EXIT.
       It MUST run after step 6 - an unmapped-record block is commented
       first, so the safety pass never re-comments the same lines - and
       BEFORE step 7, so its comment lines are indented with everything
       else.

    7. ``ProcedureIndentNormalizer`` re-anchors Area B, covering the
       paragraph created in step 3, the totals added in step 5, the
       restart paragraphs added in step 5b and the comments added in
       step 6b.

    8. ``FinalSequenceResequencerService`` rewrites columns 1-6 and 73-80,
       correcting the placeholder sequence numbers cloned in steps 3, 5,
       5b and 6b.
    """

    def __init__(
        self,
        *,
        composers: dict,
        resolvers: dict,
        component_messages: Callable[[object], list[str]],
        steps: ConversionLayoutSteps | None = None,
        restart_context=None,
    ) -> None:
        # Run-scoped. Built by ConversionPipeline, which can see the
        # source, the DCLGEN columns and the program kind; finish() can
        # see none of those.
        self.restart_context = restart_context
        self.steps = steps or ConversionLayoutSteps(
            composers=composers,
            resolvers=resolvers,
            component_messages=component_messages,
        )

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def finish(
        self,
        *,
        converted_cobol: str,
        original_idms_text: str,
        validation_messages: list[str],
    ) -> str:
        steps = self.steps

        converted_cobol = steps.apply_layout(
            converted_cobol=converted_cobol,
            original_idms_text=original_idms_text,
        )
        converted_cobol = steps.extract_output_write_paragraph(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.apply_late_date_conversion(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.materialise_records(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.declare_counters(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )

        # 5b. Restart control. ONCE, here - see the class docstring.
        converted_cobol = steps.inject_restart_control(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
            restart_context=self.restart_context,
        )

        converted_cobol = steps.comment_unmapped_blocks(
            converted_cobol=converted_cobol,
            original_idms_text=original_idms_text,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.apply_structural_safety(
            converted_cobol=converted_cobol,
            original_idms_text=original_idms_text,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.normalize_indentation(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.align_moves(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.separate_paragraphs(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )
        converted_cobol = steps.resequence(converted_cobol)

        # Final cleanup: remove unnecessary comments from fixed-format output
        converted_cobol = steps.cleanup_final_comments(
            converted_cobol=converted_cobol,
            validation_messages=validation_messages,
        )

        # Production COBOL standards (centralized initialization,
        # organized WORKING-STORAGE).
        try:
            enhancement_pipeline = ConverterEnhancementPipeline(
                converted_cobol,
                program_id=None,
            )
            converted_cobol = enhancement_pipeline.execute()
        except Exception as exc:  # noqa: BLE001
            validation_messages.append(
                f"Enhancement pipeline FAILED and was skipped: "
                f"{type(exc).__name__}: {exc}"
            )

        return converted_cobol


__all__ = ["ConversionLayoutPipeline"]
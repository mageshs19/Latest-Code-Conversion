# LOCATION: converter/pipeline/conversion/conversion_pipeline_steps.py
# ACTION: CREATE NEW FILE

"""Helper steps for the CONTENT phase of the IDMS->DB2 conversion.

ConversionPipeline owns pass ORDER. This mixin owns what each step does.
Splitting them keeps the order readable in one screen and lets a step be
tested without constructing the whole pipeline.

CORRECTION 1 - the legacy stand-down could never fire
-----------------------------------------------------
``GATE_LEGACY_RESTART_GENERATOR`` was False, so::

    if GATE_LEGACY_RESTART_GENERATOR and restart_context is not None:

was unreachable and BOTH restart generators ran on every program. The
metadata-driven pass emits 710-/720- handlers; the legacy pass emits
``PERFORM 810-``/``820-``. Measured on VMDZ1567: 710-/720- scored 2 each
(defined and performed), 810-/820- scored 1 each (performed only). A
PERFORM of a paragraph that does not exist is IGYPS2072-S.

CORRECTION 2 - the program kind was read from the INPUT
--------------------------------------------------------
``is_update=self._program_is_update(conversion_input)``. ConversionInput
carries paths and parsed metadata; it has never carried the IDMS write
verbs. Once the workspace was flattened to one Program folder the
input's only kind signal disappeared and EVERY program resolved to
retrieval, so update programs silently lost restart control, their
COMMIT and their business UPDATE.

The kind is now MEASURED from the expanded source, once, and every
consumer is TOLD. Two classifiers eventually disagree, and the
disagreement is invisible until a cleanup pass deletes the COMMIT the
restart pass just injected.
"""

from __future__ import annotations

from converter.domain.models import ConversionInput
from converter.pipeline.run import run_stage
from converter.pipeline.stage import Document
from converter.resolvers.program_kind_resolver import ProgramKindResolver
from rules.program_kind_rules import KIND_UPDATE

# Module path of the resolver that turns DCLGEN columns into a restart
# DclgenRoleInfo. Imported lazily and REPORTED when absent, so a wrong
# path names itself instead of crashing a conversion.
RESTART_DCLGEN_MODULE = "converter.postprocess.update_restart_dclgen_resolver"
RESTART_DCLGEN_CLASS = "UpdateRestartDclgenResolver"

# When a metadata-driven restart context exists, the LEGACY restart
# generator stands down. Two generators writing restart infrastructure
# into one program injected the DZ01RSTV DCLGEN twice, which duplicates
# every data name in the group - a hard compile error.
#
# Set False to run both and compare output. The log states which
# generator owned each program either way.
GATE_LEGACY_RESTART_GENERATOR = True
LEGACY_RESTART_SKIPPED = (
    "Restart: legacy paragraph generator skipped; the metadata-driven "
    "restart pass owns this program."
)

# One classifier, consulted once. Any composer that needs the kind is
# TOLD, never left to work it out again.
PROGRAM_KIND_ATTRIBUTE = "program_kind"
PROGRAM_KIND_HANDOFF_OK = "Program kind: handed '{kind}' to {component}."
PROGRAM_KIND_HANDOFF_REFUSED = (
    "Program kind: {component} does not accept a program kind; it will "
    "classify independently and may disagree."
)
COMMIT_CLEANUP_MISSING = (
    "Retrieval cleanup: composer is not registered; a COMMIT in a "
    "read-only program will not be removed."
)
DATE_COMPARE_MISSING = (
    "DB2 date compare: composer is not registered; DATE host "
    "comparisons will not be realigned."
)


class ConversionPipelineSteps:
    """What each content-phase step does. Order lives in the pipeline."""

    # ------------------------------------------------------------------
    # Registry helper
    # ------------------------------------------------------------------
    @staticmethod
    def _stage(
        name: str,
        converted_cobol: str,
        validation_messages: list[str],
    ) -> str:
        """Run one registered stage and drain its diagnostics.

        A disabled stage is a no-op. An unknown name is reported as an
        [error] message rather than silently dropping the pass.
        """
        doc = run_stage(name, Document(cobol=converted_cobol))
        validation_messages.extend(doc.messages)
        return doc.cobol

    # ------------------------------------------------------------------
    # Program kind
    # ------------------------------------------------------------------
    def _resolve_program_kind(
        self,
        *,
        conversion_input: ConversionInput,
        source_text: str,
        validation_messages: list[str],
    ) -> str:
        """Measure UPDATE vs RETRIEVAL from the EXPANDED source."""
        declared = getattr(conversion_input, "is_update", None)
        if declared is None:
            declared = self._input_declares_update(conversion_input)

        kind, messages = ProgramKindResolver().resolve(
            source_text=source_text,
            input_says_update=declared,
        )
        validation_messages.extend(messages)
        return kind

    def _input_declares_update(
        self,
        conversion_input: ConversionInput,
    ) -> bool | None:
        """What the input believes, or None when it is silent.

        Kept so an input that genuinely knows can still PROMOTE a
        program. It can no longer demote one.
        """
        probe = getattr(self, "_program_is_update", None)
        if not callable(probe):
            return None
        try:
            return bool(probe(conversion_input))
        except Exception:  # noqa: BLE001
            return None

    def _hand_off_program_kind(
        self,
        *,
        component,
        component_name: str,
        program_kind: str,
        validation_messages: list[str],
    ) -> None:
        """Tell a composer the kind, or report that it will guess."""
        if component is None:
            return

        if not hasattr(component, PROGRAM_KIND_ATTRIBUTE):
            validation_messages.append(
                PROGRAM_KIND_HANDOFF_REFUSED.format(component=component_name)
            )
            return

        try:
            setattr(component, PROGRAM_KIND_ATTRIBUTE, program_kind)
        except Exception:  # noqa: BLE001
            validation_messages.append(
                PROGRAM_KIND_HANDOFF_REFUSED.format(component=component_name)
            )
            return

        validation_messages.append(
            PROGRAM_KIND_HANDOFF_OK.format(
                kind=program_kind, component=component_name
            )
        )

    # ------------------------------------------------------------------
    # Restart context
    # ------------------------------------------------------------------
    def _restart_dclgen_resolver(self, validation_messages: list[str]):
        """The resolver that turns DCLGEN columns into a restart role.

        Imported lazily and by NAME. A wrong path is reported with the
        path it tried and the conversion continues without restart,
        instead of aborting every program in the batch.
        """
        try:
            module = __import__(
                RESTART_DCLGEN_MODULE, fromlist=[RESTART_DCLGEN_CLASS]
            )
            return getattr(module, RESTART_DCLGEN_CLASS)()
        except Exception as exc:  # noqa: BLE001
            validation_messages.append(
                "Restart context: the restart DCLGEN resolver was not "
                f"available at {RESTART_DCLGEN_MODULE}."
                f"{RESTART_DCLGEN_CLASS} ({type(exc).__name__}: {exc}); "
                "no restart control will be injected."
            )
            return None

    def _restart_context(
        self,
        *,
        conversion_input: ConversionInput,
        source_text: str,
        program_kind: str,
        validation_messages: list[str],
    ):
        """Build the run-scoped restart context, or None with a reason."""
        from converter.resolvers.restart_context_builder import (
            RestartContextBuilder,
        )

        builder = RestartContextBuilder(
            dclgen_resolver=self._restart_dclgen_resolver(validation_messages),
        )
        context, messages = builder.build(
            source_text=source_text,
            dclgen_columns=conversion_input.dclgen_columns,
            is_update=(program_kind == KIND_UPDATE),
        )
        validation_messages.extend(messages)
        return context

    def _apply_legacy_restart_generator(
        self,
        *,
        converted_cobol: str,
        conversion_input: ConversionInput,
        operations: list,
        generators: dict,
        restart_context,
        validation_messages: list[str],
    ) -> str:
        """The LEGACY restart path, run only when nothing better can.

        A retrieval program still yields a context - one whose kind is
        'retrieval' - so this guard skips the legacy generator for
        read-only programs too. That matches the previous behaviour,
        where it ran but did nothing.
        """
        if GATE_LEGACY_RESTART_GENERATOR and restart_context is not None:
            validation_messages.append(LEGACY_RESTART_SKIPPED)
            return converted_cobol

        converted_cobol, select_messages = generators["select_paragraph"].apply(
            cobol_text=converted_cobol,
            program_id=conversion_input.target_program_id,
            operations=operations,
        )
        validation_messages.extend(select_messages)
        return converted_cobol

    # ------------------------------------------------------------------
    # DB2 infrastructure and cursor passes
    # ------------------------------------------------------------------
    def _apply_db2_infrastructure(
        self,
        *,
        converted_cobol: str,
        operations: list,
        generators: dict,
        composers: dict,
        validation_messages: list[str],
    ) -> str:
        converted_cobol, infrastructure_messages = generators[
            "db2_infrastructure"
        ].apply(cobol_text=converted_cobol, operations=operations)
        validation_messages.extend(infrastructure_messages)

        # MIGRATED -> registry stage 'cursor_order_cleanup' (call 1 of 2)
        converted_cobol = self._stage(
            "cursor_order_cleanup", converted_cobol, validation_messages
        )

        converted_cobol, cursor_messages = generators[
            "cursor_paragraph"
        ].apply(cobol_text=converted_cobol, operations=operations)
        validation_messages.extend(cursor_messages)

        # LRF host variable population
        if hasattr(
            generators["cursor_paragraph"], "augment_lrf_procedure_division"
        ):
            converted_cobol, lrf_messages = generators[
                "cursor_paragraph"
            ].augment_lrf_procedure_division(converted_cobol)
            validation_messages.extend(lrf_messages)

        # ------------------------------------------------------------------
        # Flow-Bucket Orchestration - REMOVED 10-10-2026
        #
        # The pass never executed: it read raw lines without stripping the
        # 6-digit COBOL sequence area, so _parse_program_sections() could
        # not find WORKING-STORAGE and it logged "No WORKING-STORAGE
        # SECTION found - skipping orchestration" on every program. All
        # five of its stated goals are already delivered by fixed-format
        # aware passes, verified on VMDZ7200:
        #     cursor flags + 88 levels -> db2_infrastructure_generator
        #     NNNN / TS-TIMESTAMP      -> timestamp_generator
        #     WS section markers       -> infrastructure block builder
        # ------------------------------------------------------------------

        # Cursor driving flow.
        converted_cobol = composers["cursor_flow"].compose(converted_cobol)
        validation_messages.extend(
            self._component_messages(composers["cursor_flow"])
        )

        # ------------------------------------------------------------------
        # Cursor close guarantee: the FETCH paragraph is driven UNTIL
        # <cursor>-EOC, the CLOSE paragraph is performed, and the fetched
        # row reaches the business paragraph.
        # ------------------------------------------------------------------
        converted_cobol = self._stage(
            "guarantee_cursor_close", converted_cobol, validation_messages
        )

        converted_cobol = composers["sqlcode_cleanup"].compose(converted_cobol)
        validation_messages.extend(
            self._component_messages(composers["sqlcode_cleanup"])
        )

        # MIGRATED -> registry stage 'cursor_order_cleanup' (call 2 of 2)
        converted_cobol = self._stage(
            "cursor_order_cleanup", converted_cobol, validation_messages
        )

        # ------------------------------------------------------------------
        # DB2 DATE comparison realignment.
        #
        # A DB2 DATE host is DD.MM.CCYY, 10 bytes. A COBOL date field is
        # CCYYMMDD, PIC 9(8). Comparing them directly compares '0' against
        # '2' and selects the wrong rows, so this pass must be visible in
        # the log whether it fires or not.
        # ------------------------------------------------------------------
        date_compare = composers.get("date_compare")

        if date_compare is None:
            validation_messages.append(DATE_COMPARE_MISSING)
        else:
            converted_cobol = date_compare.compose(converted_cobol)
            validation_messages.extend(
                self._component_messages(date_compare)
            )

        return converted_cobol

    # ------------------------------------------------------------------
    # Cleanup passes
    # ------------------------------------------------------------------
    def _apply_cleanup_composers(
        self,
        *,
        converted_cobol: str,
        composers: dict,
        validation_messages: list[str],
    ) -> str:
        """Content-level cleanup, before any layout decision is taken.

        feedback_cleanup == CobolCleanupComposer. It runs
        OutputWritePlacementCleanup, which moves the guarded output WRITE
        out of the child-row paragraph into the parent paragraph. The
        paragraph EXTRACTION in the finishing phase depends on that
        relocation having already happened.
        """
        for name in (
            "feedback_cleanup",
            "unnecessary_comments_cleanup",
            "update_program_feedback",
        ):
            converted_cobol = composers[name].compose(converted_cobol)
            validation_messages.extend(
                self._component_messages(composers[name])
            )

        # MIGRATED -> registry stage 'update_restart_skip' (call 2 of 2)
        converted_cobol = self._stage(
            "update_restart_skip", converted_cobol, validation_messages
        )

        return converted_cobol

    def _apply_commit_cleanup(
        self,
        *,
        converted_cobol: str,
        composers: dict,
        program_kind: str,
        validation_messages: list[str],
    ) -> str:
        """Remove a COMMIT from a read-only program - and only then.

        The restart pass injects a COMMIT into an update program. If this
        composer classifies independently it will delete that COMMIT and
        the checkpoint will never be committed, so it is told the kind.
        """
        commit_cleanup = composers.get("retrieval_commit_cleanup")

        if commit_cleanup is None:
            validation_messages.append(COMMIT_CLEANUP_MISSING)
            return converted_cobol

        self._hand_off_program_kind(
            component=commit_cleanup,
            component_name="retrieval_commit_cleanup",
            program_kind=program_kind,
            validation_messages=validation_messages,
        )
        converted_cobol = commit_cleanup.compose(converted_cobol)
        validation_messages.extend(
            self._component_messages(commit_cleanup)
        )
        return converted_cobol


__all__ = [
    "ConversionPipelineSteps",
    "RESTART_DCLGEN_MODULE",
    "RESTART_DCLGEN_CLASS",
    "GATE_LEGACY_RESTART_GENERATOR",
    "LEGACY_RESTART_SKIPPED",
    "PROGRAM_KIND_ATTRIBUTE",
]
# LOCATION: converter/pipeline/conversion/conversion_pipeline.py
# ACTION: REPLACE ENTIRE FILE
from __future__ import annotations

import os

from converter.analyzers.program_flow_analyzer import ProgramFlowAnalyzer
from converter.domain.models import ConversionInput
from converter.pipeline.conversion.conversion_layout_pipeline import (
    ConversionLayoutPipeline,
)
from converter.pipeline.conversion.conversion_pipeline_steps import (  # noqa: F401
    GATE_LEGACY_RESTART_GENERATOR,
    LEGACY_RESTART_SKIPPED,
    RESTART_DCLGEN_CLASS,
    RESTART_DCLGEN_MODULE,
    ConversionPipelineSteps,
)
from converter.validators.mapping_scope_filter import MappingScopeFilter
from converter.validators.mapping_validator import MappingValidator

# ----------------------------------------------------------------------
# LRF stage vocabulary
#
# These are message TEMPLATES and factory KEYS, kept here beside the only
# code that uses them, matching the literals this module already carried.
# They belong in rules/lrf_conversion_rules.py once that module owns the
# pipeline-side vocabulary as well as the transformer-side vocabulary.
# ----------------------------------------------------------------------
TRANSFORMER_LRF_PATH_EXPANDER = "lrf_path_expander"
TRANSFORMER_LRF_UPDATE_EXPANDER = "lrf_update_expander"
TRANSFORMER_LR_STATUS_REPLACER = "lr_status_token_replacer"

LABEL_LRF_READ = "LRF expansion"
LABEL_LRF_UPDATE = "LRF update expansion"
LABEL_LR_STATUS = "LR-STATUS tokens"

METHOD_EXPAND = "expand"
METHOD_APPLY = "apply"

LRF_STAGE_NOT_WIRED_TEMPLATE = (
    "{label}: no component was wired under '{key}'; the logical-record "
    "syntax it owns will reach the output unconverted."
)
LRF_STAGE_NO_METHOD_TEMPLATE = (
    "{label}: the component wired under '{key}' has no {method}() method; "
    "the stage was skipped."
)
LRF_STAGE_FAILED_TEMPLATE = (
    "{label}: skipped, the text from the previous stage will be used. "
    "Reason: {reason}"
)


class ConversionPipeline(ConversionPipelineSteps):
    """Runs the CONTENT phase of the IDMS->DB2 conversion.

    Depends on the host class for the component factory methods and message
    helpers (via mixins). Returns (converted_cobol, operations,
    dclgen_repository); validation messages are appended to the passed-in
    list.

    The FINISHING phase - layout, paragraph extraction, counters, restart
    control, indent and resequencing - lives in ConversionLayoutPipeline.
    That split keeps the two concerns testable in isolation: this class
    decides WHAT the program says, that class decides HOW it is laid out.

    WHAT each step does lives in ConversionPipelineSteps. This file owns
    ORDER, and only order.

    Pass-ordering contracts (content phase)
    ---------------------------------------
    0a. LOGICAL RECORD EXPANSION. THREE stages, in this order, all inside
        ``_expand_logical_records``:

        1. ``LrfPathExpander``  - the READ and DELETE side::

               OBTAIN FIRST <LR> WHERE <keyword> -> OBTAIN FIRST <rec> WITHIN <set>
               ERASE <LR> WHERE <keyword>        -> ERASE <rec>
               FIELD OF <rec> OF LR              -> FIELD OF <rec>

        2. ``LrfUpdateExpander`` - the WRITE side::

               MODIFY <LR> WHERE <keyword>       -> MODIFY <rec>
               STORE  <LR> WHERE <keyword>       -> STORE <rec>

        3. ``LrStatusTokenReplacer`` - the status literals both expanders
           may leave behind::

               LR-STATUS = 'X-EOA'               -> DB-END-OF-SET -> SQLCODE = 100

        Stage 3 MUST run last: it consumes tokens the first two emit.

        The group MUST run first in the pipeline, because the PROGRAM KIND
        resolver, MappingScopeFilter, CobolTransformer and
        ProgramFlowAnalyzer all read the source text. Every pass after this
        point sees classic IDMS and needs no logical-record knowledge.

    0b. ``ProgramKindResolver`` measures UPDATE vs RETRIEVAL from the
        EXPANDED source. After 0a, because the update-side LRF forms are
        rewritten in stage 2 above; before statement transformation, which
        removes the write verbs entirely.

    0c. ``MappingScopeFilter`` rescopes the mapping validation report to the
        program being converted. MappingValidator audits the WHOLE Sheet
        Mapping workbook, so a restart-table gap was reported as a blocking
        error against every retrieval program that never touches it. A gap
        stays an error for a table this program references, and becomes a
        workbook note for any other.

    1.  ``feedback_cleanup`` (CobolCleanupComposer) runs
        ``OutputWritePlacementCleanup``, which lifts a guarded output WRITE
        out of the child-row paragraph into the PARENT paragraph, after the
        child cursor CLOSE. Left in the child-row paragraph the WRITE fires
        once per fetched child row instead of once per parent row.

    Steps 2 through 8 are owned by ConversionLayoutPipeline and documented
    there.

    CORRECTION 1 - THE WRITE SIDE WAS DOCUMENTED BUT NEVER RUN
    ----------------------------------------------------------
    Contract 0b used to claim the update-side LRF forms "are rewritten
    there", meaning by LrfPathExpander in 0a. That expander carries exactly
    three patterns - OBTAIN, OBTAIN continued, ERASE. It has never held a
    MODIFY or a STORE pattern, so an Update-with-LRF program kept::

        STORE  VMBTL07-R01 WHERE ST-VMBEVEF.
        MODIFY VMBTL07-R01 WHERE MO-VMBEVEF.

    all the way to the output, while the run log reported::

        LRF expansion: expanded 1 statement(s), skipped 0.

    "skipped 0" was not reassurance. A statement is only counted as skipped
    once it has MATCHED an LR pattern and then been refused. MODIFY and
    STORE matched nothing, so they were never seen as logical-record
    statements and never counted at all.

    ``LrfUpdateExpander`` had already been written and unit-tested for
    exactly these two verbs. It had no call site anywhere in the
    composition root - only in its own test module. Stage 2 above is that
    missing call site. The docstring claim is now true.

    CORRECTION 2 - THREE SILENT EXITS
    ---------------------------------
    ``_expand_logical_records`` returned the unmodified source whenever a
    transformer key was absent from the factory dict, and said nothing::

        expander = transformers.get("lrf_path_expander")
        if expander is None:
            return source_text          # no message

    A pass that was never WIRED is not the same thing as a program with no
    logical records, and silence cannot tell those apart. That is the same
    failure mode already recorded against the bare ``except Exception:
    pass`` that hid the LRF populator for three conversion cycles. Every
    stage now reports a missing component, a missing method, and a raised
    exception, and drains the component's own messages in all three cases.

    PROGRAM KIND - MEASURED, NOT CONFIGURED
    ---------------------------------------
    The kind used to come from ``self._program_is_update(conversion_input)``.
    ConversionInput carries paths and parsed metadata; it has never carried
    the IDMS write verbs. Once the workspace was flattened to a single
    Program folder - "One Program folder. No Retrieval / Update split" -
    the input's only kind signal disappeared and EVERY program resolved to
    retrieval. Update programs then silently lost restart control, their
    COMMIT and their business UPDATE, and the run log reported "Retrieval
    DB2 COBOL generation completed." for all of them.

    The kind is now measured from the source, ONCE, and handed to every
    consumer that needs it. The input may still PROMOTE a program to
    update; it may not demote one whose source carries a write verb.

    RESTART CONTEXT
    ---------------
    The restart pass is run by the FINISHING phase, but its context can
    only be built HERE: finish() receives text and messages, never the
    conversion input, the DCLGEN columns or the program kind. The context
    is therefore built from the EXPANDED source - the checkpoint record
    is IDMS syntax and must be seen before it is converted away - and
    handed to ConversionLayoutPipeline through its constructor.

    The checkpoint record is written with the CLASSIC form - ``MODIFY
    FFRECAB``, ``STORE FFRECAB`` - which carries no ``WHERE <keyword>``
    clause. LR_MODIFY_WHERE_PATTERN requires that clause, so stage 2
    cannot match a checkpoint operation and restart handling is
    structurally out of its reach.

    TWO RESTART GENERATORS, ONE OWNER
    ---------------------------------
    ``SelectParagraphGenerator`` is the LEGACY restart path. It hardcoded
    the restart table, column and host names because it never read a
    DCLGEN, and it injected its own DZ01RSTV include and working storage.
    The metadata-driven pass (restart_injection, step 5b of the finishing
    phase) resolves every name from Sheet Mapping, DCLGEN and the program
    source, and MEASURES the checkpoint payload from the restart record
    layout - the value the legacy path guessed at 1215.

    Running both duplicated the DZ01RSTV include and left a PERFORM of a
    deleted handler. The legacy generator stands down whenever a restart
    context exists. See GATE_LEGACY_RESTART_GENERATOR.

    REGISTRY MIGRATION
    ------------------
    Passes marked MIGRATED are defined in converter/pipeline/registry.py
    and executed through run_stage(). The composer is constructed by the
    registry, not taken from the factory dict. Call POSITION is still
    owned by this file.

    OBSERVED DUPLICATE CALLS (behaviour preserved, not yet changed)
    ---------------------------------------------------------------
      * ``update_restart_skip`` runs twice: once after statement
        transformation and again in the cleanup group.
      * ``cursor_order_cleanup`` runs twice inside
        ``_apply_db2_infrastructure``.
    Both composers are idempotent, so output is unaffected.
    """

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def _run_pipeline(
        self,
        *,
        conversion_input: ConversionInput,
        validation_messages: list[str],
    ) -> tuple[str, list, object]:
        repositories = self._repositories(conversion_input)
        resolvers = self._resolvers(repositories)
        generators = self._generators(
            repositories=repositories,
            resolvers=resolvers,
        )
        transformers = self._transformers(
            repositories=repositories,
            resolvers=resolvers,
            generators=generators,
        )
        composers = self._composers(
            repositories=repositories,
            resolvers=resolvers,
        )

        # --- 0a. LRF -> classic IDMS expansion ------------------------
        source_text = self._expand_logical_records(
            conversion_input=conversion_input,
            transformers=transformers,
            validation_messages=validation_messages,
        )

        # --- 0b. Program kind, measured once from the source ----------
        program_kind = self._resolve_program_kind(
            conversion_input=conversion_input,
            source_text=source_text,
            validation_messages=validation_messages,
        )

        # --- 0c. Input validation, rescoped to this program -----------
        mapping_validator = MappingValidator(
            mapping_repository=repositories["mapping"],
            dclgen_repository=repositories["dclgen"],
            table_name_resolver=resolvers["table_name"],
        )
        mapping_scope_filter = MappingScopeFilter(
            mapping_repository=repositories["mapping"],
            table_name_resolver=resolvers["table_name"],
        )
        validation_messages.extend(
            mapping_scope_filter.apply(
                messages=mapping_validator.validate(),
                source_text=source_text,
            )
        )
        validation_messages.extend(
            self._component_messages(mapping_scope_filter)
        )

        # --- Restart context, from the EXPANDED source ----------------
        restart_context = self._restart_context(
            conversion_input=conversion_input,
            source_text=source_text,
            program_kind=program_kind,
            validation_messages=validation_messages,
        )

        # --- IDMS -> DB2 statement transformation ---------------------
        converted_cobol, transform_messages, operations = transformers[
            "cobol"
        ].transform(
            cobol_text=source_text,
            target_program_id=conversion_input.target_program_id,
        )
        validation_messages.extend(transform_messages)

        # MIGRATED -> registry stage 'update_restart_skip' (call 1 of 2)
        converted_cobol = self._stage(
            "update_restart_skip", converted_cobol, validation_messages
        )

        # --- Program flow analysis (diagnostics only) -----------------
        flow_analysis = ProgramFlowAnalyzer(
            mapping_rows=conversion_input.sheet_mapping_rows,
            dclgen_columns=conversion_input.dclgen_columns,
        ).analyze(
            cobol_text=source_text,
            operations=operations,
        )
        validation_messages.extend(flow_analysis.diagnostics)

        # --- Field references -> DCLGEN host variables ----------------
        converted_cobol = transformers["field_reference"].rewrite(
            converted_cobol
        )
        validation_messages.extend(
            self._component_messages(transformers["field_reference"])
        )

        # --- DB2 infrastructure, cursors ------------------------------
        converted_cobol = self._apply_db2_infrastructure(
            converted_cobol=converted_cobol,
            operations=operations,
            generators=generators,
            composers=composers,
            validation_messages=validation_messages,
        )

        # --- Timestamp / audit, SQLERROR routine ----------------------
        converted_cobol, timestamp_messages = generators["timestamp"].apply(
            cobol_text=converted_cobol,
            target_program_id=conversion_input.target_program_id,
        )
        validation_messages.extend(timestamp_messages)

        converted_cobol = generators["sql_error"].ensure_sql_error_paragraph(
            converted_cobol
        )

        # --- LEGACY restart paragraphs - gated ------------------------
        converted_cobol = self._apply_legacy_restart_generator(
            converted_cobol=converted_cobol,
            conversion_input=conversion_input,
            operations=operations,
            generators=generators,
            restart_context=restart_context,
            validation_messages=validation_messages,
        )

        # --- Safe cleanup passes --------------------------------------
        converted_cobol = self._apply_cleanup_composers(
            converted_cobol=converted_cobol,
            composers=composers,
            validation_messages=validation_messages,
        )

        converted_cobol = self._apply_commit_cleanup(
            converted_cobol=converted_cobol,
            composers=composers,
            program_kind=program_kind,
            validation_messages=validation_messages,
        )

        # --- FINISHING phase ------------------------------------------
        #
        # original_idms_text is the EXPANDED source, not the raw upload.
        # The converted text derives from it line by line, so style
        # preservation and unmapped-record discovery must compare against
        # the same baseline.
        converted_cobol = ConversionLayoutPipeline(
            composers=composers,
            resolvers=resolvers,
            component_messages=self._component_messages,
            restart_context=restart_context,
        ).finish(
            converted_cobol=converted_cobol,
            original_idms_text=source_text,
            validation_messages=validation_messages,
        )

        return converted_cobol, operations, repositories["dclgen"]

    # ------------------------------------------------------------------
    # LRF expansion
    # ------------------------------------------------------------------
    def _expand_logical_records(
        self,
        *,
        conversion_input: ConversionInput,
        transformers: dict,
        validation_messages: list[str],
    ) -> str:
        """Rewrite LRF syntax into classic IDMS syntax.

        Returns the source text every later pass must use.

        THREE stages, applied in order, each independent of the others:

            1. read / delete side   LrfPathExpander.expand
            2. write side           LrfUpdateExpander.expand
            3. status literals      LrStatusTokenReplacer.apply

        Never raises. A stage that is missing, malformed or that throws is
        REPORTED and skipped, and the text from the previous stage carries
        on - an unconverted LRF verb is caught downstream by the
        residual-IDMS checks anyway. What must never happen is a stage
        failing in silence, because then a wiring fault is indistinguishable
        from a program that has no logical records.
        """
        text = str(conversion_input.idms_cobol_text or "")
        if not text.strip():
            return text

        text = self._lrf_stage(
            transformers=transformers,
            key=TRANSFORMER_LRF_PATH_EXPANDER,
            method=METHOD_EXPAND,
            label=LABEL_LRF_READ,
            text=text,
            validation_messages=validation_messages,
        )

        text = self._lrf_stage(
            transformers=transformers,
            key=TRANSFORMER_LRF_UPDATE_EXPANDER,
            method=METHOD_EXPAND,
            label=LABEL_LRF_UPDATE,
            text=text,
            validation_messages=validation_messages,
        )

        text = self._lrf_stage(
            transformers=transformers,
            key=TRANSFORMER_LR_STATUS_REPLACER,
            method=METHOD_APPLY,
            label=LABEL_LR_STATUS,
            text=text,
            validation_messages=validation_messages,
        )
        self._dump_expanded(conversion_input, text)
        return text

    @staticmethod
    def _dump_expanded(conversion_input: ConversionInput, text: str) -> None:
        """Write the fully expanded source when DUMP_EXPANDED is set.

        TEMPORARY INSTRUMENTATION. The expanded text exists only in
        memory, so the block-level analyser cannot be written against a
        shape anybody has actually seen. Delete this method and its one
        call site once the LR access analyser is in place.
        """
        folder = os.environ.get("DUMP_EXPANDED", "")
        if not folder:
            return
        try:
            os.makedirs(folder, exist_ok=True)
            name = str(
                getattr(conversion_input, "target_program_id", "") or "UNKNOWN"
            ).strip()
            path = os.path.join(folder, f"{name}_expanded.cbl")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
        except Exception:  # noqa: BLE001
            return
        
    def _lrf_stage(
        self,
        *,
        transformers: dict,
        key: str,
        method: str,
        label: str,
        text: str,
        validation_messages: list[str],
    ) -> str:
        """Run ONE logical-record stage. Reports every way it can decline.

        Four outcomes, all visible:

          * the factory produced no component under ``key``
          * the component has no ``method``
          * the call raised
          * the call returned

        The component's own messages are drained in the last two cases,
        including the failure case: a transformer that reported two
        findings and then threw on the third must not lose the two.
        """
        component = transformers.get(key)

        if component is None:
            validation_messages.append(
                LRF_STAGE_NOT_WIRED_TEMPLATE.format(label=label, key=key)
            )
            return text

        run = getattr(component, method, None)
        if not callable(run):
            validation_messages.append(
                LRF_STAGE_NO_METHOD_TEMPLATE.format(
                    label=label, key=key, method=method
                )
            )
            return text

        try:
            produced = run(text)
        except Exception as exc:  # noqa: BLE001
            validation_messages.extend(self._component_messages(component))
            validation_messages.append(
                LRF_STAGE_FAILED_TEMPLATE.format(label=label, reason=exc)
            )
            return text

        validation_messages.extend(self._component_messages(component))
        return produced or text


__all__ = ["ConversionPipeline"]
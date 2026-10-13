# LOCATION: converter/pipeline/conversion/conversion_pipeline.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

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
    0a. ``LrfPathExpander`` rewrites Logical Record Facility syntax into the
        classic IDMS syntax the rest of the converter already understands::

            OBTAIN FIRST <LR> WHERE <keyword>  ->  OBTAIN FIRST <rec> WITHIN <set>
            LR-STATUS = 'X-EOA'                ->  DB-END-OF-SET
            FIELD OF <rec> OF LR               ->  FIELD OF <rec>

        It MUST run first, because the PROGRAM KIND resolver,
        MappingScopeFilter, CobolTransformer and ProgramFlowAnalyzer all
        read the source text. Every pass after this point sees classic
        IDMS and needs no logical-record knowledge.

    0b. ``ProgramKindResolver`` measures UPDATE vs RETRIEVAL from the
        EXPANDED source. After 0a, because the update-side LRF forms
        (``MODIFY <logical-record> WHERE <keyword>``) are rewritten there;
        before statement transformation, which removes the write verbs
        entirely.

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

        Returns the source text every later pass must use. Never raises:
        an expansion failure falls back to the original source and is
        reported as a validation message, because an unconverted LRF verb
        is caught downstream by the residual-IDMS checks anyway.
        """
        source_text = str(conversion_input.idms_cobol_text or "")

        expander = transformers.get("lrf_path_expander")
        if expander is None:
            return source_text

        try:
            expanded = expander.expand(source_text)
        except Exception as exc:  # noqa: BLE001
            validation_messages.append(
                "LRF expansion: skipped, original IDMS source will be used. "
                f"Reason: {exc}"
            )
            return source_text

        validation_messages.extend(self._component_messages(expander))
        expanded = expanded or source_text

        replacer = transformers.get("lr_status_token_replacer")
        if replacer is None:
            return expanded

        try:
            replaced = replacer.apply(expanded)
        except Exception as exc:  # noqa: BLE001
            validation_messages.append(
                "LR-STATUS tokens: skipped, expanded source will be used. "
                f"Reason: {exc}"
            )
            return expanded

        validation_messages.extend(self._component_messages(replacer))
        return replaced or expanded


__all__ = ["ConversionPipeline"]
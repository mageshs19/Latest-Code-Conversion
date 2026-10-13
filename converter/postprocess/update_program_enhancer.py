"""Update-program postprocess enhancer.

CORRECTION 1 - "deliberately not used by retrieval" was prose, not code
------------------------------------------------------------------------
The class docstring asserted the contract; enhance() took no program
kind and checked none. Four retrieval programs ran straight through it
and received restart working storage, a restart DCLGEN include and a
full set of restart-table paragraphs that nothing performs - while the
metadata-driven pass correctly reported

    Restart injection: Retrieval program is read-only; restart control
    not applied.

in the SAME run. Two gates, one applied.

The conversion pipeline has ALREADY classified the program. This pass is
TOLD, never classifies again: two classifiers eventually disagree.

CORRECTION 2 - the restart table name was INVENTED
----------------------------------------------------
_build_restart_config ended with

    restart_table_name = restart_table_name or "DZ01RSTV"
    restart_dclgen_name = restart_dclgen_name or "DCLDZ01RSTV"

A site table name fabricated in a fallback is the one thing every
resolver in this codebase refuses to do.

CORRECTION 2b - and it was reading attributes that do not exist
----------------------------------------------------------------
    getattr(context, "restart_table_name", None)
    getattr(context, "restart_dclgen_name", None)

Both return None on every run. The values live on context.restart_dclgen,
a DclgenRoleInfo carrying table_name, include_name and host_record_name.
The invented literals happened to equal the real values at this site, so
a wrong attribute path looked like a working feature for the entire life
of the framework. Refusing to invent exposed it on the first run.

include_name is NOT a substitute for host_record_name: include_name is
the EXEC SQL INCLUDE member (DZ01RSTV); host_record_name is the COBOL
group (DCLDZ01RSTV).

CORRECTION 3 - three returns said nothing
-------------------------------------------
_apply_generic_restart_logic returned the source unchanged when the
config was None, and _build_restart_config returned None, both in
silence. A silent return is indistinguishable from "there was nothing to
do". Every exit now reports.

CORRECTION 4 - fixing 2b switched on a pass that REGRESSED the output
-----------------------------------------------------------------------
With the attribute path corrected, the generic restart framework ran for
the first time. VMDZ1567 went from 420 to 333 statement lines and
regained every state four later passes had already removed:

    COPY VMBD205I                   the input-record rename undone
    MOVE 1815                       the CHAR literal unquoted again
    NR-IDFMAS-479BFAR               the OF DCLDZBFARTV qualifier dropped
    CTR-REC / SW-EOF / SW-RECAB     legacy residue restored
    700-SELECT / 700-UPDATE /
    700-INSERT / 710 / 720          the legacy restart family re-injected

It rebuilds from an earlier version of the text. It is a THIRD restart
mechanism alongside the metadata-driven composer and the legacy
paragraph generator, and two were already one too many.

APPLY_GENERIC_RESTART_FRAMEWORK is therefore False. The config builder
stays corrected so the next person does not re-discover 2b.

CORRECTION 5 - a stale NOTE said this class was never called
--------------------------------------------------------------
An earlier note recorded that enhance() was not invoked by
runners/run_update.py. That was wrong: the probe which produced it had
filtered its own traceback away, and the real cause was an ImportError
from a deleted constant. A runtime trace now shows enhance() running for
all six programs via runners/update/update_postprocess_pipeline.py.

A note that outlives its evidence is worse than no note.

CALLERS
-------
    runners/update/update_postprocess_pipeline.enhance_update_program   LIVE
    runners/batch/update_postprocess_pipeline.apply_update_postprocess  duplicate
    converter/ui/conversion_actions

The two pipeline modules are the same hundred lines with different
function names. One of them should go.
"""

from __future__ import annotations

from converter.postprocess.cobol_update_standard_generator import (
    CobolUpdateStandardGenerator,
)
from converter.postprocess.dynamic_metadata_resolver import (
    DynamicMetadataResolver,
)
from converter.postprocess.update_business_sql_standardizer import (
    UpdateBusinessSqlStandardizer,
)
from converter.postprocess.update_enhancement_result import (
    EnhancementResult,
)
from converter.postprocess.update_main_flow_rewriter import (
    UpdateMainFlowRewriter,
)
from converter.postprocess.update_postprocess_line_utils import (
    UpdatePostprocessLineUtils,
)
from converter.postprocess.update_restart_paragraph_manager import (
    UpdateRestartParagraphManager,
)
from converter.postprocess.update_storage_include_manager import (
    UpdateStorageIncludeManager,
)
from rules.update_restart_rules import UPDATE_RESTART_DIAGNOSTICS
from converter.repositories.mapping_repository import MappingRepository

from converter.postprocess.restart_config import RestartConfig
from converter.postprocess.restart_logic_pipeline import RestartLogicPipeline
from converter.postprocess.cobol_restart_logic_generator import (
    CobolRestartLogicGenerator,
)

PROGRAM_KIND_RETRIEVAL = "retrieval"
PROGRAM_KIND_UPDATE = "update"

# Fields read off the resolved DCLGEN role. Named so a rename in
# DclgenRoleInfo fails loudly here instead of falling through to a
# plausible neighbour - see CORRECTION 2b.
ROLE_TABLE_FIELD = "table_name"
ROLE_HOST_RECORD_FIELD = "host_record_name"

# --- Generic restart framework ---------------------------------------
#
# OFF. See CORRECTION 4. Set True only with a baselined before/after diff
# of at least one generated member.
APPLY_GENERIC_RESTART_FRAMEWORK = False

MESSAGES = {
    "retrieval": (
        "Update postprocess: retrieval program; update enhancement not "
        "applied."
    ),
    "kind_missing": (
        "Update postprocess: no program kind supplied; the caller must "
        "pass the kind the pipeline already resolved. Proceeding as an "
        "update program."
    ),
    "framework_disabled": (
        "Generic restart logic: disabled; the metadata-driven restart "
        "pass owns restart control for this program."
    ),
    "config_refused": (
        "Generic restart logic: no restart DCLGEN on the context; "
        "framework not applied."
    ),
    "names_unresolved": (
        "Generic restart logic: restart table '{table}' / DCLGEN "
        "'{dclgen}' unresolved on the context; refused to invent a name."
    ),
    "no_source_for_detection": (
        "Generic restart logic: the context carries no converted COBOL, "
        "so original variable names were not detected."
    ),
    "applied_silently": (
        "Generic restart logic: applied for {table} / {dclgen}; text "
        "{outcome}. The pipeline reported no diagnostics of its own."
    ),
    "not_applicable": (
        "Generic restart logic: not applicable; no reason supplied by "
        "the pipeline."
    ),
}


class UpdateProgramEnhancer:
    """Update-program postprocess enhancer. Refuses retrieval programs."""

    def __init__(self) -> None:
        self.resolver = DynamicMetadataResolver()
        self.generator = CobolUpdateStandardGenerator()
        self.line_utils = UpdatePostprocessLineUtils()

        self.storage_include_manager = UpdateStorageIncludeManager(
            generator=self.generator,
            line_utils=self.line_utils,
        )

        self.main_flow_rewriter = UpdateMainFlowRewriter(
            line_utils=self.line_utils,
        )

        self.restart_paragraph_manager = UpdateRestartParagraphManager(
            generator=self.generator,
            line_utils=self.line_utils,
        )

        self.business_sql_standardizer = UpdateBusinessSqlStandardizer(
            line_utils=self.line_utils,
        )

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------
    def enhance(
        self,
        *,
        source_cobol: str,
        converted_cobol: str,
        copybook_fields: list,
        dclgen_columns: list,
        target_program_id: str = "",
        sheet_mapping_rows: list | None = None,
        program_kind: str = "",
    ) -> EnhancementResult:
        diagnostics: list[str] = [UPDATE_RESTART_DIAGNOSTICS["start"]]

        kind = str(program_kind or "").strip().lower()

        if not kind:
            # NEW-6 CORRECTION - an ABSENT kind meant "assume update".
            #
            # The batch runner never passed program_kind, so every program
            # reaching this method was enhanced and the guard below never
            # fired. VMDZ7200 came out carrying DZ01RSTV,
            # 700-RESTART-CONTROL, 710/720 and an INSERT INTO the
            # checkpoint table - a read-only program turned into a writer.
            #
            # An unknown kind is MEASURED from the source rather than
            # assumed. Measurement uses source_cobol, before statement
            # transformation: the converted text no longer carries the
            # write verbs that prove the kind.
            from converter.resolvers.program_kind_resolver import (
                ProgramKindResolver,
            )

            diagnostics.append(MESSAGES["kind_missing"])
            measured, kind_messages = ProgramKindResolver().is_update(
                source_cobol
            )
            diagnostics.extend(kind_messages)
            kind = PROGRAM_KIND_UPDATE if measured else PROGRAM_KIND_RETRIEVAL

        if kind == PROGRAM_KIND_RETRIEVAL:
            diagnostics.append(MESSAGES["retrieval"])
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["end"])
            return EnhancementResult(
                converted_cobol=converted_cobol,
                diagnostics=diagnostics,
            )
        # Sheet Mapping is the authority for DB2 table names. An empty
        # repository keeps the AND-gate CLOSED - a safe skip rather than
        # a fabricated restart table.
        mapping_repository = MappingRepository(sheet_mapping_rows or [])

        try:
            context = self.resolver.resolve(
                source_cobol=source_cobol,
                generated_cobol=converted_cobol,
                copybook_fields=copybook_fields,
                dclgen_columns=dclgen_columns,
                target_program_id=target_program_id,
                mapping_repository=mapping_repository,
            )
        except Exception as exc:  # noqa: BLE001 - reported, never silent
            diagnostics.append(
                f"{UPDATE_RESTART_DIAGNOSTICS['context_failed']} Reason: {exc}"
            )
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["end"])

            return EnhancementResult(
                converted_cobol=converted_cobol,
                diagnostics=diagnostics,
            )

        diagnostics.extend(context.diagnostics)
        self._report_restart_gate(
            context=context,
            dclgen_columns=dclgen_columns,
            mapping_repository=mapping_repository,
            diagnostics=diagnostics,
        )

        output = converted_cobol

        output = self.storage_include_manager.fix_malformed_sqlerror(
            output, diagnostics
        )
        output = self.storage_include_manager.normalize_program_name(
            output, context, diagnostics
        )
        output = self.storage_include_manager.ensure_working_storage(
            output, context, diagnostics
        )
        output = self.storage_include_manager.ensure_date_working_storage(
            output, diagnostics
        )
        output = self.storage_include_manager.ensure_dclgen_include(
            output, context, diagnostics
        )
        output = self.storage_include_manager.ensure_referenced_dclgen_includes(
            output, diagnostics
        )
        output = self.storage_include_manager.ensure_copybook_include(
            output, context, diagnostics
        )

        output = self.main_flow_rewriter.replace_legacy_restart_main_flow(
            output, context, diagnostics
        )

        output = self.restart_paragraph_manager.ensure_read_flat_file(
            output, context, diagnostics
        )
        output = self.restart_paragraph_manager.ensure_restart_paragraphs(
            output, context, diagnostics
        )

        output = self.business_sql_standardizer.standardize(
            output, context, diagnostics
        )

        output = self._apply_generic_restart_logic(
            output, context, diagnostics
        )

        output = self.storage_include_manager.remove_legacy_restart_working_storage(
            output, diagnostics
        )
        output = self.storage_include_manager.ensure_sqlerror_paragraph(
            output, diagnostics
        )

        try:
            output = self.storage_include_manager.deduplicate_includes(
                output, diagnostics
            )
        except Exception as exc:  # noqa: BLE001
            diagnostics.append(f"WARNING: deduplicate_includes failed: {exc}")

        diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["end"])

        return EnhancementResult(
            converted_cobol=output,
            diagnostics=diagnostics,
        )

    # -----------------------------------------------------------------
    # Restart gate reporting
    # -----------------------------------------------------------------
    @staticmethod
    def _report_restart_gate(
        *,
        context,
        dclgen_columns: list,
        mapping_repository: MappingRepository,
        diagnostics: list[str],
    ) -> None:
        """Say WHY no restart SQL will be generated.

        Case 3   a DCLGEN restart group exists but Sheet Mapping does not
                 confirm the table, so the AND-gate blocked fabrication.
        Case 2/4 the restart DCLGEN itself was never resolved.
        """
        if getattr(context, "restart_dclgen", None) is not None:
            return

        has_dclgen_candidate = bool(dclgen_columns)
        mapping_has_hint = any(
            mapping_repository.has_table(table)
            for table in mapping_repository.tables()
        )

        if has_dclgen_candidate and mapping_has_hint:
            diagnostics.append(
                "WARNING (Case 3): Restart flow NOT generated. A DCLGEN "
                "restart group was found, but the restart table is not "
                "confirmed in the Sheet Mapping. Legacy IDMS restart flow "
                "PRESERVED UNCHANGED. Add the restart table to the Sheet "
                "Mapping to auto-convert."
            )
            return

        diagnostics.append(
            "WARNING (Case 2/4): Restart-table DCLGEN not resolved. Legacy "
            "IDMS restart/control flow PRESERVED UNCHANGED and must be "
            "redesigned manually. Add the restart table to the DCLGEN "
            "inputs to auto-convert."
        )

    # -----------------------------------------------------------------
    # Generic restart framework  -- OFF, see CORRECTION 4
    # -----------------------------------------------------------------
    def _apply_generic_restart_logic(
        self,
        cobol_source: str,
        context: object,
        diagnostics: list[str],
    ) -> str:
        """Apply the restart framework, or report why it was not applied."""
        if not APPLY_GENERIC_RESTART_FRAMEWORK:
            diagnostics.append(MESSAGES["framework_disabled"])
            return cobol_source

        restart_config = self._build_restart_config(context, diagnostics)
        if restart_config is None:
            return cobol_source

        try:
            generator = CobolRestartLogicGenerator(restart_config)
            pipeline = RestartLogicPipeline(
                config=restart_config,
                generator=generator,
                line_utils=self.line_utils,
            )

            if not pipeline.is_applicable(context):
                reason = pipeline.not_applicable_reason()
                diagnostics.append(
                    f"Generic restart logic: {reason}"
                    if reason
                    else MESSAGES["not_applicable"]
                )
                return cobol_source

            result = pipeline.apply_to_program(cobol_source, context)
            diagnostics.extend(pipeline.diagnostics)

            # An applied pass indistinguishable from a skipped one cannot
            # be reviewed, and this one rewrites restart control.
            if not pipeline.diagnostics:
                diagnostics.append(
                    MESSAGES["applied_silently"].format(
                        table=restart_config.restart_table_name,
                        dclgen=restart_config.restart_dclgen_name,
                        outcome=(
                            "changed"
                            if result != cobol_source
                            else "unchanged"
                        ),
                    )
                )

            return result

        except Exception as exc:  # noqa: BLE001
            diagnostics.append(
                f"Generic restart logic framework error: {exc} "
                "(falling back to legacy logic)"
            )
            return cobol_source

    @staticmethod
    def _build_restart_config(
        context: object,
        diagnostics: list[str],
    ) -> RestartConfig | None:
        """The restart config, or None WITH a reason. See CORRECTION 2b."""
        role = getattr(context, "restart_dclgen", None)
        if role is None:
            diagnostics.append(MESSAGES["config_refused"])
            return None

        table = str(getattr(role, ROLE_TABLE_FIELD, "") or "").strip()
        host_record = str(
            getattr(role, ROLE_HOST_RECORD_FIELD, "") or ""
        ).strip()

        if not table or not host_record:
            diagnostics.append(
                MESSAGES["names_unresolved"].format(
                    table=table or "(unresolved)",
                    dclgen=host_record or "(unresolved)",
                )
            )
            return None

        config = RestartConfig(
            restart_table_name=table,
            restart_dclgen_name=host_record,
        )

        cobol_source = str(getattr(context, "converted_cobol", "") or "")
        if cobol_source:
            config.detect_from_cobol(cobol_source)
        else:
            diagnostics.append(MESSAGES["no_source_for_detection"])

        return config


__all__ = [
    "APPLY_GENERIC_RESTART_FRAMEWORK",
    "MESSAGES",
    "PROGRAM_KIND_RETRIEVAL",
    "PROGRAM_KIND_UPDATE",
    "ROLE_HOST_RECORD_FIELD",
    "ROLE_TABLE_FIELD",
    "EnhancementResult",
    "UpdateProgramEnhancer",
]
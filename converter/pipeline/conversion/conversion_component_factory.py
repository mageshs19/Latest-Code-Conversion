# LOCATION: converter/pipeline/conversion/conversion_component_factory.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

from converter.composers.cobol_cleanup_composer import CobolCleanupComposer
from converter.composers.cobol_formatter import CobolFormatter
from converter.composers.cursor_flow_composer import CursorFlowComposer
from converter.composers.cursor_order_cleanup_composer import (
    CursorOrderCleanupComposer,
)
from converter.composers.db2_date_comparison_composer import (
    Db2DateComparisonComposer,
)
from converter.composers.final_cobol_fix_composer import (
    FinalCobolFixComposer,
    FinalCobolFixComposerConfig,
)
from converter.composers.fixed_format_composer import FixedFormatComposer
from converter.composers.manual_layout_composer import ManualLayoutComposer
from converter.composers.manual_style_preserver import ManualStylePreserver
from converter.composers.restart.restart_line_utils import RestartLineUtils
from converter.composers.restart.restart_stage_adapter import (
    RestartStageAdapter,
)
from converter.composers.retrieval_commit_cleanup_composer import (
    RetrievalCommitCleanupComposer,
)
from converter.composers.sqlcode_wrapper_cleanup_composer import (
    SqlcodeWrapperCleanupComposer,
)
from converter.composers.unnecessary_comments_cleanup_composer import (
    UnnecessaryCommentsCleanupComposer,
)
from converter.composers.update_program_feedback_composer import (
    UpdateProgramFeedbackComposer,
)
from converter.composers.update_restart_skip_composer import (
    UpdateRestartSkipComposer,
)
from converter.domain.models import ConversionInput
from converter.generators.cursor_paragraph_generator import (
    CursorParagraphGenerator,
)
from converter.generators.db2_infrastructure_generator import (
    Db2InfrastructureGenerator,
)
from converter.pipeline.lrf_host_variable_population import (
    setup_lrf_host_variable_population,
)
from converter.generators.select_paragraph_generator import (
    SelectParagraphGenerator,
)
from converter.generators.sql_error_generator import SqlErrorGenerator
from converter.generators.sql_generator import SqlGenerator
from converter.generators.timestamp_generator import TimestampGenerator
from converter.repositories.copybook_repository import CopybookRepository
from converter.repositories.dclgen_repository import DclgenRepository
from converter.repositories.lrf_repository import LrfRepository
from converter.repositories.mapping_repository import MappingRepository
from converter.resolvers.column_name_resolver import ColumnNameResolver
from converter.resolvers.cursor_name_resolver import CursorNameResolver
from converter.resolvers.host_variable_resolver import HostVariableResolver
from converter.resolvers.lrf_path_resolver import LrfPathResolver
from converter.resolvers.record_context_resolver import RecordContextResolver
from converter.resolvers.table_name_resolver import TableNameResolver
from converter.transformers.cobol_transformer import CobolTransformer
from converter.transformers.field_reference_rewriter import (
    FieldReferenceRewriter,
)
from converter.transformers.idms_statement_transformer import (
    IdmsStatementTransformer,
)
from converter.transformers.lrf_path_expander import LrfPathExpander
from patterns.idms_patterns import IDMS_WRITE_VERB_PATTERN
from rules.final_feedback_fix_rules import (
    DEFAULT_DB2_DATE_EXTERNAL_FORMAT,
    ORDER_BY_COLUMNS_IN_SELECT_DEFAULT,
)
from converter.composers.record_materialisation_composer import (
    RecordMaterialisationComposer,
)
from converter.composers.cursor_close_guarantee_composer import (
    CursorCloseGuaranteeComposer,
)
from rules.idms_transformer_messages import TRANSFORMER_MESSAGES


class ConversionComponentFactory:
    """Builds repositories, resolvers, generators, transformers, composers.

    CORRECTION 1 - module imported where an instance was required
    -------------------------------------------------------------
    This file previously carried BOTH

        from converter.resolvers import cursor_name_resolver
        from converter.resolvers.cursor_name_resolver import CursorNameResolver

    and returned the first of those under the "cursor_name" key. That put a
    MODULE into the resolver map, so Db2InfrastructureGenerator failed at
    runtime with

        AttributeError: module 'converter.resolvers.cursor_name_resolver'
        has no attribute 'cursor_name_from_table'

    The module import is removed. "cursor_name" now holds a constructed
    CursorNameResolver, like every other resolver in the map.

    CORRECTION 2 - COMMIT emitted in a read-only program
    ----------------------------------------------------
    IDMS FINISH closes the run unit, so the DB2 equivalent in an UPDATE
    program is COMMIT. A RETRIEVAL program declares every cursor
    FOR READ ONLY and has nothing to commit; the COBOL team's manual
    reference emits none, and rules/manual_reference_rules.py already
    declared EMIT_COMMIT_IN_RETRIEVAL = False. Nothing read it, so
    VM7BD200 shipped with

        MOVE 'COMMIT' TO SQL-LOCATION.
        EXEC SQL
          COMMIT
        END-EXEC.

    The program KIND is now classified ONCE, from the SOURCE program, and
    published to the two components that need it:

      1. IdmsStatementTransformer  - suppresses the FINISH -> COMMIT
                                     conversion at the point of decision.
      2. RetrievalCommitCleanupComposer - safety net for a COMMIT that
                                     arrives by any other route.

    Classification reads the SOURCE, never the generated text: a generated
    COMMIT would otherwise classify the program that produced it.

    FAIL-SAFE: when the source is unknown (a caller that builds composers
    without ever calling _repositories), the program is treated as an
    UPDATE program and the COMMIT is KEPT. Removing a COMMIT a program
    needs is a data-integrity defect; keeping one it does not need is a
    cosmetic divergence.

    CORRECTION 3 - the restart adapter was handed self.line_utils
    -------------------------------------------------------------
    The first restart wiring read

        composers["restart_injection"] = RestartStageAdapter(
            self.line_utils, ...
        )

    and every conversion died with

        AttributeError: 'ConversionService' object has no attribute
        'line_utils'

    There is no shared line utility on this class, and there never was:
    each composer constructs its own (CobolCleanupLineUtils,
    FixedFormatLineService, CursorFlowLineFormatter). The restart
    modules additionally need is_comment(), which NO production class
    exposes - only the test stand-in did, so wiring any of them directly
    would have failed on the first comment line of a real program.

    RestartLineUtils wraps the shared FixedFormatLineService and supplies
    the two methods the restart package calls, exactly as
    converter/composers/cursor_close_guarantee/line_utils.py wraps
    CursorFlowLineFormatter for its own package. One definition of a
    logical line, one adapter, no duplicated geometry.

    The adapter's `context` is None here on purpose: the restart context
    is RUN-scoped (program kind, DCLGEN role, retention, totals) and is
    set by the layout pipeline immediately before the pass runs. Storing
    it on a factory-built object would let one program's context leak
    into the next in a batch run.

    LRF (Logical Record Facility)
    -----------------------------
    LRF metadata is OPTIONAL. With no subschema supplied, LrfRepository is
    empty, LrfPathResolver reports is_empty(), and LrfPathExpander returns
    the program source unchanged - so a program without logical records
    converts exactly as it did before LRF support existed.
    """

    def __init__(self) -> None:
        # Per-program state. Reset on every _repositories() call so a
        # batch run cannot leak program 1's kind into program 2.
        self._source_text: str = ""
        self._source_known: bool = False

    # ------------------------------------------------------------------
    # Program kind
    # ------------------------------------------------------------------
    def _remember_source(self, conversion_input: ConversionInput | None) -> None:
        """Record the SOURCE program text for kind classification."""
        text = str(getattr(conversion_input, "idms_cobol_text", "") or "")
        self._source_text = text
        self._source_known = bool(text.strip())

    def _program_is_update(
        self,
        conversion_input: ConversionInput | None = None,
    ) -> bool:
        """True when the SOURCE contains IDMS write verbs.

        STORE / MODIFY / ERASE make a program an update program. A
        program with none of them is retrieval and needs no COMMIT.

        An explicitly supplied conversion_input always wins over the
        remembered one, so a caller that skips _repositories() can still
        get a correct answer.
        """
        if conversion_input is not None:
            text = str(getattr(conversion_input, "idms_cobol_text", "") or "")
            if text.strip():
                return bool(IDMS_WRITE_VERB_PATTERN.search(text))

        if not self._source_known:
            # Fail safe: unknown source -> keep the COMMIT.
            return True

        return bool(IDMS_WRITE_VERB_PATTERN.search(self._source_text))

    # ------------------------------------------------------------------
    # Repositories
    # ------------------------------------------------------------------
    def _repositories(self, conversion_input: ConversionInput) -> dict[str, object]:
        # First component built for a program, so this is the one place
        # every caller passes the source through.
        self._remember_source(conversion_input)

        return {
            "mapping": MappingRepository(conversion_input.sheet_mapping_rows),
            "dclgen": DclgenRepository(conversion_input.dclgen_columns),
            "copybook": CopybookRepository(conversion_input.copybook_fields),
            "lrf": LrfRepository(
                getattr(conversion_input, "logical_records", None) or []
            ),
        }

    # ------------------------------------------------------------------
    # Resolvers
    # ------------------------------------------------------------------
    def _resolvers(self, repositories: dict[str, object]) -> dict[str, object]:
        mapping_repository = repositories["mapping"]
        dclgen_repository = repositories["dclgen"]

        table_name_resolver = TableNameResolver(
            mapping_repository=mapping_repository,
            dclgen_repository=dclgen_repository,
        )
        column_name_resolver = ColumnNameResolver(
            mapping_repository=mapping_repository,
            dclgen_repository=dclgen_repository,
            table_name_resolver=table_name_resolver,
        )
        host_variable_resolver = HostVariableResolver(
            dclgen_repository=dclgen_repository,
            table_name_resolver=table_name_resolver,
        )
        record_context_resolver = RecordContextResolver(
            mapping_repository=mapping_repository,
            dclgen_repository=dclgen_repository,
        )

        # MUST be an instance. See the class docstring.
        cursor_name_resolver = CursorNameResolver()

        lrf_path_resolver = LrfPathResolver(
            lrf_repository=repositories.get("lrf"),
            mapping_repository=mapping_repository,
        )

        return {
            "table_name": table_name_resolver,
            "column_name": column_name_resolver,
            "host_variable": host_variable_resolver,
            "record_context": record_context_resolver,
            "cursor_name": cursor_name_resolver,
            "lrf_path": lrf_path_resolver,
        }

    # ------------------------------------------------------------------
    # Generators
    # ------------------------------------------------------------------
    def _generators(self, repositories, resolvers) -> dict[str, object]:
        sql_error_generator = SqlErrorGenerator()

        sql_generator = SqlGenerator(
            mapping_repository=repositories["mapping"],
            dclgen_repository=repositories["dclgen"],
            table_name_resolver=resolvers["table_name"],
            column_name_resolver=resolvers["column_name"],
            host_variable_resolver=resolvers["host_variable"],
        )
        db2_infrastructure_generator = Db2InfrastructureGenerator(
            table_name_resolver=resolvers["table_name"],
            column_name_resolver=resolvers["column_name"],
            host_variable_resolver=resolvers["host_variable"],
            cursor_name_resolver=resolvers["cursor_name"],
        )
        cursor_paragraph_generator = CursorParagraphGenerator(
            db2_infrastructure_generator=db2_infrastructure_generator,
            host_variable_resolver=resolvers["host_variable"],
            sql_error_generator=sql_error_generator,
        )

        # Setup LRF host variable population support
        try:
            setup_lrf_host_variable_population(
                cursor_paragraph_generator=cursor_paragraph_generator,
                host_variable_resolver=resolvers["host_variable"],
                table_name_resolver=resolvers["table_name"],
                cursor_name_resolver=resolvers["cursor_name"],
            )
        except Exception:  # noqa: BLE001
            # Silently fail; LRF support is optional
            pass

        timestamp_generator = TimestampGenerator(
            mapping_repository=repositories["mapping"],
            table_name_resolver=resolvers["table_name"],
            host_variable_resolver=resolvers["host_variable"],
        )
        select_paragraph_generator = SelectParagraphGenerator()

        return {
            "sql": sql_generator,
            "sql_error": sql_error_generator,
            "db2_infrastructure": db2_infrastructure_generator,
            "cursor_paragraph": cursor_paragraph_generator,
            "timestamp": timestamp_generator,
            "select_paragraph": select_paragraph_generator,
        }

    # ------------------------------------------------------------------
    # Transformers
    # ------------------------------------------------------------------
    def _transformers(
        self,
        repositories,
        resolvers,
        generators,
        conversion_input: ConversionInput | None = None,
    ) -> dict[str, object]:
        """Build the transformer map.

        `conversion_input` is OPTIONAL and trailing, so every existing
        positional caller keeps working unchanged. When supplied it
        overrides the remembered source for kind classification.
        """
        idms_statement_transformer = IdmsStatementTransformer(
            sql_generator=generators["sql"],
            sql_error_generator=generators["sql_error"],
            table_name_resolver=resolvers["table_name"],
            cursor_name_resolver=resolvers["cursor_name"],
        )

        self._apply_commit_policy(
            transformer=idms_statement_transformer,
            conversion_input=conversion_input,
        )

        return {
            "idms_statement": idms_statement_transformer,
            "cobol": CobolTransformer(
                idms_statement_transformer=idms_statement_transformer
            ),
            "field_reference": FieldReferenceRewriter(
                mapping_repository=repositories["mapping"],
                table_name_resolver=resolvers["table_name"],
                host_variable_resolver=resolvers["host_variable"],
            ),
            # Runs FIRST in the pipeline. No-op when no LRF metadata or no
            # LRF syntax is present.
            "lrf_path_expander": LrfPathExpander(
                path_resolver=resolvers["lrf_path"],
            ),
        }

    def _apply_commit_policy(
        self,
        *,
        transformer,
        conversion_input: ConversionInput | None = None,
    ) -> None:
        is_update = self._program_is_update(conversion_input)

        try:
            transformer.emit_commit = is_update
            published = True
        except Exception:  # noqa: BLE001
            published = False

        messages = getattr(transformer, "messages", None)
        if messages is None:
            return

        if not published:
            messages.append(
                "Program kind: COMMIT policy could NOT be published; "
                "the transformer refused the attribute. COMMIT will be "
                "emitted by default."
            )
            return

        messages.append(
            TRANSFORMER_MESSAGES["program_kind"].format(
                kind="UPDATE" if is_update else "RETRIEVAL",
                emit=is_update,
            )
        )

    # ------------------------------------------------------------------
    # Composers
    # ------------------------------------------------------------------
    def _composers(
        self,
        repositories,
        resolvers,
        conversion_input: ConversionInput | None = None,
    ) -> dict[str, object]:
        composers: dict[str, object] = {}
        composers.update(self._formatting_composers())
        composers.update(self._cursor_composers())
        composers.update(
            self._cleanup_composers(repositories, resolvers, conversion_input)
        )
        composers.update(self._update_composers(repositories, resolvers))
        composers.update(self._restart_composers(repositories, resolvers))
        composers.update(self._final_fix_composers())
        return composers

    def _formatting_composers(self) -> dict[str, object]:
        return {
            "formatter": CobolFormatter(),
            "fixed_format": FixedFormatComposer(),
            "manual_layout": ManualLayoutComposer(),
            "style_preserver": ManualStylePreserver(),
        }

    def _cursor_composers(self) -> dict[str, object]:
        return {
            "cursor_flow": CursorFlowComposer(),
            "cursor_close_guarantee": CursorCloseGuaranteeComposer(),
            "cursor_order_cleanup": CursorOrderCleanupComposer(),
            "sqlcode_cleanup": SqlcodeWrapperCleanupComposer(),
            "date_compare": Db2DateComparisonComposer(),
        }

    def _cleanup_composers(
        self,
        repositories,
        resolvers,
        conversion_input: ConversionInput | None = None,
    ) -> dict[str, object]:
        return {
            "feedback_cleanup": CobolCleanupComposer(
                dclgen_repository=repositories["dclgen"],
            ),
            # Safety net for the COMMIT decision. A no-op for an update
            # program, and a no-op for a retrieval program that carries
            # no COMMIT. Register AFTER feedback_cleanup and BEFORE
            # fixed_format so the replacement comment is sequenced with
            # everything else.
            "retrieval_commit_cleanup": RetrievalCommitCleanupComposer(
                is_update_program=self._program_is_update(conversion_input),
            ),
            "unnecessary_comments_cleanup": UnnecessaryCommentsCleanupComposer(),
            "update_restart_skip": UpdateRestartSkipComposer(),
            # Expands a whole-record MOVE into the record layout plus
            # field-by-field moves. Consumed by the FINISHING phase, not
            # by the content phase, because it needs sequenced lines.
            "record_materialisation": RecordMaterialisationComposer(
                mapping_repository=repositories["mapping"],
                table_name_resolver=resolvers["table_name"],
                host_variable_resolver=resolvers["host_variable"],
            ),
        }

    def _update_composers(self, repositories, resolvers) -> dict[str, object]:
        return {
            "update_program_feedback": UpdateProgramFeedbackComposer(
                mapping_repository=repositories["mapping"],
                dclgen_repository=repositories["dclgen"],
                table_name_resolver=resolvers["table_name"],
                host_variable_resolver=resolvers["host_variable"],
            ),
        }

    def _restart_composers(self, repositories, resolvers) -> dict[str, object]:
        """Restart control injection for an update program.

        RestartLineUtils wraps the shared fixed-format service: no
        production class exposes both logical() and is_comment(). See
        CORRECTION 3 in the class docstring.

        `context` stays None here. It is RUN-scoped and is set by the
        layout pipeline immediately before the pass, so one program's
        context cannot leak into the next in a batch run.
        """
        return {
            "restart_injection": RestartStageAdapter(
                RestartLineUtils(),
                context=None,
                mapping_repository=repositories["mapping"],
                table_name_resolver=resolvers["table_name"],
            ),
        }

    def _final_fix_composers(self) -> dict[str, object]:
        return {
            "final_feedback_fix": FinalCobolFixComposer(
                config=FinalCobolFixComposerConfig(
                    db2_date_external_format=DEFAULT_DB2_DATE_EXTERNAL_FORMAT,
                    require_order_by_columns_in_select=(
                        ORDER_BY_COLUMNS_IN_SELECT_DEFAULT
                    ),
                )
            ),
        }


__all__ = ["ConversionComponentFactory"]
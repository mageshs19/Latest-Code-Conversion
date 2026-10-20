# LOCATION: converter/transformers/idms_statement_transformer.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

from converter.transformers.idms_statement.control_statement_converter import (
    ControlStatementConverterMixin,
)
from converter.transformers.idms_statement.data_statement_converter import (
    DataStatementConverterMixin,
)
from converter.transformers.idms_statement.transformer_shared_mixin import (
    TransformerSharedMixin,
)

# Converter call signatures. The mixins are deliberately left untouched,
# so the dispatcher adapts to them rather than the other way round.
ARITY_LINE = 1          # (stripped_line)
ARITY_UPPER_LINE = 2    # (upper, stripped_line)
ARITY_WITH_DIVISION = 3  # (upper, stripped_line, current_division)
ARITY_WITH_SQL_ERROR = 4  # (upper, stripped_line, division, sql_error_paragraph)

NO_OPENED_SET = ""


class IdmsStatementTransformer(
    TransformerSharedMixin,
    ControlStatementConverterMixin,
    DataStatementConverterMixin,
):
    """Converts executable IDMS statements to DB2-compatible COBOL.

    Conversion logic only. Regex patterns live in patterns/idms_patterns.py;
    all *DB2: message text lives in rules/idms_transformer_messages.py.

    Feedback-driven rules:
    - OBTAIN CALC does not generate DB2 SELECT for update flow.
    - Direct UPDATE is enough when the WHERE has all composite PK/CALC keys.
    - Original IDMS OBTAIN CALC is still removed from final COBOL.
    - SqlGenerator methods already generate SQLCODE checks where required.
    - This transformer must not add duplicate SQLCODE wrappers.

    CORRECTION 1 - state leaked between programs
    --------------------------------------------
    ConversionComponentFactory builds ONE instance, and the batch runners
    convert every program in the folder inside a single process. Because
    `messages` and `unmapped_records` were only initialised in __init__,
    program 1's unmapped records were still present when program 2 ran,
    and the record-level composer commented records program 2 never
    referenced. reset() now clears per-program state; call it once per
    program, before the first transform_line().

    CORRECTION 2 - an empty result deleted a statement
    --------------------------------------------------
    The dispatcher accepted any non-None result. A converter that returned
    an empty list therefore removed the source line silently. Only a
    NON-EMPTY result now counts as a conversion; anything else falls
    through to the next converter and finally to token replacement, so a
    statement can never disappear without a *DB2: comment explaining it.

    CORRECTION 3 - the converter chain was rebuilt per line
    -------------------------------------------------------
    Seven closures were allocated for every source line. The chain is a
    fixed table of bound methods built once in __init__.

    CORRECTION 4 - THE PROGRAM KIND WAS MEASURED AND NEVER DELIVERED
    -----------------------------------------------------------------
    ConversionPipelineSteps._hand_off_program_kind refuses, and reports
    the refusal, when a component does not already declare the attribute
    named by PROGRAM_KIND_ATTRIBUTE - "program_kind". This class declared
    no such attribute and was never offered the kind in any case: that
    method has exactly ONE call site, for retrieval_commit_cleanup.

    The consequence was not cosmetic. _convert_obtain_calc encodes the
    UPDATE semantic only - 'the direct UPDATE carries the composite key,
    so the positioning read is redundant' - and applied it to retrieval
    programs, where the OBTAIN CALC is the only population of the DCLGEN
    host group. VMDZ4310 shipped with twelve MOVEs out of DCLDZBEFFTV and
    no SELECT. The kind was measured correctly for all six programs on
    every run and simply never arrived.

    CORRECTION 5 - WHY reset() DOES NOT CLEAR THE TWO NEW ATTRIBUTES
    -----------------------------------------------------------------
    ``messages`` and ``unmapped_records`` are OUTPUTS: this class produces
    them, so clearing them at the start of a program is correct.

    ``program_kind`` and ``lrf_calc_records`` are INPUTS. They are
    delivered by the pipeline BEFORE transform() runs, and reset() runs
    INSIDE transform(). Clearing them there would erase the handoff
    between the moment it is made and the moment it is read, and the
    converter would silently fall back to update semantics on every
    program - reproducing the exact defect CORRECTION 4 fixes.

    They are therefore overwritten WHOLESALE by the pipeline for each
    program rather than cleared here. A missing handoff is visible:
    _hand_off_program_kind reports it, and _convert_lrf_calc_read refuses
    on an empty kind, which is the safe direction.
    """

    def __init__(
        self,
        sql_generator,
        sql_error_generator,
        table_name_resolver,
        cursor_name_resolver,
    ) -> None:
        self.sql_generator = sql_generator
        self.sql_error_generator = sql_error_generator
        self.table_name_resolver = table_name_resolver
        self.cursor_name_resolver = cursor_name_resolver

        self.messages: list[str] = []
        # Collect every record with no DB2 target so a composer can comment
        # the WHOLE record block at record level.
        self.unmapped_records: set[str] = set()

        # ---- per-program INPUTS, supplied by the pipeline -----------
        #
        # PROGRAM_KIND_ATTRIBUTE. Declared so
        # ConversionPipelineSteps._hand_off_program_kind stops refusing.
        # Empty means 'not delivered', and every kind-gated branch
        # refuses on empty, so an un-wired build behaves exactly as this
        # class did before. See CORRECTION 4 and CORRECTION 5.
        self.program_kind: str = ""

        # COBOL-form records for which LrfPathExpander emitted an
        # OBTAIN CALC parent access, published as its
        # calc_parent_records. Distinguishes an LRF-GENERATED keyed read
        # from a hand-written one, which must keep its behaviour.
        self.lrf_calc_records: set[str] = set()

        # Records an analyser classified as bounded searches. No producer
        # exists yet; declared here so the shape has one owner.
        self.bounded_search_records: dict[str, str] = {}

        # Converters that never open a cursor set, in dispatch order.
        # Order matters: OBTAIN CALC must be offered the line before
        # OBTAIN FIRST / NEXT, and every declarative form before any
        # executable form.
        #
        # _convert_lrf_calc_read sits immediately AHEAD of
        # _convert_obtain_calc and returns None on every path that is not
        # an LRF-generated keyed parent in a retrieval program, so the
        # existing converter is offered exactly the lines it sees today.
        self._plain_converters = (
            (self._convert_declarative_or_control, ARITY_UPPER_LINE),
            (self._convert_finish_or_commit, ARITY_WITH_DIVISION),
            (self._convert_bind_ready_connect_disconnect, ARITY_WITH_DIVISION),
            (self._convert_status_abort_perform, ARITY_WITH_DIVISION),
            (self._convert_on_db_rec_not_found, ARITY_LINE),
            (self._convert_lrf_calc_read, ARITY_WITH_DIVISION),
            (self._convert_obtain_calc, ARITY_WITH_SQL_ERROR),
            (self._convert_find_current, ARITY_WITH_DIVISION),
        )

        # Converters that may also open a cursor set.
        self._cursor_converters = (
            self._convert_obtain_first_next,
            self._convert_find_first,
        )

    #
    # Per-program lifecycle
    #
    def reset(self) -> None:
        """Clear per-program OUTPUT state.

        MUST be called once per program by CobolTransformer.transform(),
        before the first transform_line(). Without it a batch run carries
        one program's diagnostics and unmapped records into the next.

        program_kind and lrf_calc_records are deliberately NOT cleared -
        they are INPUTS delivered before transform() runs, and this
        method runs inside it. See CORRECTION 5.
        """
        self.messages = []
        self.unmapped_records = set()

    #
    # Public entry point
    #
    def transform_line(
        self,
        line: str,
        current_division: str,
        sql_error_paragraph: str,
    ) -> tuple[list[str], str]:
        stripped_line = str(line or "").strip()

        if not stripped_line:
            return [line], NO_OPENED_SET

        upper = stripped_line.upper()

        plain = self._run_plain_converters(
            upper=upper,
            stripped_line=stripped_line,
            current_division=current_division,
            sql_error_paragraph=sql_error_paragraph,
        )

        if plain is not None:
            return plain, NO_OPENED_SET

        cursor_lines, opened_set = self._run_cursor_converters(
            upper=upper,
            stripped_line=stripped_line,
            current_division=current_division,
        )

        if cursor_lines is not None:
            return cursor_lines, opened_set

        store_lines = self._convert_store_modify_erase(
            upper,
            stripped_line,
            current_division,
            sql_error_paragraph,
        )

        if self._is_converted(store_lines):
            return store_lines, NO_OPENED_SET

        return self._replace_idms_condition_tokens(line), NO_OPENED_SET

    #
    # Dispatch
    #
    def _run_plain_converters(
        self,
        *,
        upper: str,
        stripped_line: str,
        current_division: str,
        sql_error_paragraph: str,
    ) -> list[str] | None:
        """First converter that returns a non-empty result wins."""
        for converter, arity in self._plain_converters:
            result = self._invoke(
                converter=converter,
                arity=arity,
                upper=upper,
                stripped_line=stripped_line,
                current_division=current_division,
                sql_error_paragraph=sql_error_paragraph,
            )

            if self._is_converted(result):
                return result

        return None

    def _run_cursor_converters(
        self,
        *,
        upper: str,
        stripped_line: str,
        current_division: str,
    ) -> tuple[list[str] | None, str]:
        """Converters that may also report the IDMS set they opened."""
        for converter in self._cursor_converters:
            result, opened_set = converter(
                upper,
                stripped_line,
                current_division,
            )

            if self._is_converted(result):
                return result, str(opened_set or NO_OPENED_SET)

        return None, NO_OPENED_SET

    @staticmethod
    def _invoke(
        *,
        converter,
        arity: int,
        upper: str,
        stripped_line: str,
        current_division: str,
        sql_error_paragraph: str,
    ):
        if arity == ARITY_LINE:
            return converter(stripped_line)

        if arity == ARITY_UPPER_LINE:
            return converter(upper, stripped_line)

        if arity == ARITY_WITH_DIVISION:
            return converter(upper, stripped_line, current_division)

        return converter(
            upper,
            stripped_line,
            current_division,
            sql_error_paragraph,
        )

    @staticmethod
    def _is_converted(result) -> bool:
        """True only for a real replacement.

        None means "this converter does not handle the line".
        An EMPTY list used to mean the same thing by accident, but the old
        dispatcher accepted it and the source statement vanished with no
        *DB2: comment. Empty is now treated as "not handled".

        This is also what makes _convert_lrf_calc_read safe to place
        ahead of _convert_obtain_calc: its five refusals all return None,
        so the line falls through to the existing converter untouched.
        """
        return result is not None and len(result) > 0


__all__ = ["IdmsStatementTransformer"]
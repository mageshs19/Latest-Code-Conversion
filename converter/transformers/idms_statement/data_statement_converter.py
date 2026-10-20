# LOCATION: converter/transformers/idms_statement/data_statement_converter.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

from converter.resolvers.program_kind_resolver import KIND_RETRIEVAL
from converter.services.name_normalizer import NameNormalizer
from patterns.idms_patterns import (
    ERASE_PATTERN,
    FIND_CURRENT_PATTERN,
    FIND_FIRST_PATTERN,
    MODIFY_PATTERN,
    OBTAIN_CALC_PATTERN,
    OBTAIN_CALC_REVERSED_PATTERN,
    OBTAIN_FIRST_NEXT_PATTERN,
    ON_DB_REC_NOT_FOUND_PATTERN,
    STORE_PATTERN,
)
from rules.idms_transformer_messages import (
    CONVERTED_FIND_FIRST_TEMPLATE,
    CONVERTED_OBTAIN_FIRST_TEMPLATE,
    CONVERTED_OBTAIN_NEXT_TEMPLATE,
    DIRECT_UPDATE_COMPOSITE_KEY,
    FIND_FIRST_OUTSIDE_PROCEDURE_TEMPLATE,
    LRF_CALC_READ_CONVERTED_TEMPLATE,
    LRF_CALC_READ_MARKER_TEMPLATE,
    LRF_CALC_READ_NO_SQL_TEMPLATE,
    OBTAIN_CALC_OUTSIDE_PROCEDURE_TEMPLATE,
    OBTAIN_OUTSIDE_PROCEDURE_TEMPLATE,
    OPERATION_ERASE,
    OPERATION_MODIFY,
    OPERATION_STORE,
    PERFORM_FETCH_CURSOR_TEMPLATE,
    PERFORM_OPEN_CURSOR_TEMPLATE,
    REMOVED_FIND_CURRENT_TEMPLATE,
    REMOVED_OBTAIN_CALC_SELECT_TEMPLATE,
    STORE_MODIFY_ERASE_OUTSIDE_PROCEDURE_TEMPLATE,
)
from rules.idms_transformer_rules import (
    CONTINUE_STATEMENT,
    OBTAIN_FIRST_KEYWORD,
    PROCEDURE_DIVISION_NAME,
    SQLCODE_100_CONTINUE_BODY,
    SQLCODE_100_IF_CLOSE,
    SQLCODE_100_IF_OPEN,
)

# Indent applied to the statement lifted into the generated
# IF SQLCODE = 100 guard block.
GUARDED_STATEMENT_INDENT = "    "

NO_OPENED_SET = ""

# COBOL sentence terminator and the generated-comment prefix. Literal
# COBOL vocabulary; they belong in rules/idms_transformer_rules.py once
# that module owns the terminator vocabulary.
SENTENCE_TERMINATOR = "."
GENERATED_COMMENT_PREFIX = "*"

# Per-program state attributes this mixin READS. Declared as names so the
# producer and the consumer cannot drift apart.
BOUNDED_SEARCH_ATTRIBUTE = "bounded_search_records"
PROGRAM_KIND_ATTRIBUTE = "program_kind"
LRF_CALC_RECORDS_ATTRIBUTE = "lrf_calc_records"

# Comment bodies for the bounded-search branch. These belong in
# rules/idms_transformer_messages.py beside CONVERTED_OBTAIN_* once that
# module owns the bounded-search vocabulary; they live here while the
# feature is being introduced, exactly as GUARDED_STATEMENT_INDENT does.
# Each must fit a COBOL comment body (65 columns) after formatting.
BOUNDED_SEARCH_SELECT_TEMPLATE = (
    "*DB2: LR bounded search {record} WITHIN {set_name}"
)
BOUNDED_SEARCH_PREDICATE_TEMPLATE = (
    "*DB2: loop exit {predicate} folded into the WHERE clause."
)
BOUNDED_SEARCH_ADVANCE_TEMPLATE = (
    "*DB2: OBTAIN NEXT {record} folded into the singleton SELECT."
)


class DataStatementConverterMixin:
    """Converts IDMS data-access statements to DB2/cursor COBOL.

    NAME HANDLING CONTRACT
    ----------------------
    Two forms of every IDMS name are needed and they must never be mixed:

        *_key      NameNormalizer.normalize()  -> DB2 identifier, underscore
                   separated. Used ONLY for resolver / repository lookups
                   and for the opened_set value returned to the caller,
                   which downstream passes re-normalize.

        *_display  NameNormalizer.to_cobol()   -> IDMS / COBOL spelling,
                   hyphen separated. Used ONLY inside generated *DB2:
                   comment text.

    CORRECTION 1 - IDMS set name emitted as a DB2 identifier
    --------------------------------------------------------
    _convert_obtain_first_next and _convert_find_first passed the
    normalized key straight into the comment template, so an LRF-expanded
    program produced

        *DB2: Converted OBTAIN FIRST VMBFAS WITHIN AR_VMBFRM1.

    for the IDMS set AR-VMBFRM1. An IDMS set is not a DB2 identifier and
    must keep its hyphens. _convert_obtain_calc already did this correctly
    via cobol_record; the other two were never brought in line.

    CORRECTION 2 - hyphenated record names were corrupted too
    ---------------------------------------------------------
    The same defect rendered record VMB-FAR as VMB_FAR. It went unnoticed
    only because the reference program's record, VMBFAS, carries no hyphen.

    CORRECTION 3 - no unmapped-record guard on the cursor paths
    -----------------------------------------------------------
    _convert_obtain_calc and _convert_store_modify_erase both refuse when
    table_for_record() is empty. The two cursor converters did not, so an
    unmapped record resolved to an empty table, then to an empty cursor
    name, and the generated lines read

        PERFORM OPEN-.
        PERFORM FETCH-.

    which the compiler rejects. Both now keep and comment the statement.

    CORRECTION 4 - FIND FIRST declares <record> as OPTIONAL
    -------------------------------------------------------
    FIND_FIRST_PATTERN allows 'FIND FIRST WITHIN <set>', which yields
    record=None -> empty record -> the same broken PERFORM. Guarded.

    CORRECTION 5 - EVERY OBTAIN FIRST/NEXT BECAME A CURSOR
    -------------------------------------------------------
    This converter receives THREE arguments - the line, the line
    uppercased, and the division name. It cannot see the statement that
    encloses the OBTAIN, so it mapped every

        OBTAIN FIRST <rec> WITHIN <set>
        OBTAIN NEXT  <rec> WITHIN <set>

    to OPEN / FETCH on a cursor, unconditionally. That is correct for a
    WALK. It is wrong for a BOUNDED SEARCH, which is what an LR access
    like this one really is::

        OBTAIN FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF
        PERFORM UNTIL LR-STATUS = 'NO-MORE-VMBEVEF'
                   OR CT-EVENT OF VMBEVEF = '0092'
           OBTAIN NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF
        END-PERFORM

    The loop does not process every member; it advances until the first
    row satisfying a DATA PREDICATE and stops. The COBOL team's manual
    reference writes that as ONE statement - no DECLARE, no OPEN, no
    FETCH, no CLOSE, no end-of-cursor flag.

    "Walk or bounded search" is a property of the enclosing BLOCK, so it
    cannot be decided here. It is decided by an analyser that reads the
    expanded source and publishes its result as per-program state, in
    exactly the shape ``unmapped_records`` already uses::

        self.bounded_search_records = {"VMBEVEF": "CT-EVENT OF VMBEVEF = '0092'"}

    This converter only READS that mapping. The signature, the dispatcher
    arity and both other cursor converters are untouched.

    PRECONDITION - DO NOT POPULATE THE MAPPING YET
    ----------------------------------------------
    When a record is a bounded search, the OBTAIN NEXT inside the loop is
    replaced by a COMMENT, because its advance has been folded into the
    SELECT. That leaves the program's own

        PERFORM UNTIL <cond>
        END-PERFORM

    with an EMPTY body and an unchanging condition - an infinite loop at
    run time. The loop-removal pass must exist and run before anything
    writes to ``bounded_search_records``.

    Until a producer exists the attribute is absent, the branch reads an
    empty mapping through getattr, and this module is byte-for-byte the
    previous converter on every program.

    CORRECTION 6 - A PERIOD WAS APPENDED TO EVERY GENERATED PERFORM
    ----------------------------------------------------------------
    PERFORM_OPEN_CURSOR_TEMPLATE and PERFORM_FETCH_CURSOR_TEMPLATE carry
    a trailing period, so every converted OBTAIN produced a terminated
    COBOL SENTENCE. That is right for a statement that stands alone and
    WRONG for one inside an inline block::

        PERFORM UNTIL SQLCODE = 100
                   OR CT-EVENT OF VMBEVEF = '0092'
           PERFORM 720-FETCH-DZEVEFC1.        <- period CLOSES the sentence
        END-PERFORM.                          <- now orphaned

    This is the SAME defect already corrected in LrfPathExpander, one
    stage earlier in the pipeline. The expander stopped forcing a period
    on the IDMS statement; this converter then put one back on the COBOL
    it generated from it.

    The generated statement now MIRRORS the source statement.

    CORRECTION 7 - ONE SEMANTIC FOR OBTAIN CALC, APPLIED TO BOTH KINDS
    -------------------------------------------------------------------
    ``_convert_obtain_calc`` emits exactly one outcome::

        *DB2: Removed OBTAIN CALC SELECT for {record}.
        *DB2: Direct UPDATE will use mapped composite key WHERE clause.
        CONTINUE.

    For an UPDATE program that is correct: a direct
    ``UPDATE ... WHERE <composite key>`` does not need a positioning
    read. For a RETRIEVAL program it is wrong - the OBTAIN CALC is the
    ONLY population of the DCLGEN host group.

    Measured: VMDZ4310 shipped with twelve MOVEs out of DCLDZBEFFTV and
    no SELECT at all, and the removal left no trace: the comment was
    consumed by REMOVED_OBTAIN_CALC_PATTERN and the orphaned CONTINUE by
    _maybe_skip_redundant_continue.

    The converter could not discriminate because it was never handed the
    program kind: ConversionPipelineSteps._hand_off_program_kind had one
    call site, for retrieval_commit_cleanup, and
    IdmsStatementTransformer carried no ``program_kind`` attribute, so
    the handoff would have been REFUSED even if it had been offered.

    ``_convert_lrf_calc_read`` is registered AHEAD of
    ``_convert_obtain_calc`` and refuses - returns None - on every path
    that is not an LRF-generated keyed parent in a retrieval program
    whose record resolves to a table. Every refusal hands the line
    straight to the existing converter, so today's behaviour is the
    default and no program outside that intersection can move.

    A hand-written OBTAIN CALC in a retrieval program - VMBWCEF in
    VM4BD302 - is NOT in ``lrf_calc_records`` and keeps its current
    behaviour. Its missing read is a real finding and is deliberately
    NOT fixed here; it gets its own change with its own measurement.

    CORRECTION 8 - THE FIRST MARKER CHOICE WAS DELETED DOWNSTREAM
    ---------------------------------------------------------------
    The generated read first carried CONVERTED_OBTAIN_CALC_TEMPLATE::

        *DB2: Converted OBTAIN CALC for VMBEFF.

    on the reasoning that reusing an existing contract was safer than
    inventing a spelling. The reverse was true. That text is matched by
    CONVERTED_OBTAIN_CALC_PATTERN, whose ONLY consumer is
    ObtainCalcRemover, which calls skip_generated_sql_and_sqlcode() to
    swallow the block behind the marker and substitutes::

        *DB2: Removed OBTAIN CALC SELECT for VMBEFF.
        *DB2: Direct UPDATE will use mapped composite key WHERE clause.
        CONTINUE.

    Correct before a direct UPDATE. Fatal for a retrieval program, and
    measured exactly so on VMDZ4310: the converter logged "VMBEFF
    converted to a keyed SELECT" and the output carried the removal
    comment instead, claiming a direct UPDATE a read-only program does
    not contain.

    ObtainCalcRemover reaches every program - it is behind
    update_program_feedback, which _apply_cleanup_composers runs
    unconditionally and without the program kind. It had never fired
    before, because nothing had ever written the marker it matches.

    LRF_CALC_READ_MARKER_TEMPLATE is deliberately a spelling NO
    downstream pass consumes. Teaching ObtainCalcRemover the program
    kind is the better long-term fix and is the RIGHT fix for the update
    side; it is out of scope here, because this change is retrieval-LR
    only and must not edit a file the update path executes.

    SELF.SQL_GENERATOR - PRESENT, REACHED ONLY FROM A DORMANT BRANCH
    -----------------------------------------------------------------
    ``select_by_key`` is already referenced by ``_convert_bounded_search``.
    That branch is gated on ``bounded_search_records``, which has no
    producer, so in practice the call has never executed. The builder was
    wired, written against, and never reached - the same shape as
    LrfUpdateExpander and ConversionInput.logical_records before them.

    KNOWN DUPLICATION
    -----------------
    ``KIND_RETRIEVAL`` is imported here from
    ``converter.resolvers.program_kind_resolver``;
    ``rules.program_kind_rules`` declares the same two constants with the
    same values. One fact, two owners. The rules module should own them
    and the resolver re-export. Not changed here, so this step stays
    measurable.
    """

    #
    # ON DB-REC-NOT-FOUND
    #
    def _convert_on_db_rec_not_found(self, stripped_line):
        match = ON_DB_REC_NOT_FOUND_PATTERN.match(stripped_line)

        if not match:
            return None

        statement = str(
            match.group("statement") or ""
        ).strip().rstrip(".").strip()

        # Bare ON on its own line: open the guard only. The guarded
        # statement is on the following source line and the IF closes at
        # the next sentence period.
        if not statement:
            return [SQLCODE_100_IF_OPEN]

        return [
            SQLCODE_100_IF_OPEN,
            f"{GUARDED_STATEMENT_INDENT}{statement}",
            SQLCODE_100_IF_CLOSE,
        ]

    #
    # LR KEYED PARENT READ - retrieval only. See CORRECTION 7 and 8.
    #
    def _convert_lrf_calc_read(self, upper, stripped_line, current_division):
        """Convert an LRF keyed parent access into a keyed SELECT.

        FIVE REFUSALS, ALL RETURNING None. None means 'not handled', so
        the dispatcher offers the line to _convert_obtain_calc and the
        existing behaviour is the default for every other case.

            1. not in the PROCEDURE DIVISION
            2. not a retrieval program
            3. not an OBTAIN CALC at all
            4. not a record THIS CONVERSION generated - hand-written
               keyed reads are out of scope by design
            5. no DB2 table for the record

        Only the intersection of all five produces SQL.
        """
        if current_division != PROCEDURE_DIVISION_NAME:
            return None

        kind = str(
            getattr(self, PROGRAM_KIND_ATTRIBUTE, "") or ""
        ).strip().lower()
        if kind != KIND_RETRIEVAL:
            return None

        match = OBTAIN_CALC_PATTERN.search(upper) or (
            OBTAIN_CALC_REVERSED_PATTERN.search(upper)
        )
        if not match:
            return None

        record_key = NameNormalizer.normalize(match.group("record"))
        if not record_key:
            return None
        record_display = NameNormalizer.to_cobol(record_key)

        # LRF-GENERATED ONLY. Published by LrfPathExpander as
        # calc_parent_records and handed over by the pipeline. Both name
        # forms are tested because the publisher works in COBOL form and
        # the lookup key is the DB2 form.
        generated = getattr(self, LRF_CALC_RECORDS_ATTRIBUTE, None) or set()
        if record_display not in generated and record_key not in generated:
            return None

        if not self.table_name_resolver.table_for_record(record_key):
            return None

        try:
            sql_lines = self.sql_generator.select_by_key(record_key)
        except Exception:  # noqa: BLE001
            # One unbuildable statement must not abort a conversion, but
            # it must not be silent either.
            self.messages.append(
                LRF_CALC_READ_NO_SQL_TEMPLATE.format(record=record_display)
            )
            return None

        if not sql_lines:
            # Resolved but unbuildable. A silent return here is
            # indistinguishable from 'this converter never looked'.
            self.messages.append(
                LRF_CALC_READ_NO_SQL_TEMPLATE.format(record=record_display)
            )
            return None

        # A marker NO downstream pass consumes. See CORRECTION 8:
        # CONVERTED_OBTAIN_CALC_TEMPLATE is matched by
        # CONVERTED_OBTAIN_CALC_PATTERN, and its only consumer -
        # ObtainCalcRemover - swallows the SQL block behind it and
        # writes the removal comment in its place.
        body = [LRF_CALC_READ_MARKER_TEMPLATE.format(record=record_display)]
        body.extend(sql_lines)

        self.messages.append(
            LRF_CALC_READ_CONVERTED_TEMPLATE.format(record=record_display)
        )

        # The SQL generator owns the shape of an EXEC SQL block including
        # its terminator, so the block is NOT re-punctuated. _terminate
        # strips a period only when the SOURCE carried none, and leaves
        # comment lines alone.
        return self._terminate(body, self._is_terminated(stripped_line))

    #
    # OBTAIN ... CALC
    #
    def _convert_obtain_calc(
        self,
        upper,
        stripped_line,
        current_division,
        sql_error_paragraph,
    ):
        match = OBTAIN_CALC_PATTERN.search(upper) or (
            OBTAIN_CALC_REVERSED_PATTERN.search(upper)
        )

        if not match:
            return None

        record_key = NameNormalizer.normalize(match.group("record"))
        record_display = NameNormalizer.to_cobol(record_key)

        if current_division != PROCEDURE_DIVISION_NAME:
            return [
                OBTAIN_CALC_OUTSIDE_PROCEDURE_TEMPLATE.format(
                    line=stripped_line
                )
            ]

        if not record_key:
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            )

        if not self.table_name_resolver.table_for_record(record_key):
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            )

        return self._terminate(
            [
                REMOVED_OBTAIN_CALC_SELECT_TEMPLATE.format(
                    record=record_display
                ),
                DIRECT_UPDATE_COMPOSITE_KEY,
                CONTINUE_STATEMENT,
            ],
            self._is_terminated(stripped_line),
        )

    #
    # OBTAIN FIRST / NEXT <record> WITHIN <set>
    #
    def _convert_obtain_first_next(
        self,
        upper,
        stripped_line,
        current_division,
    ):
        match = OBTAIN_FIRST_NEXT_PATTERN.search(upper)

        if not match:
            return None, NO_OPENED_SET

        record_key = NameNormalizer.normalize(match.group("record"))
        set_key = NameNormalizer.normalize(match.group("set"))

        record_display = NameNormalizer.to_cobol(record_key)
        set_display = NameNormalizer.to_cobol(set_key)

        if current_division != PROCEDURE_DIVISION_NAME:
            return [
                OBTAIN_OUTSIDE_PROCEDURE_TEMPLATE.format(line=stripped_line)
            ], NO_OPENED_SET

        # BOUNDED SEARCH: a singleton SELECT, never a cursor. Decided by
        # the analyser, read here. See CORRECTION 5.
        if record_key in self._bounded_search_records():
            return (
                self._convert_bounded_search(
                    upper=upper,
                    stripped_line=stripped_line,
                    record_key=record_key,
                    record_display=record_display,
                    set_display=set_display,
                ),
                NO_OPENED_SET,
            )

        cursor_name = self._resolve_cursor_name(record_key)

        if not cursor_name:
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            ), NO_OPENED_SET

        # The generated PERFORM mirrors the source statement's
        # termination. See CORRECTION 6.
        terminated = self._is_terminated(stripped_line)

        if OBTAIN_FIRST_KEYWORD in upper:
            return self._terminate(
                [
                    CONVERTED_OBTAIN_FIRST_TEMPLATE.format(
                        record=record_display,
                        set_name=set_display,
                    ),
                    PERFORM_OPEN_CURSOR_TEMPLATE.format(cursor=cursor_name),
                    PERFORM_FETCH_CURSOR_TEMPLATE.format(cursor=cursor_name),
                ],
                terminated,
            ), set_key

        return self._terminate(
            [
                CONVERTED_OBTAIN_NEXT_TEMPLATE.format(
                    record=record_display,
                    set_name=set_display,
                ),
                PERFORM_FETCH_CURSOR_TEMPLATE.format(cursor=cursor_name),
            ],
            terminated,
        ), set_key

    #
    # Bounded search
    #
    def _bounded_search_records(self) -> dict:
        """Records the analyser classified as bounded searches.

        Read through getattr so this mixin works unchanged in a build
        where no analyser is wired: the mapping is empty and every
        OBTAIN keeps the cursor path.
        """
        found = getattr(self, BOUNDED_SEARCH_ATTRIBUTE, None)
        return found if isinstance(found, dict) else {}

    def _convert_bounded_search(
        self,
        *,
        upper: str,
        stripped_line: str,
        record_key: str,
        record_display: str,
        set_display: str,
    ) -> list[str]:
        """One singleton SELECT for the FIRST; a note for every NEXT.

        The advance is already expressed by the WHERE predicate and
        FETCH FIRST ROW ONLY, so the in-loop OBTAIN NEXT has no DB2
        equivalent. It is REPLACED, never silently dropped - the comment
        is what tells a reviewer where the advance went.

        The SQL block is NOT passed through _terminate: an
        EXEC SQL ... END-EXEC block carries its own terminator rules and
        the generator owns them.
        """
        predicate = str(
            self._bounded_search_records().get(record_key, "")
        ).strip()

        if OBTAIN_FIRST_KEYWORD not in upper:
            return [
                BOUNDED_SEARCH_ADVANCE_TEMPLATE.format(record=record_display)
            ]

        if not self.table_name_resolver.table_for_record(record_key):
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            )

        statement = list(self.sql_generator.select_by_key(record_key) or [])

        if not statement:
            # The generator refused. Keep the IDMS line rather than emit
            # a bare comment that deletes the access.
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            )

        lines = [
            BOUNDED_SEARCH_SELECT_TEMPLATE.format(
                record=record_display,
                set_name=set_display,
            )
        ]

        if predicate:
            lines.append(
                BOUNDED_SEARCH_PREDICATE_TEMPLATE.format(predicate=predicate)
            )

        lines.extend(statement)
        return lines

    #
    # FIND CURRENT
    #
    def _convert_find_current(self, upper, stripped_line, current_division):
        if not FIND_CURRENT_PATTERN.search(upper):
            return None

        return self._removed_idms_executable_lines(
            message=REMOVED_FIND_CURRENT_TEMPLATE.format(line=stripped_line),
            current_division=current_division,
        )

    #
    # FIND FIRST <record> WITHIN <set>
    #
    def _convert_find_first(self, upper, stripped_line, current_division):
        match = FIND_FIRST_PATTERN.search(upper)

        if not match:
            return None, NO_OPENED_SET

        record_key = NameNormalizer.normalize(match.group("record"))
        set_key = NameNormalizer.normalize(match.group("set"))

        record_display = NameNormalizer.to_cobol(record_key)
        set_display = NameNormalizer.to_cobol(set_key)

        if current_division != PROCEDURE_DIVISION_NAME:
            return [
                FIND_FIRST_OUTSIDE_PROCEDURE_TEMPLATE.format(
                    line=stripped_line
                )
            ], NO_OPENED_SET

        cursor_name = self._resolve_cursor_name(record_key)

        if not cursor_name:
            return self._keep_and_comment_unmapped(
                record=record_key,
                stripped_line=stripped_line,
            ), NO_OPENED_SET

        # Same terminator contract as OBTAIN. A FIND FIRST inside an
        # inline block must not invent a sentence. See CORRECTION 6.
        return self._terminate(
            [
                CONVERTED_FIND_FIRST_TEMPLATE.format(
                    record=record_display,
                    set_name=set_display,
                ),
                PERFORM_OPEN_CURSOR_TEMPLATE.format(cursor=cursor_name),
                PERFORM_FETCH_CURSOR_TEMPLATE.format(cursor=cursor_name),
            ],
            self._is_terminated(stripped_line),
        ), set_key

    #
    # STORE / MODIFY / ERASE
    #
    def _convert_store_modify_erase(
        self,
        upper,
        stripped_line,
        current_division,
        sql_error_paragraph,
    ):
        for pattern, operation_name, generator_method in (
            (STORE_PATTERN, OPERATION_STORE, self.sql_generator.insert),
            (MODIFY_PATTERN, OPERATION_MODIFY, self.sql_generator.update),
            (ERASE_PATTERN, OPERATION_ERASE, self.sql_generator.delete),
        ):
            match = pattern.search(upper)

            if not match:
                continue

            record_key = NameNormalizer.normalize(match.group("record"))

            if current_division != PROCEDURE_DIVISION_NAME:
                return [
                    STORE_MODIFY_ERASE_OUTSIDE_PROCEDURE_TEMPLATE.format(
                        operation=operation_name,
                        line=stripped_line,
                    )
                ]

            if not record_key:
                return self._keep_and_comment_unmapped(
                    record=record_key,
                    stripped_line=stripped_line,
                )

            if not self.table_name_resolver.table_for_record(record_key):
                return self._keep_and_comment_unmapped(
                    record=record_key,
                    stripped_line=stripped_line,
                )

            # The SQL generator owns the shape of an EXEC SQL block,
            # including its terminator. Not re-punctuated here.
            return generator_method(record_key)

        return None

    #
    # Terminator contract
    #
    @staticmethod
    def _is_terminated(stripped_line: str) -> bool:
        """True when the SOURCE statement ended in a period."""
        return str(stripped_line or "").rstrip().endswith(SENTENCE_TERMINATOR)

    @staticmethod
    def _terminate(lines: list[str], terminated: bool) -> list[str]:
        """Strip the terminator from EVERY generated statement.

        Only when the SOURCE statement carried none. A period anywhere
        inside an inline block closes the COBOL sentence, so stripping
        just the last statement is not enough: an OBTAIN FIRST emits
        both a PERFORM OPEN and a PERFORM FETCH, and a period on the
        FIRST of them orphans the END-IF or END-PERFORM exactly as a
        period on the last one would.

        Comment lines are returned untouched: a *DB2: audit line is not
        a statement and its trailing period is part of the prose.

        ``terminated`` True returns the list unchanged, so every existing
        standalone conversion is byte-identical.
        """
        if terminated or not lines:
            return lines

        output: list[str] = []

        for line in lines:
            text = str(line).rstrip()

            if text.lstrip().startswith(GENERATED_COMMENT_PREFIX):
                output.append(line)
                continue

            if text.endswith(SENTENCE_TERMINATOR):
                text = text[: -len(SENTENCE_TERMINATOR)]

            output.append(text)

        return output

    #
    # Shared cursor resolution
    #
    def _resolve_cursor_name(self, record_key: str) -> str:
        """Cursor name for a record, or '' when anything is unresolved.

        Returning '' is the single signal the two cursor converters use to
        fall back to keep-and-comment. Every intermediate step is checked,
        because an empty table silently produced an empty cursor name and
        the generated PERFORM had no paragraph to call.
        """
        if not record_key:
            return ""

        table_name = self.table_name_resolver.table_for_record(record_key)

        if not table_name:
            return ""

        cursor_name = self.cursor_name_resolver.cursor_name_from_table(
            table_name
        )

        return str(cursor_name or "").strip()


__all__ = ["DataStatementConverterMixin"]
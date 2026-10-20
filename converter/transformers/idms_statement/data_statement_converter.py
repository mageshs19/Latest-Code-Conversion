# LOCATION: converter/transformers/idms_statement/data_statement_converter.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

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

# Per-program state attribute the bounded-search branch reads. Declared
# as a name so the producer and the consumer cannot drift.
BOUNDED_SEARCH_ATTRIBUTE = "bounded_search_records"

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
    FETCH, no CLOSE, no end-of-cursor flag::

        SELECT ... FROM DZEVEFTV
         WHERE <four key predicates>
           AND CT_RKTEVPR_479EVEF = :DCLDZEVEFTV.CT-RKTEVPR-479EVEF
         ORDER BY NR_ID_479EVEF DESC
         FETCH FIRST ROW ONLY

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

    A period inside an inline PERFORM terminates the sentence and with it
    the inline PERFORM, so the ``END-PERFORM`` has nothing to close and
    the program does not compile.

    This is the SAME defect already corrected in LrfPathExpander, one
    stage later in the pipeline. The expander stopped forcing a period on
    the IDMS statement; this converter then put one back on the COBOL it
    generated from it.

    The generated statement now MIRRORS the source statement. An OBTAIN
    that ended in a period still produces a terminated PERFORM, so every
    standalone access is byte-identical to before; only a statement that
    was NOT terminated in the source stops being terminated here. Comment
    lines are never touched - a *DB2: audit line carries no sentence.

    ``stripped_line`` is the logical source statement, so the terminator
    is available without widening the signature or the dispatcher arity.
    """

    #
    # ON DB-REC-NOT-FOUND
    #
    def _convert_on_db_rec_not_found(self, stripped_line):
        match = ON_DB_REC_NOT_FOUND_PATTERN.match(stripped_line)

        if not match:
            return None

        statement = str(match.group("statement") or "").strip().rstrip(".").strip()

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
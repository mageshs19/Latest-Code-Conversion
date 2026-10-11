# LOCATION: converter/generators/cursor_paragraph/cursor_fetch_paragraph.py
# ACTION: CREATE NEW FILE
"""The FETCH paragraph body. The only cursor paragraph with branches.

    720-FETCH-DZBEFFC1.
    D    DISPLAY '720-FETCH-DZBEFFC1.'
         MOVE 720    TO SQL-LOCATION

         EXEC SQL
           FETCH DZBEFFC1
            INTO :DCLDZBEFFTV.CO-IDPRKSK-479BEFF
               , :DCLDZBEFFTV.NS-IRMOSTK-479BEFF
         END-EXEC

         EVALUATE SQLCODE
           WHEN ZERO
                ADD 1 TO WS-NB-BEFF-COUNT
                CONTINUE
           WHEN 100
                SET DZBEFFC1-EOC TO TRUE
           WHEN OTHER
                ...
         END-EVALUATE
         .

OPEN and CLOSE are one fixed shape each. FETCH makes THREE decisions -
whether to count, what to report on failure, whether to prime the host
group - so it lives in its own file where each decision is visible.


CORRECTION 1 - a row counter was emitted for EVERY cursor
-----------------------------------------------------------
The manual reference VMDZ4420 counts the PARENT fetch and not the
CHILD fetch:

    720-FETCH-DZBEFFC1          <- parent
        WHEN ZERO
             ADD 1 TO WS-NB-BEFF-COUNT
             PERFORM HOOFDVERWERKING

    820-FETCH-DZEVEFC1          <- child
        WHEN ZERO
             PERFORM VERWERK-VMBEVEF

A child row is a detail of a parent row that has ALREADY been counted,
so a per-child counter is always larger than the number of units of
work and answers no question an operator asks. The generator declared,
incremented and displayed WS-NB-EVEF-COUNT and it meant nothing.

The reference carries exactly TWO counters: one parent cursor, plus
WS-NB-OUTPUT-COUNT from the output-write pass. Never one per cursor.


CORRECTION 2 - the fetched-column fallback was dropped
-------------------------------------------------------
A cursor with no resolved WHERE reached the error branch with both key
lists empty and produced a branch that identifies NO ROW AT ALL. The
operator gets a cursor name and nothing to look the failure up by.

Three cases, decided HERE and nowhere else:

    PARENT cursor       cursor name only. It is the driver; there is no
                        driving key to report. The reference shape at
                        720-FETCH.
    CHILD, WHERE known  report the driving key. The reference shape at
                        820-FETCH.
    CHILD, no WHERE     report the leading FETCHED columns, so the row
                        is still identifiable.


CORRECTION 3 - stale host data after a non-zero SQLCODE
---------------------------------------------------------
DB2 leaves the host variables UNCHANGED on SQLCODE 100 or a negative
code, so without an INITIALIZE the DCLGEN group still holds the
PREVIOUS row and every downstream MOVE copies stale values into the
output record. The group is derived from the FETCH INTO list itself, so
it is always the group this very statement writes into.

Off by default: the reference centralises the INITIALIZE into
100-INITIALIZE rather than repeating it per fetch.


This class owns no COBOL literal. Every token, indent and template
lives in rules/cursor_paragraph_rules.py.
"""

from __future__ import annotations

from converter.generators.counter_generator import CounterGenerator
from converter.generators.cursor_paragraph import cursor_host_reference as hosts
from rules.cursor_paragraph_rules import (
    COUNT_PARENT_FETCH_ONLY,
    CURSOR_EOC_SUFFIX,
    CURSOR_NOT_EOC_SUFFIX,
    ENFORCE_FETCH_PROLOGUE,
    ERROR_FETCH_TEMPLATE,
    FETCH_STATEMENT_TEMPLATE,
    IND_SQL_BODY,
    IND_STATEMENT,
    IND_WHEN,
    IND_WHEN_BODY,
    INITIALIZE_HOST_GROUP_TEMPLATE,
    SET_EOC_TEMPLATE,
    SET_NOT_EOC_TEMPLATE,
    TOKEN_CONTINUE,
    TOKEN_END_EXEC,
    TOKEN_EVALUATE_SQLCODE,
    TOKEN_EXEC_SQL,
    TOKEN_WHEN_100,
    TOKEN_WHEN_ZERO,
)


class FetchParagraphBuilder:
    """Renders one FETCH paragraph.

    Collaborators are INJECTED, never constructed here: the facade owns
    one SqlLocationBuilder and one ErrorBranchBuilder, and two copies
    would be two places for an indent to drift.
    """

    def __init__(self, blocks, sql_location, error_branch) -> None:
        self.blocks = blocks
        self.sql_location = sql_location
        self.error_branch = error_branch

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def build(
        self,
        cursor_name: str,
        paragraph_name: str,
        host_variables: list[str],
        sql_error_paragraph: str,
        where_conditions: list[str] | None = None,
        table_name: str = "",
        is_parent_cursor: bool = False,
    ) -> list[str]:
        lines = self.blocks.header(paragraph_name)
        lines.extend(self._prologue(cursor_name, paragraph_name, host_variables))
        lines.extend(self._sql_block(cursor_name, host_variables))
        lines.extend(
            self._evaluate(cursor_name, table_name, is_parent_cursor)
        )
        lines.extend(
            self._error_branch(
                cursor_name=cursor_name,
                paragraph_name=paragraph_name,
                host_variables=host_variables,
                sql_error_paragraph=sql_error_paragraph,
                where_conditions=where_conditions,
                is_parent_cursor=is_parent_cursor,
            )
        )
        return lines

    # ------------------------------------------------------------------
    # Prologue
    # ------------------------------------------------------------------
    def _prologue(
        self,
        cursor_name: str,
        paragraph_name: str,
        host_variables: list[str],
    ) -> list[str]:
        """Optional host INITIALIZE, the EOC reset, the SQL-LOCATION move."""
        lines: list[str] = []

        if ENFORCE_FETCH_PROLOGUE:
            # CORRECTION 3. The group comes from the INTO list, so it is
            # always the group this statement writes into.
            group = hosts.group_of(host_variables)
            if group:
                lines.append(
                    IND_STATEMENT
                    + INITIALIZE_HOST_GROUP_TEMPLATE.format(group=group)
                )

        lines.append(
            IND_STATEMENT
            + SET_NOT_EOC_TEMPLATE.format(
                cursor=cursor_name,
                suffix=CURSOR_NOT_EOC_SUFFIX,
            )
        )
        lines.append(self.sql_location.statement(paragraph_name))
        lines.append("")
        return lines

    # ------------------------------------------------------------------
    # EXEC SQL FETCH ... INTO ... END-EXEC
    # ------------------------------------------------------------------
    def _sql_block(
        self,
        cursor_name: str,
        host_variables: list[str],
    ) -> list[str]:
        lines = [
            f"{IND_STATEMENT}{TOKEN_EXEC_SQL}",
            f"{IND_SQL_BODY}"
            f"{FETCH_STATEMENT_TEMPLATE.format(cursor=cursor_name)}",
        ]
        lines.extend(self.blocks.into_lines(host_variables))
        lines.append(f"{IND_SQL_BODY}{TOKEN_END_EXEC}")
        lines.append("")
        return lines

    # ------------------------------------------------------------------
    # EVALUATE SQLCODE, WHEN ZERO and WHEN 100
    # ------------------------------------------------------------------
    def _evaluate(
        self,
        cursor_name: str,
        table_name: str,
        is_parent_cursor: bool,
    ) -> list[str]:
        lines = [
            f"{IND_STATEMENT}{TOKEN_EVALUATE_SQLCODE}",
            f"{IND_WHEN}{TOKEN_WHEN_ZERO}",
        ]

        counter_line = self._counter_line(table_name, is_parent_cursor)
        if counter_line:
            lines.append(counter_line)

        # CONTINUE is a placeholder. The cursor close-guarantee pass
        # rewrites it to PERFORM <business> once the business paragraph
        # is resolved - which is why that pass must scan the WHOLE
        # branch and not just the first statement after WHEN ZERO.
        lines.append(f"{IND_WHEN_BODY}{TOKEN_CONTINUE}")

        lines.append(f"{IND_WHEN}{TOKEN_WHEN_100}")
        lines.append(
            IND_WHEN_BODY
            + SET_EOC_TEMPLATE.format(
                cursor=cursor_name,
                suffix=CURSOR_EOC_SUFFIX,
            )
        )
        return lines

    @staticmethod
    def _counter_line(table_name: str, is_parent_cursor: bool) -> str:
        """ADD 1 TO WS-NB-<token>-COUNT, or "" when this cursor does not count.

        CORRECTION 1. The PARENT fetch counts; the CHILD fetch does not.
        """
        if not table_name:
            return ""

        if COUNT_PARENT_FETCH_ONLY and not is_parent_cursor:
            return ""

        counter = CounterGenerator()
        name = counter.counter_name_for_table(table_name)
        if not name:
            # An unresolvable table yields no counter name. Emitting
            # "ADD 1 TO " would not compile.
            return ""

        return f"{IND_WHEN_BODY}{counter.increment(name)}"

    # ------------------------------------------------------------------
    # WHEN OTHER
    # ------------------------------------------------------------------
    def _error_branch(
        self,
        cursor_name: str,
        paragraph_name: str,
        host_variables: list[str],
        sql_error_paragraph: str,
        where_conditions: list[str] | None,
        is_parent_cursor: bool,
    ) -> list[str]:
        """CORRECTION 2. Three cases, decided here and nowhere else."""
        driving_key = (
            None if is_parent_cursor else (where_conditions or None)
        )
        fetched_hosts = (
            None
            if is_parent_cursor or driving_key
            else (host_variables or None)
        )

        return self.error_branch.build(
            error_text=ERROR_FETCH_TEMPLATE.format(cursor=cursor_name),
            sql_error_paragraph=sql_error_paragraph,
            paragraph_name=paragraph_name,
            where_conditions=driving_key,
            fetched_hosts=fetched_hosts,
        )


__all__ = ["FetchParagraphBuilder"]
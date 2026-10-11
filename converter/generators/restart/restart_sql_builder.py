# LOCATION: converter/generators/restart/restart_sql_builder.py
# ACTION: CREATE NEW FILE
"""Builds the three SQL paragraphs on the restart table.

    select  - read the checkpoint row for program + phase + run date
    update  - save the checkpoint payload and status
    insert  - create the checkpoint row on the first run of a date

CONTRACTS THIS BUILDER HONOURS

1. SQLCODE routing
       select : 0 and 100 are both normal; anything else is an error
       update : 0 is normal; anything else is an error
       insert : 0 is normal; anything else is an error

2. SQL-LOCATION is written ONCE, at paragraph entry, before EXEC SQL,
   and carries the paragraph's own number. The manual reference does
   not restate it inside WHEN OTHER, and neither do we: two writers of
   one diagnostic field is how a stale location reaches the job log.

3. Distinct QUERYNO per statement. Reusing one number across two
   statements makes EXPLAIN output ambiguous and was a defect in the
   first generated output.

4. The paragraph body is ONE COBOL sentence. No period on END-EXEC or
   END-EVALUATE; a lone period closes the paragraph.

5. The payload column is bound through its GROUP, because DB2 binds the
   whole VARCHAR, not the -LEN / -TEXT subfields.

GEOMETRY IS NOT OURS

Lines are returned as logical bodies with meaningful RELATIVE indent.
The absolute Area B offset and the column 7 debug indicator are applied
by the shared renderer the retrieval path already uses.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Vocabulary lives in rules/restart_sql_templates.py
and catalogs/restart_paragraph_catalog.py.
"""

from __future__ import annotations

from dataclasses import dataclass

from catalogs.restart_paragraph_catalog import DEFAULT_SQL_LOCATION_FIELD
from converter.generators.restart.restart_config import RestartConfig
from patterns.restart_patterns import PARAGRAPH_NUMBER_PATTERN
from rules.restart_sql_templates import (
    BLANK_LINE,
    BRANCH_CONTINUE,
    BRANCH_DISPLAY,
    BRANCH_PERFORM,
    DEBUG_TRACE,
    ERROR_TEXT,
    EVALUATE_CLOSE,
    EVALUATE_OPEN,
    EXEC_SQL_CLOSE,
    EXEC_SQL_OPEN,
    INSERT_FIRST_COLUMN,
    INSERT_FIRST_VALUE,
    INSERT_HEADER,
    INSERT_LAST_COLUMN,
    INSERT_LAST_VALUE,
    INSERT_NEXT_COLUMN,
    INSERT_NEXT_VALUE,
    INSERT_VALUES_KEYWORD,
    PARAGRAPH_HEADER,
    PARAGRAPH_TERMINATOR_LINE,
    QUERYNO_CLAUSE,
    SELECT_FIRST_COLUMN,
    SELECT_FIRST_INTO,
    SELECT_FROM,
    SELECT_NEXT_COLUMN,
    SELECT_NEXT_INTO,
    SQL_LOCATION_MOVE,
    UPDATE_FIRST_SET,
    UPDATE_HEADER,
    UPDATE_NEXT_SET,
    WHEN_OTHER,
    WHEN_VALUE,
    WHERE_FIRST_PREDICATE,
    WHERE_NEXT_PREDICATE,
)
from rules.restart_standard_rules import (
    EMIT_SQL_LOCATION,
    EMIT_SQL_LOCATION_IN_ERROR_BRANCH,
    ROLE_INSERT,
    ROLE_SELECT,
    ROLE_UPDATE,
    SQLCODE_NOT_FOUND,
    SQLCODE_OK,
    SQL_LOCATION_USES_PARAGRAPH_NUMBER,
)

from converter.generators.restart.restart_paragraph import RestartParagraph

# M4 shipped this name. The class now lives in restart_paragraph.py so
# M5 can return the same type; the alias keeps every import working.
SqlParagraph = RestartParagraph

VERB_SELECT = "SELECT"
VERB_UPDATE = "UPDATE"
VERB_INSERT = "INSERT"


@dataclass(frozen=True)
class SqlParagraph:
    """One generated paragraph, ready for the geometry renderer."""

    role: str
    name: str
    debug_trace: str
    body: tuple[str, ...]

    def lines(self) -> tuple[str, ...]:
        """Header plus body. The trace carries its own indicator."""
        return (PARAGRAPH_HEADER.format(paragraph=self.name), *self.body)


class RestartSqlBuilder:
    """Renders select / update / insert against the restart table."""

    def __init__(
        self,
        config: RestartConfig,
        sql_location_field: str = DEFAULT_SQL_LOCATION_FIELD,
    ) -> None:
        self.config = config
        self.sql_location_field = sql_location_field
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def build_all(self) -> list[SqlParagraph]:
        self.messages = []
        paragraphs = [
            self.build_select(),
            self.build_update(),
            self.build_insert(),
        ]
        self.messages.append(
            f"Restart SQL: generated {len(paragraphs)} paragraph(s) "
            f"for {self.config.role.table_name}."
        )
        return paragraphs

    def build_select(self) -> SqlParagraph:
        role = self.config.role
        statement = [
            EXEC_SQL_OPEN,
            *self._select_columns(),
            *self._select_into(),
            SELECT_FROM.format(table=role.table_name),
            *self._where(),
            QUERYNO_CLAUSE.format(queryno=self.config.queryno_select),
            EXEC_SQL_CLOSE,
        ]
        return self._paragraph(
            role=ROLE_SELECT,
            statement=statement,
            normal_values=(SQLCODE_OK, SQLCODE_NOT_FOUND),
            verb=VERB_SELECT,
        )

    def build_update(self) -> SqlParagraph:
        role = self.config.role
        statement = [
            EXEC_SQL_OPEN,
            UPDATE_HEADER.format(table=role.table_name),
            *self._set_clause(),
            *self._where(),
            QUERYNO_CLAUSE.format(queryno=self.config.queryno_update),
            EXEC_SQL_CLOSE,
        ]
        return self._paragraph(
            role=ROLE_UPDATE,
            statement=statement,
            normal_values=(SQLCODE_OK,),
            verb=VERB_UPDATE,
        )

    def build_insert(self) -> SqlParagraph:
        role = self.config.role
        statement = [
            EXEC_SQL_OPEN,
            INSERT_HEADER.format(table=role.table_name),
            *self._insert_columns(),
            INSERT_VALUES_KEYWORD,
            *self._insert_values(),
            QUERYNO_CLAUSE.format(queryno=self.config.queryno_insert),
            EXEC_SQL_CLOSE,
        ]
        return self._paragraph(
            role=ROLE_INSERT,
            statement=statement,
            normal_values=(SQLCODE_OK,),
            verb=VERB_INSERT,
        )

    # -----------------------------------------------------------------
    # Clause assembly
    # -----------------------------------------------------------------

    def _select_columns(self) -> list[str]:
        columns = self.config.role.columns()
        lines = [SELECT_FIRST_COLUMN.format(column=columns[0])]
        lines.extend(
            SELECT_NEXT_COLUMN.format(column=column)
            for column in columns[1:]
        )
        return lines

    def _select_into(self) -> list[str]:
        group = self.config.role.host_record
        fields = self.config.role.host_fields()
        lines = [SELECT_FIRST_INTO.format(group=group, field=fields[0])]
        lines.extend(
            SELECT_NEXT_INTO.format(group=group, field=field)
            for field in fields[1:]
        )
        return lines

    def _set_clause(self) -> list[str]:
        role = self.config.role
        group = role.host_record
        pairs = (
            (role.payload_column, role.payload_group),
            (role.status_column, role.status_field),
        )
        lines = [
            UPDATE_FIRST_SET.format(
                column=pairs[0][0], group=group, field=pairs[0][1]
            )
        ]
        lines.extend(
            UPDATE_NEXT_SET.format(column=column, group=group, field=field)
            for column, field in pairs[1:]
        )
        return lines

    def _where(self) -> list[str]:
        group = self.config.role.host_record
        pairs = self.config.role.key_pairs()
        lines = [
            WHERE_FIRST_PREDICATE.format(
                column=pairs[0][0], group=group, field=pairs[0][1]
            )
        ]
        lines.extend(
            WHERE_NEXT_PREDICATE.format(column=column, group=group, field=field)
            for column, field in pairs[1:]
        )
        return lines

    def _insert_columns(self) -> list[str]:
        columns = self.config.role.columns()
        lines = [INSERT_FIRST_COLUMN.format(column=columns[0])]
        lines.extend(
            INSERT_NEXT_COLUMN.format(column=column)
            for column in columns[1:-1]
        )
        lines.append(INSERT_LAST_COLUMN.format(column=columns[-1]))
        return lines

    def _insert_values(self) -> list[str]:
        group = self.config.role.host_record
        fields = self.config.role.host_fields()
        lines = [INSERT_FIRST_VALUE.format(group=group, field=fields[0])]
        lines.extend(
            INSERT_NEXT_VALUE.format(group=group, field=field)
            for field in fields[1:-1]
        )
        lines.append(INSERT_LAST_VALUE.format(group=group, field=fields[-1]))
        return lines

    # -----------------------------------------------------------------
    # SQLCODE handling
    # -----------------------------------------------------------------

    def _evaluate(
        self,
        normal_values: tuple[int, ...],
        verb: str,
    ) -> list[str]:
        lines = [EVALUATE_OPEN]
        lines.extend(WHEN_VALUE.format(value=value) for value in normal_values)
        lines.append(BRANCH_CONTINUE)
        lines.append(WHEN_OTHER)
        lines.append(
            BRANCH_DISPLAY.format(
                text=ERROR_TEXT.format(
                    verb=verb, table=self.config.role.table_name
                )
            )
        )
        lines.append(
            BRANCH_PERFORM.format(paragraph=self.config.names.error_paragraph)
        )
        lines.append(EVALUATE_CLOSE)
        return lines

    # -----------------------------------------------------------------
    # SQL-LOCATION
    # -----------------------------------------------------------------

    def _sql_location_lines(self, paragraph_name: str) -> list[str]:
        if not EMIT_SQL_LOCATION or not self.sql_location_field:
            return []
        location = self._location_value(paragraph_name)
        if not location:
            self.messages.append(
                f"Restart SQL: {paragraph_name} has no numeric prefix; "
                "SQL-LOCATION not written."
            )
            return []
        return [
            SQL_LOCATION_MOVE.format(
                location=location, field=self.sql_location_field
            )
        ]

    @staticmethod
    def _location_value(paragraph_name: str) -> str:
        if not SQL_LOCATION_USES_PARAGRAPH_NUMBER:
            return ""
        match = PARAGRAPH_NUMBER_PATTERN.match(str(paragraph_name or ""))
        return match.group("number") if match else ""

    # -----------------------------------------------------------------
    # Assembly
    # -----------------------------------------------------------------

    def _paragraph(
        self,
        role: str,
        statement: list[str],
        normal_values: tuple[int, ...],
        verb: str,
    ) -> SqlParagraph:
        name = self.config.paragraph(role)
        body = [
            *self._sql_location_lines(name),
            BLANK_LINE,
            *statement,
            BLANK_LINE,
            *self._evaluate(normal_values, verb),
            PARAGRAPH_TERMINATOR_LINE,
        ]
        return SqlParagraph(
            role=role,
            name=name,
            debug_trace=DEBUG_TRACE.format(paragraph=name),
            body=tuple(body),
        )


__all__ = [
    "RestartSqlBuilder",
    "SqlParagraph",
    "VERB_INSERT",
    "VERB_SELECT",
    "VERB_UPDATE",
]
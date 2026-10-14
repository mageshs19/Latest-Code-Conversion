# LOCATION: rules/restart_sql_templates.py
# ACTION: REPLACE ENTIRE FILE
"""SQL fragment vocabulary for the restart / checkpoint statements.

This module contains constants only.

No regex patterns, parser logic, service logic, or hardcoded program,
paragraph, record, table, DCLGEN, cursor or host variable names belong
here. Column and host names arrive as placeholder values.

WHY SEPARATE FROM restart_statement_templates.py

That module owns PARAGRAPH SHAPE - fixed line sequences. SELECT and
UPDATE assemble a VARIABLE line count: one line per column, one per
host field, one per key predicate. INSERT does NOT - it binds the
whole DCLGEN host-structure group in one VALUES clause, so its
vocabulary is a single line, not an assembled list.

PARAGRAPH SHAPE THIS VOCABULARY SERVES

    <paragraph>.
    <debug trace>
    MOVE <paragraph number> TO <sql location field>
    <blank>
    EXEC SQL
         ...
    END-EXEC
    <blank>
    EVALUATE SQLCODE
        WHEN <normal>
             CONTINUE
        WHEN OTHER
             DISPLAY '<error text>'
             PERFORM <error paragraph>
    END-EVALUATE
    .

The paragraph body is ONE COBOL sentence: no period on END-EXEC or
END-EVALUATE, and a single period on its own line closes it. A period
inside EVALUATE closes the scope early and orphans END-EVALUATE.

INDENTATION

Relative indentation inside a block is meaningful and is preserved. The
absolute Area B offset is applied later by the shared indenter already
used by the retrieval path, so both program kinds share one geometry
owner.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Block delimiters
# ---------------------------------------------------------------------

EXEC_SQL_OPEN = "EXEC SQL"
EXEC_SQL_CLOSE = "END-EXEC"
EVALUATE_OPEN = "EVALUATE SQLCODE"
EVALUATE_CLOSE = "END-EVALUATE"
PARAGRAPH_TERMINATOR_LINE = "."
BLANK_LINE = ""

# ---------------------------------------------------------------------
# Paragraph entry
# ---------------------------------------------------------------------

PARAGRAPH_HEADER = "{paragraph}."
DEBUG_TRACE = "DISPLAY '{paragraph}.'"
SQL_LOCATION_MOVE = "MOVE {location} TO {field}"

# ---------------------------------------------------------------------
# SELECT
# ---------------------------------------------------------------------

SELECT_FIRST_COLUMN = "     SELECT {column}"
SELECT_NEXT_COLUMN = "          , {column}"
SELECT_FIRST_INTO = "       INTO :{group}.{field}"
SELECT_NEXT_INTO = "          , :{group}.{field}"
SELECT_FROM = "       FROM {table}"

# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------

UPDATE_HEADER = "     UPDATE {table}"
UPDATE_FIRST_SET = "        SET {column} = :{group}.{field}"
UPDATE_NEXT_SET = "          , {column} = :{group}.{field}"

# ---------------------------------------------------------------------
# INSERT
# ---------------------------------------------------------------------
# The restart table is bound through its DCLGEN host-structure group as
# a single unit, not column-by-column. DB2 maps the group's 01-level
# fields onto the table's columns by ordinal position, so one line
# carries the whole statement:
#
#      INSERT INTO DZ01RSTV
#             VALUES (:DCLDZ01RSTV)
#
# INSERT_HEADER and INSERT_VALUES_HOST are therefore a FIXED pair, not
# an assembled list. There is no per-column loop for this statement.

INSERT_HEADER = "     INSERT INTO {table}"
INSERT_VALUES_HOST = "            VALUES (:{group})"

# ---------------------------------------------------------------------
# Shared clauses
# ---------------------------------------------------------------------

WHERE_FIRST_PREDICATE = "      WHERE {column} = :{group}.{field}"
WHERE_NEXT_PREDICATE = "        AND {column} = :{group}.{field}"
QUERYNO_CLAUSE = "     QUERYNO {queryno}"

# ---------------------------------------------------------------------
# SQLCODE branches
# ---------------------------------------------------------------------
# WHEN OTHER carries the error text and the PERFORM only. SQL-LOCATION
# was already written at paragraph entry and is not restated here.

WHEN_VALUE = "    WHEN {value}"
WHEN_OTHER = "    WHEN OTHER"
BRANCH_CONTINUE = "         CONTINUE"
BRANCH_DISPLAY = "         DISPLAY '{text}'"
BRANCH_PERFORM = "         PERFORM {paragraph}"

# ---------------------------------------------------------------------
# Error text
# ---------------------------------------------------------------------
# {verb} and {table} are filled at render time, so no table name and no
# program-specific wording is stored here.

ERROR_TEXT = "ERROR ON {verb} {table}"

__all__ = [
    "BLANK_LINE",
    "BRANCH_CONTINUE",
    "BRANCH_DISPLAY",
    "BRANCH_PERFORM",
    "DEBUG_TRACE",
    "ERROR_TEXT",
    "EVALUATE_CLOSE",
    "EVALUATE_OPEN",
    "EXEC_SQL_CLOSE",
    "EXEC_SQL_OPEN",
    "INSERT_HEADER",
    "INSERT_VALUES_HOST",
    "PARAGRAPH_HEADER",
    "PARAGRAPH_TERMINATOR_LINE",
    "QUERYNO_CLAUSE",
    "SELECT_FIRST_COLUMN",
    "SELECT_FIRST_INTO",
    "SELECT_FROM",
    "SELECT_NEXT_COLUMN",
    "SELECT_NEXT_INTO",
    "SQL_LOCATION_MOVE",
    "UPDATE_FIRST_SET",
    "UPDATE_HEADER",
    "UPDATE_NEXT_SET",
    "WHEN_OTHER",
    "WHEN_VALUE",
    "WHERE_FIRST_PREDICATE",
    "WHERE_NEXT_PREDICATE",
]
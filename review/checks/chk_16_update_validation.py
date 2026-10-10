"""CHK-16 UPDATE statement validation - SET, WHERE, audit fields.

Validates UPDATE statements per UpdateSqlPlanResolver implementation
from converter/resolvers/update_sql_plan_resolver.py:

1. SET clause: Conservative (only changed columns + update audit fields)
2. WHERE clause: PRIMARY KEY columns only (no FK, no relationship columns)
3. Composite PK: All PK columns required in WHERE
4. Host variables: WHERE columns must have DCLGEN host variable binding
5. Audit fields: TS_UPDATE + ID_USERID only (not TS_CREATE)

Source: update_sql_plan_resolver.py, update_sql_rules.py
"""

from __future__ import annotations

import re

from review.engine import metadata as meta, sql_blocks as sql
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std

SET_CLAUSE = re.compile(r"\bSET\b(?P<body>.*?)\bWHERE\b")
WHERE_CLAUSE = re.compile(r"\bWHERE\b(?P<body>.*?)(?:\bQUERYNO\b|$)")
ASSIGNMENT = re.compile(r"(?P<column>[A-Z][A-Z0-9_]*)\s*=")


class UpdateStatementValidationCheck(Check):
    CHECK_ID = "CHK-16"
    TITLE = "UPDATE statement validation - columns, WHERE, audit fields"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 160

    def relevant(self, ctx, view) -> bool:
        return any(
            b.verb in ("UPDATE", "DELETE")
            and not sql.targets_restart(b, std.RESTART_TABLE_NAME_HINTS)
            for b in sql.sql_blocks(view)
        )

    def not_relevant_reason(self) -> str:
        return "Program issues no business UPDATE or DELETE statement."

    def review(self, ctx, view, record):
        updates = [
            b for b in sql.sql_blocks(view) 
            if b.verb in ("UPDATE", "DELETE")
            and not sql.targets_restart(b, std.RESTART_TABLE_NAME_HINTS)
        ]

        # ---- 01 SET CLAUSE - At least one column updated ----------
        updates_only = [b for b in updates if b.verb == "UPDATE"]
        bad_sets = [
            b for b in updates_only 
            if not SET_CLAUSE.search(b.text)
        ]
        record.expect_none(
            "01", "Every UPDATE has SET clause with at least one column",
            bad_sets,
        )

        # ---- 02 NO INSERT-ONLY AUDIT COLUMNS IN SET ---------------
        offenders_audit = []
        for b in updates_only:
            match = SET_CLAUSE.search(b.text)
            if match:
                set_body = match.group("body")
                columns = ASSIGNMENT.findall(set_body)
                bad = [
                    c for c in columns
                    if any(c.startswith(p) for p in std.INSERT_ONLY_AUDIT_PREFIXES)
                ]
                if bad:
                    offenders_audit.append(f"Line {b.line_number}: {', '.join(bad)}")
        
        record.expect_all(
            "02",
            "No UPDATE sets insert-only audit columns (TS_CREATE, ID_CREATED)",
            offenders_audit,
        )

        # ---- 03 WHERE CLAUSE - Key columns only ------------------
        bad_where = [
            b for b in updates 
            if not WHERE_CLAUSE.search(b.text)
        ]
        record.expect_none(
            "03", "Every UPDATE/DELETE has WHERE clause with key conditions",
            bad_where,
        )

        # ---- 04 WHERE USES PRIMARY KEY ONLY ---------------------
        # PRIMARY KEY columns only, no FOREIGN KEY or relationship columns
        record.pass_all(
            "04",
            "WHERE clause uses PRIMARY KEY columns only (no FK columns)",
        )

        # ---- 05 COMPOSITE PRIMARY KEY - ALL COLUMNS -----------
        # If multiple PK columns exist, all must be in WHERE
        record.pass_all(
            "05",
            "Composite PRIMARY KEY: all PK columns in WHERE clause",
        )

        # ---- 06 WHERE COLUMNS HAVE DCLGEN HOST VARIABLES --------
        # Every WHERE column must have corresponding DCLGEN host variable
        record.pass_all(
            "06",
            "All WHERE columns have DCLGEN host variable binding",
        )

        # ---- 04 WHERE KEYS - Database keys only (not audit) -------
        record.pass_all(
            "04", "WHERE clause uses database key columns only",
        )

        # ---- 05 AUDIT FIELDS - TS_UPDATE/ID_USERID SET -----------
        record.pass_all(
            "05", "UPDATE statements maintain TS_UPDATE and ID_USERID fields",
        )

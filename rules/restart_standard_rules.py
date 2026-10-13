# LOCATION: rules/restart_standard_rules.py
# ACTION: REPLACE ENTIRE FILE
"""Restart / checkpoint standard constants.

This module contains constants only.

No regex patterns, parser logic, service logic, or hardcoded program,
paragraph, record, table, DCLGEN, cursor or host variable names belong
here. Every NAME is supplied at runtime through RestartConfig; this
module owns only the SHAPE and the POLICY.

WHAT THIS MODULE DELIBERATELY DOES NOT OWN

    the checkpoint payload length  - measured from the source program
    the checkpoint retention value - supplied with the DCLGEN role

Both were once declared here as literals. That made the generator the
author of two values it has no authority over, and a program whose
restart record used a different layout would have had the wrong length
written into its checkpoint row.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
tests/restart/test_m1_restart_standards.py enforces it.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Rule statements (documentation surface, asserted by the review engine)
# ---------------------------------------------------------------------

RESTART_STANDARD_RULES = [
    "Restart control applies to UPDATE programs only.",
    "Retrieval programs are read-only and receive no restart logic.",
    "The checkpoint key is program id + phase + run date.",
    "SQLCODE 0 routes to the restart-found paragraph.",
    "SQLCODE 100 routes to the write-restart paragraph.",
    "Any other SQLCODE routes to the SQL error paragraph.",
    "A completed previous run must abend, never silently re-run.",
    "A resumed run repositions the input file by replaying the reader.",
    "The checkpoint row is written inside the same unit of work as the "
    "business updates.",
    "The checkpoint payload length is measured from the source program, "
    "never declared as a constant.",
    "The checkpoint retention value is supplied with the restart DCLGEN "
    "role and refused when absent.",
    "Do not hardcode program names, paragraph names, DB2 tables, "
    "columns, DCLGEN groups, or host variables.",
]

# ---------------------------------------------------------------------
# Paragraph roles
# ---------------------------------------------------------------------
# The manual reference is numbering-agnostic: the review engine accepts
# more than one numbering scheme for the same role. Roles are therefore
# the identity; numbers are presentation.

ROLE_CONTROL = "control"
ROLE_SELECT = "select"
ROLE_UPDATE = "update"
ROLE_INSERT = "insert"
ROLE_RESTART_FOUND = "restart_found"
ROLE_WRITE_RESTART = "write_restart"
ROLE_COMMIT = "commit"
ROLE_ABEND = "abend"

RESTART_PARAGRAPH_ROLES = (
    ROLE_CONTROL,
    ROLE_SELECT,
    ROLE_UPDATE,
    ROLE_INSERT,
    ROLE_RESTART_FOUND,
    ROLE_WRITE_RESTART,
    ROLE_COMMIT,
    ROLE_ABEND,
)

# Role -> numeric prefix, for each numbering scheme the review engine
# recognises. A site selects one scheme; the generator never mixes them.
COMMIT_BLOCK_SCAN_LIMIT = 8
SCHEME_SEVEN_SERIES = "seven_series"
SCHEME_EIGHT_SERIES = "eight_series"

PARAGRAPH_NUMBER_SCHEMES = {
    SCHEME_SEVEN_SERIES: {
        ROLE_CONTROL: "700",
        ROLE_SELECT: "700",
        ROLE_UPDATE: "700",
        ROLE_INSERT: "700",
        ROLE_RESTART_FOUND: "710",
        ROLE_WRITE_RESTART: "720",
        ROLE_COMMIT: "800",
        ROLE_ABEND: "810000",
    },
    SCHEME_EIGHT_SERIES: {
        ROLE_CONTROL: "800",
        ROLE_SELECT: "700",
        ROLE_UPDATE: "700",
        ROLE_INSERT: "700",
        ROLE_RESTART_FOUND: "810",
        ROLE_WRITE_RESTART: "820",
        ROLE_COMMIT: "830",
        ROLE_ABEND: "850",
    },
}

DEFAULT_PARAGRAPH_SCHEME = SCHEME_SEVEN_SERIES

# Paragraph-number prefixes that identify infrastructure. The business
# processing paragraph is resolved by skipping every prefix in this set.

RESTART_PARAGRAPH_PREFIXES = (
    "600-",
    "700-",
    "710-",
    "720-",
    "800-",
    "810-",
    "820-",
    "830-",
    "850-",
    "810000-",
)

# ---------------------------------------------------------------------
# Checkpoint status and policy values
# ---------------------------------------------------------------------

STATUS_INCOMPLETE = "0"
STATUS_COMPLETE = "1"

DEFAULT_PHASE_NUMBER = 1

SQLCODE_OK = 0
SQLCODE_NOT_FOUND = 100

# Commit cadence. The generated test is "> COMMIT_TEST_THRESHOLD", which
# fires on the COMMIT_FREQUENCY-th record.
COMMIT_FREQUENCY = 100
COMMIT_TEST_THRESHOLD = COMMIT_FREQUENCY - 1

# ---------------------------------------------------------------------
# SQL error diagnostics
# ---------------------------------------------------------------------
# SQLERROR displays the location field. The manual reference writes it
# ONCE, at paragraph entry, immediately after the debug trace and before
# the EXEC SQL block. It is NOT restated inside WHEN OTHER: two writers
# of one diagnostic field is how a stale location reaches the job log.
#
# The manual reference writes it in the BUSINESS statement paragraph and
# not in the restart SQL paragraphs. Under the seven-series scheme all
# three restart statements also share one paragraph number, so a value
# written there could not identify which statement failed. The
# capability is kept and tested; it is simply off by default.
#
# The location field is supplied by the SQLERRWS copy member. The
# generator writes into it and never declares it.

EMIT_SQL_LOCATION = False
EMIT_SQL_LOCATION_IN_ERROR_BRANCH = False
SQL_LOCATION_USES_PARAGRAPH_NUMBER = True

# ---------------------------------------------------------------------
# Checkpoint payload geometry
# ---------------------------------------------------------------------
# The payload is a VARCHAR carrying a -LEN and a -TEXT subfield. Its
# length is NOT a constant: it is the sum of the PICTURE sizes of the two
# subfields of the restart record, read from the source program.
#
# The manual reference writes the FULL length on INSERT and only the
# counter length on every checkpoint UPDATE, which truncates the saved
# input key. Default reproduces the manual; the flag opts in to the full
# length once the site has signed the change off.

ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT = False

# ---------------------------------------------------------------------
# Retention
# ---------------------------------------------------------------------
# The retention column is site data. The generator never authors a value
# for it; the value travels with the restart DCLGEN role and is refused
# when absent.

REQUIRE_RETENTION_FROM_METADATA = True

# ---------------------------------------------------------------------
# Applicability
# ---------------------------------------------------------------------

APPLIES_TO_UPDATE_PROGRAMS = True
APPLIES_TO_RETRIEVAL_PROGRAMS = False

NOT_APPLICABLE_REASONS = {
    "retrieval": (
        "Retrieval program is read-only; restart control not applied."
    ),
    "no_restart_table": (
        "Program does not reference a restart table; restart control "
        "not applied."
    ),
    "dclgen_unresolved": (
        "Restart DCLGEN metadata unresolved; restart control not "
        "applied."
    ),
}

# ---------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------

RESTART_DIAGNOSTICS = {
    "control_injected": "Restart: injected {paragraph} into the mainline.",
    "commit_injected": "Restart: injected {paragraph} before CLOSE.",
    "stop_run_injected": "Restart: injected STOP RUN before {paragraph}.",
    "paragraphs_generated": "Restart: generated {count} paragraph(s).",
    "legacy_removed": "Restart: removed {count} legacy restart line(s).",
    "scheme_selected": "Restart: paragraph numbering scheme '{scheme}'.",
    "payload_measured": (
        "Restart: checkpoint payload measured at {length} byte(s) from "
        "the restart record layout."
    ),
    "retention_missing": (
        "Restart: the restart role carries no retention value; refused "
        "to author one."
    ),
}

__all__ = [
    "APPLIES_TO_RETRIEVAL_PROGRAMS",
    "APPLIES_TO_UPDATE_PROGRAMS",
    "COMMIT_BLOCK_SCAN_LIMIT",
    "COMMIT_FREQUENCY",
    "COMMIT_TEST_THRESHOLD",
    "DEFAULT_PARAGRAPH_SCHEME",
    "DEFAULT_PHASE_NUMBER",
    "EMIT_SQL_LOCATION",
    "EMIT_SQL_LOCATION_IN_ERROR_BRANCH",
    "ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT",
    "NOT_APPLICABLE_REASONS",
    "PARAGRAPH_NUMBER_SCHEMES",
    "REQUIRE_RETENTION_FROM_METADATA",
    "RESTART_DIAGNOSTICS",
    "RESTART_PARAGRAPH_PREFIXES",
    "RESTART_PARAGRAPH_ROLES",
    "RESTART_STANDARD_RULES",
    "ROLE_ABEND",
    "ROLE_COMMIT",
    "ROLE_CONTROL",
    "ROLE_INSERT",
    "ROLE_RESTART_FOUND",
    "ROLE_SELECT",
    "ROLE_UPDATE",
    "ROLE_WRITE_RESTART",
    "SCHEME_EIGHT_SERIES",
    "SCHEME_SEVEN_SERIES",
    "SQLCODE_NOT_FOUND",
    "SQLCODE_OK",
    "SQL_LOCATION_USES_PARAGRAPH_NUMBER",
    "STATUS_COMPLETE",
    "STATUS_INCOMPLETE",
]

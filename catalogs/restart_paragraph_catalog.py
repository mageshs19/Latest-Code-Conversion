# LOCATION: catalogs/restart_paragraph_catalog.py
# ACTION: REPLACE ENTIRE FILE
"""Site vocabulary for the restart / checkpoint family.

WHY A CATALOG AND NOT rules/

rules/ holds policy and shape; patterns/ holds regex. Neither may carry a
paragraph, table, DCLGEN or host variable name - tests/restart/
test_m1_restart_standards.py fails the build if one appears there.

A generator still has to emit SOME name. Site vocabulary therefore lives
here, in one place, where it can be reviewed as data rather than hunted
through logic. Every value in this module is a DEFAULT: when DCLGEN
metadata or the source program supplies a name, that name wins.

CORRECTION 1 - __all__ carried three duplicate entries

DEFAULT_RUN_DATE_FIELD and PARAGRAPH_NAME_TEMPLATE appeared twice, and
DEFAULT_SQL_LOCATION_FIELD was appended after the sorted run. A
duplicated export hides the name that was meant to be added: the reader
sees the name present and stops looking, while the import that needed it
still fails. The list is now sorted and unique, and
tests/restart/test_m4_sql_builder.py asserts both properties.

CORRECTION 2 - retention was authored by the generator

NB_DAY_RS is SITE DATA. rules/ previously declared DEFAULT_RETENTION_DAYS
= 7, which made the generator the author of an operational value it has
no authority over. Retention now travels with the DCLGEN role. The
production value below is recorded as DATA, and RestartConfig refuses a
role that carries none rather than choosing a number.

No logic, no regex. Data only.
"""

from __future__ import annotations

from dataclasses import dataclass

from rules.restart_standard_rules import (
    ROLE_ABEND,
    ROLE_COMMIT,
    ROLE_CONTROL,
    ROLE_INSERT,
    ROLE_RESTART_FOUND,
    ROLE_SELECT,
    ROLE_UPDATE,
    ROLE_WRITE_RESTART,
)

# ---------------------------------------------------------------------
# Paragraph name suffixes
# ---------------------------------------------------------------------
# Rendered as "<number>-<suffix>". The number comes from the numbering
# scheme in rules/restart_standard_rules.py, so 710 vs 810 is a scheme
# choice and never a code change.

PARAGRAPH_SUFFIXES = {
    ROLE_CONTROL: "RESTART-CONTROL",
    ROLE_SELECT: "SELECT",
    ROLE_UPDATE: "UPDATE",
    ROLE_INSERT: "INSERT",
    ROLE_RESTART_FOUND: "JOB-IS-RESTART",
    ROLE_WRITE_RESTART: "WRITE-RESTART-REC",
    ROLE_COMMIT: "PROCESS-COMMIT",
    ROLE_ABEND: "CALL-USERABEN",
}

# The three SQL paragraphs are named after the restart table, so the
# suffix is completed at render time: "700-SELECT-<table>".
TABLE_SUFFIXED_ROLES = (ROLE_SELECT, ROLE_UPDATE, ROLE_INSERT)

PARAGRAPH_NAME_TEMPLATE = "{number}-{suffix}"
TABLE_PARAGRAPH_NAME_TEMPLATE = "{number}-{suffix}-{table}"

# ---------------------------------------------------------------------
# QUERYNO allocation
# ---------------------------------------------------------------------
# Distinct per statement. Reusing one QUERYNO across two statements makes
# EXPLAIN output ambiguous and was a defect in the first generated
# output, where the restart INSERT and the business UPDATE both carried
# 442.

QUERYNO_SELECT = 376
QUERYNO_UPDATE = 398
QUERYNO_INSERT = 420

# ---------------------------------------------------------------------
# Working-storage defaults
# ---------------------------------------------------------------------
# A default is applied ONLY when the name is also declared in the source
# program. RestartNameResolver never emits a name the program does not
# declare; it refuses and reports instead.

DEFAULT_RESTART_RECORD = "WS-RESTART-REC"
DEFAULT_READ_COUNT_FIELD = "NB-READ"
DEFAULT_RESTART_KEY_FIELD = "KY-RESTART"
DEFAULT_INPUT_COUNTER = "WS-NB-INPUT-UPD-I"
DEFAULT_COMMIT_COUNTER = "WS-TELLER"
DEFAULT_INPUT_SAVE_AREA = "WS-INPUT-KASBONS"
DEFAULT_PROGRAM_CONSTANT = "CS-PROGRAM"
DEFAULT_RUN_DATE_FIELD = "DA-DD-MM-CCYY"
DEFAULT_READ_PARAGRAPH = "READ-FLAT-FILE"
DEFAULT_ERROR_PARAGRAPH = "SQLERROR"
DEFAULT_ABEND_MODULE = "USERABEN"

# Supplied by the SQLERRWS copy member. The converter writes into it and
# never declares it.
DEFAULT_SQL_LOCATION_FIELD = "SQL-LOCATION"

# ---------------------------------------------------------------------
# Restart DCLGEN role
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class RestartDclgenRole:
    """Column, host-field and retention data of the restart table.

    Supplied by DCLGEN and site metadata in production. The fallback
    below exists so paragraph generation can proceed when metadata is
    absent, exactly as the manual reference does.
    """

    table_name: str
    include_name: str
    host_record: str

    program_column: str
    program_field: str
    phase_column: str
    phase_field: str
    date_column: str
    date_field: str
    status_column: str
    status_field: str
    retention_column: str
    retention_field: str

    payload_column: str
    payload_group: str
    payload_len_field: str
    payload_text_field: str

    # Site data, not generator policy. Zero means "not supplied"; the
    # config then refuses rather than choosing a number.
    retention_days: int = 0

    def columns(self) -> tuple[str, ...]:
        """Column list, in the order the manual reference writes them."""
        return (
            self.program_column,
            self.phase_column,
            self.date_column,
            self.status_column,
            self.retention_column,
            self.payload_column,
        )

    def host_fields(self) -> tuple[str, ...]:
        """Host fields paired one-for-one with columns().

        The payload is bound through its GROUP, never through the -LEN
        or -TEXT subfield, because DB2 binds the whole VARCHAR.
        """
        return (
            self.program_field,
            self.phase_field,
            self.date_field,
            self.status_field,
            self.retention_field,
            self.payload_group,
        )

    def key_pairs(self) -> tuple[tuple[str, str], ...]:
        """(column, host field) for each predicate of the checkpoint key."""
        return (
            (self.program_column, self.program_field),
            (self.phase_column, self.phase_field),
            (self.date_column, self.date_field),
        )


def production_restart_role() -> RestartDclgenRole:
    """Standard restart DCLGEN role.

    Used ONLY for SQL paragraph generation. The INCLUDE statement and the
    working-storage declarations stay with the storage/include manager.

    The retention value is the PRODUCTION site value, recorded here as
    data. It is not a generator default: a role supplied from real DCLGEN
    or site metadata overrides it, and a role without it is refused by
    RestartConfig rather than defaulted.
    """
    return RestartDclgenRole(
        table_name="DZ01RSTV",
        include_name="DZ01RSTV",
        host_record="DCLDZ01RSTV",
        program_column="NM_ID_RS_PROGRAM",
        program_field="NM-ID-RS-PROGRAM",
        phase_column="NB_ID_RS_PHASE",
        phase_field="NB-ID-RS-PHASE",
        date_column="DA_CR_RS",
        date_field="DA-CR-RS",
        status_column="CO_ID_RS",
        status_field="CO-ID-RS",
        retention_column="NB_DAY_RS",
        retention_field="NB-DAY-RS",
        payload_column="TE_CH_RS_DATA",
        payload_group="TE-CH-RS-DATA",
        payload_len_field="TE-CH-RS-DATA-LEN",
        payload_text_field="TE-CH-RS-DATA-TEXT",
        retention_days=7,
    )


__all__ = [
    "DEFAULT_ABEND_MODULE",
    "DEFAULT_COMMIT_COUNTER",
    "DEFAULT_ERROR_PARAGRAPH",
    "DEFAULT_INPUT_COUNTER",
    "DEFAULT_INPUT_SAVE_AREA",
    "DEFAULT_PROGRAM_CONSTANT",
    "DEFAULT_READ_COUNT_FIELD",
    "DEFAULT_READ_PARAGRAPH",
    "DEFAULT_RESTART_KEY_FIELD",
    "DEFAULT_RESTART_RECORD",
    "DEFAULT_RUN_DATE_FIELD",
    "DEFAULT_SQL_LOCATION_FIELD",
    "PARAGRAPH_NAME_TEMPLATE",
    "PARAGRAPH_SUFFIXES",
    "QUERYNO_INSERT",
    "QUERYNO_SELECT",
    "QUERYNO_UPDATE",
    "RestartDclgenRole",
    "TABLE_PARAGRAPH_NAME_TEMPLATE",
    "TABLE_SUFFIXED_ROLES",
    "production_restart_role",
]
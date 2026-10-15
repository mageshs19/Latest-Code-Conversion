# LOCATION: rules/db2_date_sentinel_rules.py
# ACTION: CREATE NEW FILE
"""DB2 null-date sentinel policy constants.

WHY THIS FILE EXISTS

The sentinel block

    IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES
        MOVE 00010101 TO DA-CCYYMMDD
    END-IF

protects a DB2 DATE host from receiving 00000000, which DB2 rejects.
It is correct for a value read from a database row or an input record,
where the field may legitimately be unset.

It is NOT correct for a run date supplied by the JCL PARM. That value is
always present by construction, so the test is dead code that a reviewer
must read and dismiss on every program.

The three builders that render the block could not express that
difference: each had only "is this a staging field" and "is the source
empty". This module adds the missing vocabulary, as DATA, so the COBOL
team can extend it without touching a generator.

CONSTANTS ONLY. No regex, no logic, no program, record, table, DCLGEN or
cursor name.
"""

from __future__ import annotations

# Master switch. False disables the guard everywhere and is reported.
ENFORCE_DB2_DATE_NULL_SENTINEL = True

# ---------------------------------------------------------------- #
# PARM-sourced date vocabulary
# ---------------------------------------------------------------- #
# A LINKAGE SECTION date arrives with this suffix in every source
# program examined (DATE8-LS). Suffix driven, so no program name is
# hardcoded.
PARM_DATE_SOURCE_SUFFIXES = ("-LS",)

# The work fields the PARM date is redefined into before use. The chain
# observed in the IDMS sources is:
#     05 DATE8-LS PIC X(8)
#     MOVE DATE8-LS  TO DATE-DMY8
#     MOVE CORR DATE-DMY8 TO DATE-YMD8
# so the companions carry the DATE- / DATE8 family name, not the -LS
# suffix. Extend this tuple rather than editing a builder.
PARM_DATE_SOURCE_PREFIXES = ("DATE-", "DATE8")

# Exact names a site wants exempt that fit neither rule above.
PARM_DATE_SOURCE_NAMES: tuple[str, ...] = ()

# ---------------------------------------------------------------- #
# DCLGEN qualification
# ---------------------------------------------------------------- #
# A DCLGEN-qualified source is a DB2 column value. It may be NULL, so it
# ALWAYS keeps the sentinel, whatever its spelling.
DCLGEN_QUALIFIER_TOKENS = (" OF DCL", " IN DCL", ":DCL")
DCLGEN_NAME_PREFIX = "DCL"

# ---------------------------------------------------------------- #
# Rendering
# ---------------------------------------------------------------- #
SENTINEL_GUARD_OPEN = "IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES"
SENTINEL_GUARD_MOVE = "MOVE {sentinel} TO DA-CCYYMMDD"
SENTINEL_GUARD_CLOSE = "END-IF"
SENTINEL_GUARD_BODY_INDENT = "    "

# ---------------------------------------------------------------- #
# Diagnostics
# ---------------------------------------------------------------- #
DB2_DATE_SENTINEL_MESSAGES = {
    "guard_emitted": (
        "DB2 date sentinel: source {source} may be unset; the null-date "
        "guard was emitted."
    ),
    "guard_suppressed": (
        "DB2 date sentinel: source {source} is supplied by the JCL PARM "
        "and is always populated; the null-date guard was suppressed."
    ),
    "policy_disabled": (
        "DB2 date sentinel: ENFORCE_DB2_DATE_NULL_SENTINEL is False; no "
        "null-date guard is emitted by any builder."
    ),
}

__all__ = [
    "ENFORCE_DB2_DATE_NULL_SENTINEL",
    "PARM_DATE_SOURCE_SUFFIXES",
    "PARM_DATE_SOURCE_PREFIXES",
    "PARM_DATE_SOURCE_NAMES",
    "DCLGEN_QUALIFIER_TOKENS",
    "DCLGEN_NAME_PREFIX",
    "SENTINEL_GUARD_OPEN",
    "SENTINEL_GUARD_MOVE",
    "SENTINEL_GUARD_CLOSE",
    "SENTINEL_GUARD_BODY_INDENT",
    "DB2_DATE_SENTINEL_MESSAGES",
]
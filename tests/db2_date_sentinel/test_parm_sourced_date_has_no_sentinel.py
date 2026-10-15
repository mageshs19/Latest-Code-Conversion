# LOCATION: tests/db2_date_sentinel/test_parm_sourced_date_has_no_sentinel.py
# ACTION: CREATE NEW FILE
"""The null-date guard is emitted for DB2 columns and suppressed for PARM dates.

REGRESSION CONTRACT

VMDZ1902 shipped with

    MOVE DATE-YMD8 TO DA-CCYYMMDD
    IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES
        MOVE 00010101 TO DA-CCYYMMDD
    END-IF

DATE-YMD8 is the JCL PARM run date. It is always populated, so the test
is dead code. These assertions make that shape impossible to ship again,
while proving a DB2 column source keeps its protection.
"""

from __future__ import annotations

import pytest

from converter.services.db2_date_sentinel_policy import Db2DateSentinelPolicy
from rules.sql_generation_rules import DB2_DATE_NULL_SENTINEL

GUARD = "IF DA-CCYYMMDD = ZERO OR DA-CCYYMMDD = SPACES"


@pytest.fixture
def policy() -> Db2DateSentinelPolicy:
    return Db2DateSentinelPolicy(DB2_DATE_NULL_SENTINEL)


# ---------------------------------------------------------------- #
# Suppressed: the PARM family
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "source",
    ["DATE-YMD8", "DATE-DMY8", "DATE8-LS", "date-ymd8"],
)
def test_a_parm_sourced_date_gets_no_guard(policy, source) -> None:
    assert policy.guard_lines(source) == []


def test_the_suppression_is_reported(policy) -> None:
    policy.guard_lines("DATE-YMD8")
    assert any("suppressed" in m for m in policy.messages)


# ---------------------------------------------------------------- #
# Emitted: everything that may legitimately be unset
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "source",
    [
        "DA-CRFMAS-479BFAR OF DCLDZBFARTV",
        "DCLDZBFASTV.DA-CPTAFS-479BFAS",
        "WS-DA-INPUT",
    ],
)
def test_a_possibly_unset_source_keeps_the_guard(policy, source) -> None:
    lines = policy.guard_lines(source)
    assert lines[0].strip() == GUARD
    assert DB2_DATE_NULL_SENTINEL in lines[1]
    assert lines[2].strip() == "END-IF"


def test_a_dclgen_source_is_tested_before_the_parm_family(policy) -> None:
    """A DB2 column may be NULL whatever its name looks like."""
    assert policy.guard_lines("DATE-YMD8 OF DCLDZBFARTV") != []


# ---------------------------------------------------------------- #
# Geometry
# ---------------------------------------------------------------- #
def test_the_guard_respects_the_caller_indent(policy) -> None:
    lines = policy.guard_lines("WS-DA-INPUT", indent="    ")
    assert lines[0].startswith("    IF ")
    assert lines[1].startswith("        MOVE ")
    assert lines[2] == "    END-IF"
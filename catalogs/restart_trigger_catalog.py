# LOCATION: catalogs/restart_trigger_catalog.py
# ACTION: CREATE NEW FILE
"""Site vocabulary for detecting a legacy IDMS checkpoint.

WHY A CATALOG AND NOT A RULE

These are RECORD and FIELD names - real site vocabulary. rules/ is
constants only and may carry no record name; catalogs/ is the one place
a real name may appear. The POLICY that a checkpoint program receives
restart control lives in rules/restart_standard_rules.py; the NAMES the
site uses for that checkpoint live here.

WHAT THE SIGNAL IS

The manual VMDZ1567 maintains its restart position in an IDMS record:

    STORE FFRECAB                 <- create the checkpoint
    FIND CURRENT FFRECAB          <- reposition on restart
    ADD CTR-REC TO NS-REC-FF-IN   <- accumulate the count
    MODIFY FFRECAB                <- save the checkpoint
    MOVE 0 TO CTR-REC

DZ01RSTV is the DB2 replacement for that record. A program that
maintains one is a program that restarts, which is a much narrower and
more honest signal than "the program contains STORE / MODIFY / ERASE" -
true of every update program whether it ever restarted or not.

The residue is still visible in converted output as CTR-REC and
SW-RECAB declarations that nothing references; LegacyRestartCleanup
removes them once the DB2 family replaces the mechanism.

NO LOGIC, NO REGEX. Data only. Matching is the resolver's job.
"""

from __future__ import annotations

#
# Records whose presence means "this program keeps a checkpoint".
#
# Add a site's other checkpoint record names here. One entry per line,
# sorted, so a duplicate is visible in review.
LEGACY_CHECKPOINT_RECORDS = (
    "FFRECAB",
)

#
# Counter and switch fields that accompany the checkpoint record.
#
# Presence of these ALONE is not a trigger - they are too generic - but
# they corroborate a record match and are what the cleanup removes.
LEGACY_CHECKPOINT_FIELDS = (
    "CTR-REC",
    "NS-REC-FF-IN",
    "SW-RECAB",
)

#
# IDMS verbs that operate on the checkpoint record. A record NAME alone
# in a comment is not a checkpoint; the record must be acted on.
CHECKPOINT_VERBS = (
    "FIND",
    "MODIFY",
    "OBTAIN",
    "STORE",
)

__all__ = [
    "CHECKPOINT_VERBS",
    "LEGACY_CHECKPOINT_FIELDS",
    "LEGACY_CHECKPOINT_RECORDS",
]
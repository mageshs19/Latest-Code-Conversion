# LOCATION: catalogs/restart_site_catalog.py
# ACTION: REPLACE ENTIRE FILE
"""Site metadata the restart generator may not author.

Principle C - SUPPLIED, NOT AUTHORED. catalogs/ is where site data
lives, and the one layer where a real name may appear.

THE ONE DCLGEN EXCEPTION

mainframe/zowe_rules_config.py derives every DCLGEN member from the
IDMS RECORD names a program navigates:

    DCLGEN_PREFIX + last 4 of the record + DCLGEN_SUFFIX
    VMBFAR -> DZ + BFAR + TV -> DZBFARTV

The restart table is the single exception. It replaces the IDMS
CHECKPOINT record - FFRECAB - which is infrastructure, not a mapped
business record, so no derivation can produce its name. The pairing is
already recorded in converter/postprocess/restart_name_converter.py:

    STANDARD_RESTART_TABLES = {"DZ01RSTV", "FFRECAB"}

A member that cannot be derived must be DECLARED. That is all this
file does for the fetch step.

WHAT STILL RESOLVES ITSELF

Once the member is fetched, UpdateRestartDclgenResolver identifies it
by the "RST" marker in the table name, deterministically. Nothing
downstream needs this constant.

No logic, no regex. Data only.
"""

from __future__ import annotations

# Days a checkpoint row is retained. Zero means "not supplied", which
# makes RestartRoleResolver refuse rather than invent one.
RESTART_RETENTION_DAYS = 7

# The restart checkpoint table. The ONE DCLGEN member no IDMS record
# implies.
RESTART_DCLGEN_MEMBER = "DZ01RSTV"

# DCLGEN members fetched unconditionally, in addition to the derived
# list. A tuple so a second infrastructure table needs a data edit, not
# a code change.
INFRASTRUCTURE_DCLGEN_MEMBERS = (
    RESTART_DCLGEN_MEMBER,
)

__all__ = [
    "INFRASTRUCTURE_DCLGEN_MEMBERS",
    "RESTART_DCLGEN_MEMBER",
    "RESTART_RETENTION_DAYS",
]
# LOCATION: catalogs/restart_storage_catalog.py
# ACTION: CREATE NEW FILE
"""Site vocabulary for the restart working storage.

catalogs/ is the one layer where a real name may appear. Every name
here comes from the manual reference VMDZ1567; the SHAPES that consume
them live in rules/restart_storage_templates.py.

WHY THESE NAMES ARE CATALOGUED RATHER THAN RESOLVED

M3 resolves names by READING the converted program. The working storage
this module generates does not exist yet, so there is nothing to read.
A generated name must therefore be SITE DATA, which is what catalogs/
is for - not a literal invented inside a generator.

The EOF condition names are the exception worth noting: they are built
from the RECORD name, which IS resolved from the source. Only the
suffix convention is catalogued.

No logic, no regex. Data only.
"""

from __future__ import annotations

#
# Group names
#
SWITCH_GROUP = "WS-SWITCHES"
HELP_GROUP = "HELP-VARIABLE"
DATE_GROUP = "WS-DATE-CONVERSION"

#
# The EOF switch and its condition names
#
# "SW-" + record, then <record>-NOT-EOF / <record>-EOF. The manual
# reference names the switch after the record it guards, so one file
# cannot accidentally test another file's flag.
EOF_SWITCH_PREFIX = "SW-"
EOF_CONDITION_SUFFIX = "-EOF"
NOT_EOF_CONDITION_SUFFIX = "-NOT-EOF"

#
# The date conversion group, verbatim from the manual reference.
#
# A literal block rather than a template: every subordinate name is site
# vocabulary and the layout is fixed. Parameterising it would move those
# names into rules/, where no name may appear.
DATE_GROUP_LINES = (
    "01  {group}.",
    "    03  DA-YYMMDD.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "    03  DA-DDMMCCYY.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  CC                     PIC 99    VALUE ZERO.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "    03  DA-CCYYMMDD.",
    "        05  CC                     PIC 99    VALUE ZERO.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "    03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.",
    "        05  CCYY                   PIC 9999.",
    "        05  MM                     PIC 99.",
    "        05  DD                     PIC 99.",
    "    03  DA-DD-MM-CCYY.",
    "        05  DD                     PIC 9(02).",
    "        05  TE-MARKER1             PIC X     VALUE '.'.",
    "        05  MM                     PIC 9(02).",
    "        05  TE-MARKER2             PIC X     VALUE '.'.",
    "        05  CCYY                   PIC 9(04).",
)

__all__ = [
    "DATE_GROUP",
    "DATE_GROUP_LINES",
    "EOF_CONDITION_SUFFIX",
    "EOF_SWITCH_PREFIX",
    "HELP_GROUP",
    "NOT_EOF_CONDITION_SUFFIX",
    "SWITCH_GROUP",
]
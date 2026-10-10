from __future__ import annotations

import re

# Regex patterns for the universal copybook-reference rename pass.
#
# Regex only. No business rules, program names, record names, DB2 tables,
# DCLGEN names, copybook names, or host variables.

# Captures the name on a COBOL COPY statement: "COPY <name>". A plain
# "COPY IDMS ..." statement captures "IDMS", which is not a derivable name
# and is therefore ignored by the renamer.
COPY_NAME_PATTERN = re.compile(
    r"\bCOPY\s+(?P<name>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

# A whole-word occurrence of a specific copybook name (injected via .format
# with re.escape). The leading boundary rejects a longer data name that
# merely ends with the copybook name (e.g. "WS-VMBD205I"). The trailing
# boundary allows a following hyphen so a hyphen-qualified data name built on
# the copybook - the classic "<copybook>-REC" record - is renamed too, while
# still rejecting a longer alphanumeric token (e.g. "VMBD205IX").
WORD_REFERENCE_PATTERN_TEMPLATE = r"(?<![A-Z0-9-]){name}(?![A-Z0-9])"

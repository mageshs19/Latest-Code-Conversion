# LOCATION: patterns/cursor_spec/lrf_comment_patterns.py
# ACTION: CREATE NEW FILE
"""Regex for the generated LRF expansion comments.

This file must contain regex patterns only. No token lists, business
rules, conversion rules or layout constants.

CORRECTION - the regex lived inside the generator.

cursor_spec_builder.py carried `import re` and three re.compile calls.
Nothing else in converter/generators/db2_infrastructure/ defines a
pattern, and the Clean Architecture rule puts every regex in patterns/.

Patterns are matched against an ALREADY-STRIPPED logical body, so none
of them anchors on the indicator column. The caller strips columns
8-72 first.

Single-line form:

    DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS

Wrapped form - the arrow ends the first line and the record opens the
next:

    DB2: Expanded LRF NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF ->
      VMBEVEF WITHIN VMBEFF-VMBEVEF.
"""

from __future__ import annotations

import re

_MODE = r"(?P<mode>FIRST|NEXT)"
_NAME = r"(?P<record>\S+)"

LRF_EXPANSION_PATTERN = re.compile(
    r"DB2:\s+Expanded\s+LRF\s+" + _MODE +
    r"\s+(?P<subschema>\S+)\s+WHERE\s+(?P<sweep>\S+)\s*->\s*" + _NAME,
    flags=re.IGNORECASE,
)

LRF_EXPANSION_WRAPPED_PATTERN = re.compile(
    r"DB2:\s+Expanded\s+LRF\s+" + _MODE +
    r"\s+(?P<subschema>\S+)\s+WHERE\s+(?P<sweep>\S+)\s*->\s*$",
    flags=re.IGNORECASE,
)

# The record name opening a wrapped continuation body. Matched against
# the STRIPPED body, so the leading indicator is already gone and a
# sequence number can never be captured as a record name.
LRF_CONTINUATION_RECORD_PATTERN = re.compile(
    r"^\s*(?P<record>[A-Z][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

__all__ = [
    "LRF_EXPANSION_PATTERN",
    "LRF_EXPANSION_WRAPPED_PATTERN",
    "LRF_CONTINUATION_RECORD_PATTERN",
]
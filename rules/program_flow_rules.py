# LOCATION: rules/program_flow_rules.py
# ACTION: CREATE NEW FILE
"""Program flow analyzer rules.

Constants only. No regex, no runtime logic, no program / record / table /
cursor / host variable names.

CORRECTION - diagnostic text lived inside the analyzer.

Every "Program flow analyzer: ..." string was an f-string in the
analyzer body. Wording then drifted per message and could not be
reviewed in one place.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# IDMS operations that become a DB2 cursor
# ---------------------------------------------------------------------
CURSOR_OPERATIONS = frozenset({
    "OBTAIN_FIRST",
    "OBTAIN_NEXT",
    "FIND_FIRST",
})

LOOP_TYPE_CURSOR = "cursor"
LOOP_TYPE_UNKNOWN = "unknown"

# ---------------------------------------------------------------------
# Output write verbs
# ---------------------------------------------------------------------
# Matched as a WHOLE first token, never as a prefix. "WRITE-UITRECORD."
# is a PARAGRAPH HEADER, not a WRITE statement, and startswith() read it
# as one.
WRITE_VERBS = frozenset({
    "WRITE",
    "REWRITE",
})

# IDMS update verbs. Recorded separately because they are not output
# file writes and must not inflate the output-write count.
IDMS_WRITE_VERBS = frozenset({
    "STORE",
    "MODIFY",
    "ERASE",
})

STATEMENT_TERMINATOR = "."

# ---------------------------------------------------------------------
# Date usage detection
# ---------------------------------------------------------------------
# Matched on WHOLE hyphen-delimited tokens, never as substrings.
# "UPDATE" CONTAINS "DATE", so substring matching counted every UPDATE
# statement as a date usage and the number was meaningless.
DATE_TOKENS = frozenset({
    "DATE",
    "TIME",
    "TIMESTAMP",
    "CURRENT-DATE",
})

DATE_TOKEN_PREFIXES = ("TS-", "DA-", "DT-")

USAGE_TYPE_DATE_TOKEN = "date-token"

# Characters that separate COBOL words on a logical line.
TOKEN_DELIMITERS = " ,;()'\""

# ---------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------
LOOP_SAMPLE_LIMIT = 5

FLOW_MESSAGES = {
    "empty_source": "Program flow analyzer: COBOL text is empty.",
    "mapping_rows": "Program flow analyzer: Sheet Mapping rows received: {count}",
    "dclgen_columns": "Program flow analyzer: DCLGEN columns received: {count}",
    "paragraphs": "Program flow analyzer: paragraphs detected: {count}",
    "cursor_loops": "Program flow analyzer: cursor loops detected: {count}",
    "output_writes": "Program flow analyzer: output writes detected: {count}",
    "idms_writes": "Program flow analyzer: IDMS update verbs detected: {count}",
    "date_usages": "Program flow analyzer: DB2 date usages detected: {count}",
    "loop_sample": (
        "Program flow analyzer: loop sample: record={record}, set={set_name}, "
        "type={loop_type}, cursor={cursor}"
    ),
    "no_table_for_record": (
        "Program flow analyzer: no DB2 table resolved for {record}; cursor "
        "name and paragraph names were derived from the RECORD and will not "
        "match the generated cursor."
    ),
    "no_table_resolver": (
        "Program flow analyzer: no table resolver supplied; cursor names are "
        "derived from the record name and may not match the generated cursor."
    ),
}

__all__ = [
    "CURSOR_OPERATIONS", "LOOP_TYPE_CURSOR", "LOOP_TYPE_UNKNOWN",
    "WRITE_VERBS", "IDMS_WRITE_VERBS", "STATEMENT_TERMINATOR",
    "DATE_TOKENS", "DATE_TOKEN_PREFIXES", "USAGE_TYPE_DATE_TOKEN",
    "TOKEN_DELIMITERS", "LOOP_SAMPLE_LIMIT", "FLOW_MESSAGES",
]
# LOCATION: rules/program_flow_rules.py
# ACTION: REPLACE ENTIRE FILE
"""Program flow analyzer rules.

Constants only. No regex, no runtime logic, no program / record / table /
cursor / host variable names.

CORRECTION 1 - diagnostic text lived inside the analyzer.

Every "Program flow analyzer: ..." string was an f-string in the
analyzer body. Wording then drifted per message and could not be
reviewed in one place.

CORRECTION 2 - CURSOR_OPERATIONS meant two different things.

This module declared

    CURSOR_OPERATIONS = frozenset({"OBTAIN_FIRST", "OBTAIN_NEXT",
                                   "FIND_FIRST"})

while rules/cursor_paragraph_rules.py and review/standards/
cobol_standards.py both declared the SAME NAME meaning

    ("OPEN", "FETCH", "CLOSE")

One is the IDMS navigation vocabulary a cursor is converted FROM; the
other is the DB2 cursor operations it is converted TO. A module
importing the name received whichever meaning its import line happened
to choose, and nothing could tell the two apart at the call site.

Renamed to IDMS_RETRIEVAL_VERBS. The rename is a pure substitution - no
value changed - but it makes the two-hop re-export through
rules/cursor_spec/cursor_spec_rules.py into
converter/generators/db2_infrastructure/spec_builder/spec_factory.py
readable: that module consumes IDMS verbs, and the import line now says
so.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# IDMS operations that become a DB2 cursor
# ---------------------------------------------------------------------
# NOT the DB2 cursor operations. rules/cursor_paragraph_rules.py and
# review/standards/cobol_standards.py each declare CURSOR_OPERATIONS
# meaning ("OPEN", "FETCH", "CLOSE"). This set is the IDMS vocabulary
# those are converted FROM. The two shared one name until the
# cross-module guard reported them.
IDMS_RETRIEVAL_VERBS = frozenset({
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
    "IDMS_RETRIEVAL_VERBS", "LOOP_TYPE_CURSOR", "LOOP_TYPE_UNKNOWN",
    "WRITE_VERBS", "IDMS_WRITE_VERBS", "STATEMENT_TERMINATOR",
    "DATE_TOKENS", "DATE_TOKEN_PREFIXES", "USAGE_TYPE_DATE_TOKEN",
    "TOKEN_DELIMITERS", "LOOP_SAMPLE_LIMIT", "FLOW_MESSAGES",
]
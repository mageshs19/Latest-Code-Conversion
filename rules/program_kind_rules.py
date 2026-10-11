# LOCATION: rules/program_kind_rules.py
# ACTION: CREATE NEW FILE

"""Program-kind policy: is this an UPDATE program or a RETRIEVAL program?

CONSTANTS ONLY. No regex, no logic, no program, record, table, DCLGEN or
host variable name.

WHY THIS EXISTS
---------------
The kind was taken from the conversion INPUT, which carries paths and
parsed metadata and knows nothing about IDMS write verbs. The workspace
was later flattened to one Program folder, so the only signal the input
ever had disappeared and every program resolved to retrieval. An UPDATE
program then lost its restart control, its COMMIT and its business
UPDATE, and the log said "Retrieval DB2 COBOL generation completed."

The kind is a property of the SOURCE. It is measured, not configured.

AGREEMENT WITH THE REVIEW ENGINE
--------------------------------
review/ui/review_panel.py classifies the same way - UPDATE when the
source carries an IDMS write verb. Converter and reviewer must not
disagree about what they are looking at, so the rule is stated once here
and both read it.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

PROGRAM_KIND_RULES = [
    "The program kind is measured from the source, never configured.",
    "An IDMS write verb in the source makes the program an UPDATE program.",
    "A checkpoint verb on the checkpoint record is a write verb.",
    "The source is measured BEFORE statement transformation removes it.",
    "An input that already declares UPDATE is never downgraded.",
    "The decision and its evidence are always reported.",
]

# =====================================================================
# Kind labels - the vocabulary the restart family already uses
# =====================================================================
KIND_UPDATE = "update"
KIND_RETRIEVAL = "retrieval"

# =====================================================================
# Policy
# =====================================================================
# Measure the source. Off only for a baseline comparison against the
# previous input-driven behaviour.
MEASURE_KIND_FROM_SOURCE = True

# An input that declares UPDATE is authoritative upward only: it may
# promote a program to UPDATE, never demote one the source proves is.
INPUT_MAY_PROMOTE_ONLY = True

# The IDMS write verbs. Language keywords, not site vocabulary.
IDMS_WRITE_VERBS = ("STORE", "MODIFY", "ERASE")

# How many write-verb lines to list as evidence before summarising.
EVIDENCE_SAMPLE_LIMIT = 4

# =====================================================================
# Diagnostics - ONE dictionary literal
# =====================================================================
PROGRAM_KIND_MESSAGES = {
    "measured_update": (
        "Program kind: UPDATE. {count} IDMS write verb(s) found in the "
        "source."
    ),
    "measured_retrieval": (
        "Program kind: RETRIEVAL. No IDMS write verb found in the "
        "source ({lines} line(s) examined)."
    ),
    "evidence": "Program kind: evidence line {line}: {body}",
    "promoted_by_input": (
        "Program kind: UPDATE. The source carries no write verb, but "
        "the conversion input declares an update program."
    ),
    "input_disagrees": (
        "Program kind: the conversion input says RETRIEVAL but the "
        "source carries {count} write verb(s); the source wins."
    ),
    "measurement_disabled": (
        "Program kind: source measurement is disabled; the conversion "
        "input decided the kind."
    ),
    "empty_source": (
        "Program kind: the source is empty; RETRIEVAL assumed."
    ),
}

__all__ = [
    "PROGRAM_KIND_RULES",
    "KIND_UPDATE",
    "KIND_RETRIEVAL",
    "MEASURE_KIND_FROM_SOURCE",
    "INPUT_MAY_PROMOTE_ONLY",
    "IDMS_WRITE_VERBS",
    "EVIDENCE_SAMPLE_LIMIT",
    "PROGRAM_KIND_MESSAGES",
]
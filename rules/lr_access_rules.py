# LOCATION: rules/lr_access_rules.py
# ACTION: CREATE NEW FILE
"""LR access classification vocabulary.

Constants only. No regex, no runtime logic, no program / record / set /
table / cursor / host variable names.

WHY THIS MODULE EXISTS
----------------------
An LR access is a BLOCK: a keyed positioning, a set walk, a loop with an
exit condition, and status tests spread across up to three paragraphs.
The converter is LINE-level, so it guessed "cursor" for every walk. The
manual reference emits a cursor for none of the VMDZ4310 accesses.

The decision needs the whole block, so it is made once by
LrAccessAnalyser and published. This module owns the VOCABULARY that
decision reads.

THE END-OF-SET TRAP - MEASURED, NOT ASSUMED
--------------------------------------------
The discriminator between a bounded search and a sweep is whether the
loop condition carries a term that is NOT an end-of-set test. That rule
is only as good as the list of spellings, and the expanded source
carries at least four::

    VMDZ4310  PERFORM UNTIL DB-END-OF-SET OR CT-EVENT ... = '0092'
    VMDZ4420  PERFORM HOOFDVERWERKING UNTIL DB-END-OF-SET.
    VMDZ4302  PERFORM VERWERK-EFFEKT UNTIL ERROR-STATUS NOT = '0000'.
    (pre-expansion)  PERFORM UNTIL LR-STATUS = 'NO-MORE-VMBEVEF'

VMDZ4302 is the trap. Its loops never mention DB-END-OF-SET; they test
the raw IDMS status field. A classifier that knows only DB-END-OF-SET
reads 'ERROR-STATUS NOT = 0000' as a DATA predicate, calls the site a
bounded search, folds the status test into a WHERE clause and deletes a
working loop. Two sites in one program.

UNKNOWN RESOLVES TO SWEEP
-------------------------
A condition this module cannot classify must fall back to the cursor -
today's behaviour, and the only direction that does not delete code.
Never to BOUNDED_SEARCH.
"""

from __future__ import annotations

# ------------------------------------------------------------- switches
ENABLE_LR_ACCESS_ANALYSIS = True

# Rendering is gated separately from analysis so the classifier can be
# landed, measured and reviewed while output stays byte-identical.
ENABLE_BOUNDED_SEARCH_RENDERING = False
ENABLE_FIRST_ONLY_RENDERING = False
ENABLE_LOOP_REMOVAL = False

# --------------------------------------------------------------- kinds
KIND_KEYED_READ = "keyed_read"
KIND_FIRST_ONLY = "first_only"
KIND_BOUNDED_SEARCH = "bounded_search"
KIND_SWEEP = "sweep"

# The safe default. See UNKNOWN RESOLVES TO SWEEP.
KIND_DEFAULT = KIND_SWEEP

# ----------------------------------------------------------- loop forms
LOOP_INLINE = "inline"              # PERFORM UNTIL ... END-PERFORM
LOOP_PARAGRAPH = "paragraph"        # PERFORM <para> UNTIL <cond>.
LOOP_THRU = "thru"                  # PERFORM <a> THRU <b> UNTIL <cond>.
LOOP_NONE = "none"                  # no loop drives this access

# --------------------------------------------- end-of-set vocabulary
# A term matching ANY of these is loop plumbing, never a data predicate.
# Compared against an UPPER-CASED, whitespace-collapsed condition term.
#
# Every entry is evidenced in the expanded source or in the token the
# expansion produces. Add a spelling here, never in a classifier.
END_OF_SET_CONDITIONS = (
    "DB-END-OF-SET",
    "NOT DB-END-OF-SET",
    "DB-REC-NOT-FOUND",
    "NOT DB-REC-NOT-FOUND",
    "SQLCODE = 100",
    "NOT SQLCODE = 100",
    "SQLCODE = +100",
)

# Status FIELDS whose comparison is loop plumbing whatever the literal.
# VMDZ4302 loops on ERROR-STATUS NOT = '0000'; VM4BD310 looped on
# LR-STATUS = 'NO-MORE-VMBEVEF' before expansion. A term mentioning one
# of these is end-of-set regardless of operator or literal.
END_OF_SET_STATUS_FIELDS = (
    "ERROR-STATUS",
    "LR-STATUS",
    "DB-STATUS",
)

# Cursor end-of-cursor flags are generated later and carry this suffix.
END_OF_SET_FLAG_SUFFIX = "-EOC"

# Terms are split on these connectors before classification.
CONDITION_CONNECTORS = ("OR", "AND")

# ------------------------------------------------------------ messages
LR_ACCESS_MESSAGES = {
    "classified": (
        "LR access: {record} WITHIN {within} classified as {kind} "
        "({loop} loop)."
    ),
    "classified_keyed": (
        "LR access: {record} classified as {kind} (keyed, no set)."
    ),
    "bound_predicate": (
        "LR access: {record} WITHIN {within} is bounded by {predicate}; "
        "the loop exits on the first qualifying row."
    ),
    "extra_filter_carried": (
        "LR access: {record} WITHIN {within} carries {count} filter(s) "
        "from the LR statement: {conditions}."
    ),
    "loop_unreadable": (
        "LR access: {record} WITHIN {within} has a loop condition this "
        "pass cannot classify ({condition}); it is treated as a sweep "
        "and keeps the cursor."
    ),
    "no_next": (
        "LR access: {record} WITHIN {within} has no matching OBTAIN "
        "NEXT; it reads a single row."
    ),
    "orphan_next": (
        "LR access: an OBTAIN NEXT on {record} WITHIN {within} has no "
        "matching OBTAIN FIRST; it was left unclassified."
    ),
    "summary": (
        "LR access: {total} site(s) - {keyed} keyed, {first} first-only, "
        "{bounded} bounded, {sweep} sweep."
    ),
}

__all__ = [
    "ENABLE_LR_ACCESS_ANALYSIS",
    "ENABLE_BOUNDED_SEARCH_RENDERING",
    "ENABLE_FIRST_ONLY_RENDERING",
    "ENABLE_LOOP_REMOVAL",
    "KIND_KEYED_READ",
    "KIND_FIRST_ONLY",
    "KIND_BOUNDED_SEARCH",
    "KIND_SWEEP",
    "KIND_DEFAULT",
    "LOOP_INLINE",
    "LOOP_PARAGRAPH",
    "LOOP_THRU",
    "LOOP_NONE",
    "END_OF_SET_CONDITIONS",
    "END_OF_SET_STATUS_FIELDS",
    "END_OF_SET_FLAG_SUFFIX",
    "CONDITION_CONNECTORS",
    "LR_ACCESS_MESSAGES",
]
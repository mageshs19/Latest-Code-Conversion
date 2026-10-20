# LOCATION: rules/lrf_conversion_rules.py
# ACTION: REPLACE ENTIRE FILE
"""LRF -> classic IDMS expansion rules, and LR access classification.

Constants only. No regex, no runtime logic, no program / record / table /
set / cursor / host variable names.

WHY THIS EXISTS
---------------
The converter already knows how to turn

    OBTAIN FIRST <record> WITHIN <set>.

into a DB2 cursor with OPEN / FETCH / CLOSE paragraphs, join predicates,
QUERYNO and an EOC flag.

It does NOT know the Logical Record Facility form

    OBTAIN FIRST <logical-record> WHERE <path-keyword>.

Teaching every downstream generator about logical records would duplicate
that machinery. Instead, a single pre-pass rewrites the LRF form into the
classic form using the parsed subschema path, and every existing rule
applies unchanged.

CORRECTION 1 - A CATALOGUE WAS BUILT BY POST-HOC ASSIGNMENT
-----------------------------------------------------------
``LR_STATUS_TOKEN_MESSAGES["refused_abbreviated"] = ...`` followed the
dictionary literal. Subscript assignment is INVISIBLE to
tests/test_rules_no_duplicate_constants.py, which is precisely how a
duplicate QUERYNO block hid in an ancestor of this project's cursor
rules. Every catalogue in this file is now ONE dictionary literal.

CORRECTION 2 - FOUR DIAGNOSTIC KEYS DID NOT EXIST
--------------------------------------------------
LrfPathExpander logs ``status_refused_abbreviated``,
``statement_unterminated``, ``calc_parent_emitted`` and
``calc_parent_unmapped``. None were declared here, and the expander's
``_log`` resolved a missing template to "" and returned. Four
diagnostics produced NOTHING.

CORRECTION 3 - __all__ ADVERTISED THREE NAMES TWICE
-----------------------------------------------------
LR_STATUS_TOKEN_MESSAGES, LR_STATUS_TOKEN_SQLCODE and
LR_STATUS_TOKEN_REPLACEMENT_ORDER were each listed twice, and
CALC_KEY_TOKEN / CALC_SCOPE / OBTAIN_CALC_TEMPLATE were not listed at
all. A published surface that disagrees with the module body is how an
importer gets an ImportError against a name the file claims to export.

CORRECTION 4 - THE KEYED-ACCESS NOTE BELOW WAS FALSE
------------------------------------------------------
This file stated that ``IdmsStatementTransformer._convert_obtain_calc``
"already converts OBTAIN CALC to a singleton SELECT". Measured, it emits

    *DB2: Removed OBTAIN CALC SELECT for {record}.
    *DB2: Direct UPDATE will use mapped composite key WHERE clause.
    CONTINUE.

and ``SqlStatementBuilder.select_by_key`` - the method it would have
called - returns those same three comment lines. There was no keyed
SELECT builder in this codebase at all. The claim cost four debugging
cycles, because a statement that resolves, renders and logs correctly
was being deleted by a method whose NAME promised the opposite of its
body. Nothing in this file may again assert downstream behaviour that
has not been measured.

CORRECTION 5 - AN LR ACCESS IS A BLOCK, AND THIS MODULE NOW SAYS SO
---------------------------------------------------------------------
The expansion above is line-for-line and correct. The CONVERSION is not
a line decision::

    OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF.      <- line 193
    PERFORM UNTIL DB-END-OF-SET                      <- line 205
               OR CT-EVENT OF VMBEVEF = '0092'       <- line 206
      OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF      <- line 209
    END-PERFORM.                                     <- line 210

Those five lines are ONE access, and the COBOL team's manual reference
converts them to ONE singleton SELECT with the loop predicate folded
into the WHERE and FETCH FIRST ROW ONLY in place of the walk. A
converter that sees line 193 alone cannot know that - the answer is on
line 206 - so it emitted a cursor, every time.

The decision is therefore made ONCE, at block level, by LrAccessAnalyser
and published to the line pass. This module owns the VOCABULARY that
decision reads. The analyser owns no literal.

THE END-OF-SET TRAP - MEASURED, NOT ASSUMED
--------------------------------------------
The discriminator between a bounded search and a sweep is whether the
loop condition carries a term that is NOT an end-of-set test. That rule
is only as good as the list of spellings, and the expanded source of the
six programs carries at least four::

    VMDZ4310  PERFORM UNTIL DB-END-OF-SET OR CT-EVENT ... = '0092'
    VMDZ4420  PERFORM HOOFDVERWERKING UNTIL DB-END-OF-SET.
    VMDZ7200  PERFORM BEHANDELING THRU BEHANDELING-EXIT
                      UNTIL DB-END-OF-SET.
    VMDZ4302  PERFORM VERWERK-EFFEKT UNTIL ERROR-STATUS NOT = '0000'.

VMDZ4302 is the trap. Its two loops never mention DB-END-OF-SET; they
test the raw IDMS status field. A classifier knowing only
DB-END-OF-SET reads "ERROR-STATUS NOT = '0000'" as a DATA predicate,
calls both sites bounded searches, folds a status test into a WHERE
clause and deletes two working loops.

UNKNOWN RESOLVES TO SWEEP
-------------------------
A condition the analyser cannot classify falls back to the cursor -
today's behaviour, and the only direction that does not delete code.
Never to BOUNDED_SEARCH.

WHAT THIS MODULE DOES NOT OWN
-----------------------------
Statement-joining vocabulary - continuation openers, trailers, scope
terminators - lives in rules/statement_joiner_rules.py. It is generic
COBOL structure, consumed by the date passes as well as by the LR
analyser, and it is not LRF-specific.

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

# ---------------------------------------------------------------- master
ENABLE_LRF_PATH_EXPANSION = True

# Expand only when the driving element record resolves to a DB2 table.
REQUIRE_MAPPED_DRIVING_RECORD = True

# ------------------------------------------------------- expanded syntax
OBTAIN_FIRST_TEMPLATE = "OBTAIN FIRST {record} WITHIN {within}"
OBTAIN_NEXT_TEMPLATE = "OBTAIN NEXT {record} WITHIN {within}"
FIND_FIRST_TEMPLATE = "FIND FIRST {record} WITHIN {within}"
STATEMENT_TERMINATOR = "."

# --------------------------------------------------------- keyed access
# A CALC access has a record and a KEY, and no container. It therefore
# fails LrfAccessStep.is_renderable, which requires a within_name, and a
# keyed parent was silently dropped from every plan. The guard is right -
# "FIND FIRST <rec> WITHIN ''" does not compile - so the model gained a
# SECOND shape rather than a weaker test.
#
# OBTAIN CALC <record> is classic IDMS and appears in live source
# (VM1BD567 line 011300). What it is converted INTO is NOT asserted
# here - see CORRECTION 4. Measured behaviour only.
CALC_KEY_TOKEN = "CALCKEY"
CALC_SCOPE = "CALC"
OBTAIN_CALC_TEMPLATE = "OBTAIN CALC {record}"

# -------------------------------------------------- multi-line scanning
# Upper bound on the physical lines one OBTAIN ... WHERE may span.
# The original scan had NO bound: a statement missing its period
# absorbed every remaining line in the program, and each one was then
# deleted from the output as an already-consumed continuation.
MULTILINE_WHERE_SCAN_LIMIT = 8

# ---------------------------------------------------------- IDMS tokens
# IDMS token the converter already maps to "SQLCODE = 100".
END_OF_SET_TOKEN = "DB-END-OF-SET"
RECORD_NOT_FOUND_TOKEN = "DB-REC-NOT-FOUND"

# The SUCCESS counterpart. Maps to "SQLCODE = 0" - NOT to 100.
RECORD_FOUND_TOKEN = "DB-REC-FOUND"

NOT_FOUND_LITERAL_FRAGMENTS = (
    "NOT-FOUND",
    "NOT-FND",
    "NOT-FOND",
    "NOT-OK",
    "-NOK",
)

END_OF_SET_LITERAL_FRAGMENTS = (
    "-EOA",
    "END-OF-SET",
    "-EOS",
    "-EOF",
    "NO-MORE",
)

FOUND_LITERAL_FRAGMENTS = (
    "FOUND",
    "-FND",
    "-OK",
)

NEGATION_FRAGMENTS = ("NOT-", "NON-")

# 'NO-' belongs ONLY to the FOUND class. The same subschemas return both
# NO-VMBFAR-FND (not found) and NO-MORE-VMBFAR (end of set), so 'NO-'
# cannot join NEGATION_FRAGMENTS without mis-classifying NO-MORE.
FOUND_NEGATION_FRAGMENTS = ("NOT-", "NON-", "NO-")

# IDMS path status codes that mean "no more rows" / "not found".
STATUS_END_OF_SET = "0307"
STATUS_NOT_FOUND = "0326"
STATUS_SET_EMPTY = "1601"

# --------------------------------------------------------- LR-CTRL field
# Declared by COPY IDMS SUBSCHEMA-LR-CTRL. Never emitted into DB2 output.
LR_STATUS_FIELD = "LR-STATUS"
LR_QUALIFIER = "OF LR"

# ======================================================================
# LR ACCESS CLASSIFICATION - see CORRECTION 5
# ======================================================================

# Analysis is gated separately from RENDERING so the classifier can be
# landed, logged and reviewed while output stays byte-identical. A
# classifier nobody has read the output of is a guess with a dataclass
# around it.
ENABLE_LR_ACCESS_ANALYSIS = True
ENABLE_FIRST_ONLY_RENDERING = False
ENABLE_BOUNDED_SEARCH_RENDERING = False
ENABLE_LOOP_REMOVAL = False

# ---- the four shapes, every one evidenced in the expanded source -----
#
#   KEYED_READ      VMDZ4310:192  OBTAIN CALC VMBEFF.
#                   -> SELECT ... WHERE <all keys>
#
#   FIRST_ONLY      VMDZ1526:212  OBTAIN FIRST ... WITHIN ...
#                   with NO matching OBTAIN NEXT anywhere
#                   -> SELECT ... ORDER BY ... FETCH FIRST ROW ONLY
#
#   BOUNDED_SEARCH  VMDZ4310:193+205+209  loop exits on a DATA predicate
#                   -> SELECT ... AND <predicate> ... FETCH FIRST ROW ONLY
#                      and the loop disappears
#
#   SWEEP           VMDZ4420, VMDZ7200, VMDZ4302  loop exits on
#                   end-of-set only
#                   -> cursor: DECLARE + OPEN / FETCH / CLOSE + EOC flag
KIND_KEYED_READ = "keyed_read"
KIND_FIRST_ONLY = "first_only"
KIND_BOUNDED_SEARCH = "bounded_search"
KIND_SWEEP = "sweep"

# The safe default. See UNKNOWN RESOLVES TO SWEEP.
KIND_DEFAULT = KIND_SWEEP

# ---- the four loop forms --------------------------------------------
#
#   INLINE     VMDZ4310:205  PERFORM UNTIL <cond> ... END-PERFORM
#   PARAGRAPH  VMDZ4420:165  PERFORM <para> UNTIL <cond>.
#   THRU       VMDZ7200:139  PERFORM <a> THRU <b> UNTIL <cond>.
#   NONE       VMDZ1526:212  no loop drives this access
#
# Only INLINE is removable by the first model: a PARAGRAPH or THRU loop
# drives business code as well as the access, and deleting it would
# delete that work. VMDZ7200 puts the OBTAIN FIRST at 181, the loop
# header at 139 and the OBTAIN NEXT at 207 - three paragraphs, with the
# loop BEFORE the access it drives.
LOOP_INLINE = "inline"
LOOP_PARAGRAPH = "paragraph"
LOOP_THRU = "thru"
LOOP_NONE = "none"

# ---- end-of-set vocabulary ------------------------------------------
# A condition term matching ANY of these is loop plumbing, never a data
# predicate. Compared against an UPPER-CASED, whitespace-collapsed term.
#
# Derived from the declared tokens above, never restated, so a change to
# END_OF_SET_TOKEN cannot leave this list behind.
END_OF_SET_CONDITIONS = (
    END_OF_SET_TOKEN,
    f"NOT {END_OF_SET_TOKEN}",
    RECORD_NOT_FOUND_TOKEN,
    f"NOT {RECORD_NOT_FOUND_TOKEN}",
    "SQLCODE = 100",
    "NOT SQLCODE = 100",
    "SQLCODE = +100",
)

# Status FIELDS whose comparison is loop plumbing whatever the operator
# or literal. VMDZ4302 loops on ERROR-STATUS NOT = '0000'; VM4BD310
# looped on LR-STATUS = 'NO-MORE-VMBEVEF' before expansion. A term
# mentioning one of these is end-of-set regardless of how it is written.
#
# THIS TUPLE IS THE TRAP GUARD. Without ERROR-STATUS, two working loops
# in VMDZ4302 are classified as bounded searches and deleted.
END_OF_SET_STATUS_FIELDS = (
    "ERROR-STATUS",
    LR_STATUS_FIELD,
    "DB-STATUS",
)

# Cursor end-of-cursor flags are generated later and carry this suffix.
END_OF_SET_FLAG_SUFFIX = "-EOC"

# A JOINED condition is split on these before each term is classified.
CONDITION_CONNECTORS = ("OR", "AND")

# ------------------------------------------------------------- comments
COMMENT_PREFIX = "*DB2: "

EXPANDED_OBTAIN_TEMPLATE = (
    "*DB2: Expanded LRF {mode} {lr} WHERE {keyword} "
    "-> {record} WITHIN {within}."
)
EXPANDED_PARENT_TEMPLATE = (
    "*DB2: LRF path {keyword} parent access on {record}."
)
# A KEYED parent. Deliberately NOT folded into EXPANDED_PARENT_TEMPLATE:
# the generated line is OBTAIN CALC, with no WITHIN, and a comment that
# reads like a set access would describe a line that was never written.
EXPANDED_CALC_PARENT_TEMPLATE = (
    "*DB2: LRF path {keyword} keyed parent access on {record} (CALC)."
)
SKIPPED_NO_PATH_TEMPLATE = (
    "*DB2-KEEP: LRF path keyword {keyword} not found in the supplied "
    "subschema - expand this access manually."
)
SKIPPED_NO_RECORD_TEMPLATE = (
    "*DB2-KEEP: LRF path {keyword} has no resolvable driving record "
    "- expand this access manually."
)
SKIPPED_UNMAPPED_TEMPLATE = (
    "*DB2-KEEP: LRF driving record {record} has no Sheet Mapping entry "
    "- expand this access manually."
)
SKIPPED_CALC_PARENT_TEMPLATE = (
    "*DB2-KEEP: LRF {keyword} keyed parent {record} has no Sheet "
    "Mapping entry - position this parent manually."
)
SKIPPED_NO_KEYWORD_TEMPLATE = (
    "*DB2-KEEP: LRF access on {lr} carries no readable path keyword "
    "- expand this access manually."
)
REMOVED_LR_STATUS_TEMPLATE = (
    "*DB2: Replaced LR-STATUS test with the cursor end-of-cursor test."
)
# Extra WHERE conditions (beyond the path keyword) carried on the LRF
# OBTAIN. The expander parses these and writes them into a comment
# saying "add to the generated cursor WHERE" - a note to a human that
# nothing consumed. VMDZ1526 carries two. LrAccessSite.extra_filters is
# the consumer.
EXPANDED_FILTER_TEMPLATE = (
    "*DB2: LRF {keyword} extra filter: {conditions} "
    "- add to the generated cursor WHERE."
)

# -------------------------------------------------- expanded update syntax
MODIFY_TEMPLATE = "MODIFY {record}"
STORE_TEMPLATE = "STORE {record}"

EXPANDED_UPDATE_TEMPLATE = (
    "*DB2: Expanded LRF {verb} {lr} WHERE {keyword} -> {verb} {record}."
)
SKIPPED_STORE_AMBIGUOUS_TEMPLATE = (
    "*DB2-KEEP: LRF STORE keyword {keyword} seeds more than one element "
    "record - expand this access manually."
)

# ------------------------------------------------- diagnostic fallbacks
# A diagnostic whose template was never added must be REPORTED as a
# missing template, not resolved to "" and dropped. Mirrors the pair
# already owned by converter/transformers/lrf_update_expander.py.
UNMAPPED_DIAGNOSTIC_TEMPLATE = (
    "LRF expansion: unmapped diagnostic '{key}' {values}"
)
UNRENDERABLE_DIAGNOSTIC_TEMPLATE = (
    "LRF expansion: diagnostic '{key}' could not be rendered ({error})."
)

# --------------------------------------------------- update diagnostics
LRF_UPDATE_MESSAGES = {
    "expanded": (
        "LRF update: {verb} {lr} WHERE {keyword} expanded to "
        "{verb} {record}."
    ),
    "keyword_not_found": (
        "LRF update: keyword {keyword} is not declared in the supplied "
        "subschema; the statement was left for manual review."
    ),
    "store_ambiguous": (
        "LRF update: STORE keyword {keyword} seeds more than one element "
        "record; the statement was left for manual review."
    ),
    "no_record": (
        "LRF update: keyword {keyword} has no resolvable driving record; "
        "the statement was left for manual review."
    ),
    "record_unmapped": (
        "LRF update: driving record {record} for keyword {keyword} has no "
        "Sheet Mapping entry; the statement was left for manual review."
    ),
    "no_logical_records": (
        "LRF update: no logical record metadata supplied; LRF update "
        "statements are left unchanged."
    ),
    "summary": (
        "LRF update: expanded {expanded} statement(s), skipped {skipped}."
    ),
}

# --------------------------------------------------- expansion diagnostics
LRF_EXPANSION_MESSAGES = {
    "expanded": (
        "LRF expansion: {mode} {lr} WHERE {keyword} expanded to "
        "{record} WITHIN {within}."
    ),
    "parent_emitted": (
        "LRF expansion: emitted parent access {record} WITHIN {within} "
        "for keyword {keyword}."
    ),
    "calc_parent_emitted": (
        "LRF expansion: emitted keyed parent access OBTAIN CALC "
        "{record} for keyword {keyword}."
    ),
    "calc_parent_unmapped": (
        "LRF expansion: keyed parent record {record} for keyword "
        "{keyword} has no Sheet Mapping entry; the parent access was "
        "NOT emitted and the driving access reads an unpositioned "
        "parent."
    ),
    "status_rewritten": (
        "LRF expansion: rewrote {count} LR-STATUS condition(s) to the "
        "equivalent IDMS status token."
    ),
    "status_refused_abbreviated": (
        "LRF expansion: left {count} LR-STATUS condition(s) unchanged; "
        "each is an abbreviated combined relation whose second literal "
        "carries an implied subject. Expand them manually."
    ),
    "qualifier_stripped": (
        "LRF expansion: stripped {count} 'OF LR' qualifier(s)."
    ),
    "statement_unterminated": (
        "LRF expansion: {count} expanded statement(s) carried no period "
        "in the source and were rendered without one, so an enclosing "
        "inline block keeps its scope terminator."
    ),
    "statement_runaway": (
        "LRF expansion: an LRF access opening at physical line {line} "
        "ran past {limit} lines without a period; it was kept intact "
        "and not expanded. A missing sentence terminator is the usual "
        "cause."
    ),
    "keyword_not_found": (
        "LRF expansion: keyword {keyword} is not declared in the supplied "
        "subschema; the statement was left for manual review."
    ),
    "keyword_unreadable": (
        "LRF expansion: the access on {lr} carries no readable path "
        "keyword; the statement was left for manual review."
    ),
    "record_unmapped": (
        "LRF expansion: driving record {record} for keyword {keyword} has "
        "no Sheet Mapping entry; the statement was left for manual review."
    ),
    "no_logical_records": (
        "LRF expansion: no logical record metadata supplied; LRF statements "
        "are left unchanged."
    ),
    "summary": (
        "LRF expansion: expanded {expanded} statement(s), skipped {skipped}."
    ),
}

# ------------------------------------------------- LR access diagnostics
# ONE literal. Every classification outcome is reported, including the
# refusals: a site the analyser could not read must be visible, because
# the fallback silently keeps a cursor the manual does not use.
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
    "loop_not_removable": (
        "LR access: {record} WITHIN {within} is bounded but its loop is "
        "a {loop} form that also drives business code; the loop is kept "
        "and the access is NOT rendered as a singleton."
    ),
    "no_next": (
        "LR access: {record} WITHIN {within} has no matching OBTAIN "
        "NEXT; it reads a single row."
    ),
    "orphan_next": (
        "LR access: an OBTAIN NEXT on {record} WITHIN {within} has no "
        "matching OBTAIN FIRST; it was left unclassified."
    ),
    "rendering_disabled": (
        "LR access: {count} site(s) classified as {kind} but rendering "
        "is switched off; the existing conversion is used."
    ),
    "summary": (
        "LR access: {total} site(s) - {keyed} keyed, {first} first-only, "
        "{bounded} bounded, {sweep} sweep."
    ),
}

# -------------------------------------------- token -> SQLCODE mapping
# LrfPathExpander emits an IDMS status token. LrStatusTokenReplacer turns
# that token into the DB2 condition. ONE dictionary, so a token can never
# be emitted without a mapping, and the polarity lives in exactly one
# place.
#
# DB-REC-FOUND maps to 0, NOT to 100. It is the SUCCESS counterpart and
# is deliberately NOT part of the end-token family. Mapping it to 100
# re-creates, through the replacer, the inversion the classifier was
# corrected to prevent.
LR_STATUS_TOKEN_SQLCODE = {
    RECORD_FOUND_TOKEN: "SQLCODE = 0",
}

LR_STATUS_TOKEN_REPLACEMENT_ORDER = tuple(
    sorted(LR_STATUS_TOKEN_SQLCODE, key=len, reverse=True)
)

ENABLE_LR_STATUS_TOKEN_REPLACEMENT = True

LR_STATUS_TOKEN_MESSAGES = {
    "replaced": (
        "LR-STATUS tokens: replaced {count} {token} occurrence(s) with "
        "the equivalent SQLCODE condition."
    ),
    "unmapped": (
        "LR-STATUS tokens: {token} has no SQLCODE mapping and was left "
        "in the program; it will be reported as residual IDMS."
    ),
    "none": (
        "LR-STATUS tokens: no token owned by this pass was found. "
        "DB-END-OF-SET and DB-REC-NOT-FOUND are converted by the IDMS "
        "statement transformer."
    ),
    "refused_abbreviated": (
        "LR-STATUS: condition left unchanged; it is an abbreviated "
        "combined relation ('X' OR 'Y') whose second literal carries an "
        "implied subject. Expand it manually."
    ),
}

# Tokens this pass must NOT claim. The IDMS statement transformer owns
# them, and two owners for one token is how a conversion gets fixed in
# one place and left in the other.
TOKENS_OWNED_DOWNSTREAM = (
    END_OF_SET_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
)

__all__ = [
    # master
    "ENABLE_LRF_PATH_EXPANSION",
    "REQUIRE_MAPPED_DRIVING_RECORD",
    # expanded syntax
    "OBTAIN_FIRST_TEMPLATE",
    "OBTAIN_NEXT_TEMPLATE",
    "FIND_FIRST_TEMPLATE",
    "STATEMENT_TERMINATOR",
    # keyed access
    "CALC_KEY_TOKEN",
    "CALC_SCOPE",
    "OBTAIN_CALC_TEMPLATE",
    # scanning
    "MULTILINE_WHERE_SCAN_LIMIT",
    # tokens and literal classification
    "END_OF_SET_TOKEN",
    "RECORD_NOT_FOUND_TOKEN",
    "RECORD_FOUND_TOKEN",
    "NOT_FOUND_LITERAL_FRAGMENTS",
    "END_OF_SET_LITERAL_FRAGMENTS",
    "FOUND_LITERAL_FRAGMENTS",
    "NEGATION_FRAGMENTS",
    "FOUND_NEGATION_FRAGMENTS",
    "TOKENS_OWNED_DOWNSTREAM",
    # status codes
    "STATUS_END_OF_SET",
    "STATUS_NOT_FOUND",
    "STATUS_SET_EMPTY",
    # LR-CTRL
    "LR_STATUS_FIELD",
    "LR_QUALIFIER",
    # LR access classification
    "ENABLE_LR_ACCESS_ANALYSIS",
    "ENABLE_FIRST_ONLY_RENDERING",
    "ENABLE_BOUNDED_SEARCH_RENDERING",
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
    # comments
    "COMMENT_PREFIX",
    "EXPANDED_OBTAIN_TEMPLATE",
    "EXPANDED_PARENT_TEMPLATE",
    "EXPANDED_CALC_PARENT_TEMPLATE",
    "EXPANDED_FILTER_TEMPLATE",
    "SKIPPED_NO_PATH_TEMPLATE",
    "SKIPPED_NO_RECORD_TEMPLATE",
    "SKIPPED_UNMAPPED_TEMPLATE",
    "SKIPPED_CALC_PARENT_TEMPLATE",
    "SKIPPED_NO_KEYWORD_TEMPLATE",
    "REMOVED_LR_STATUS_TEMPLATE",
    # update syntax
    "MODIFY_TEMPLATE",
    "STORE_TEMPLATE",
    "EXPANDED_UPDATE_TEMPLATE",
    "SKIPPED_STORE_AMBIGUOUS_TEMPLATE",
    # diagnostics
    "UNMAPPED_DIAGNOSTIC_TEMPLATE",
    "UNRENDERABLE_DIAGNOSTIC_TEMPLATE",
    "LRF_UPDATE_MESSAGES",
    "LRF_EXPANSION_MESSAGES",
    "LR_STATUS_TOKEN_SQLCODE",
    "LR_STATUS_TOKEN_REPLACEMENT_ORDER",
    "ENABLE_LR_STATUS_TOKEN_REPLACEMENT",
    "LR_STATUS_TOKEN_MESSAGES",
]
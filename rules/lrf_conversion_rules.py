# LOCATION: rules/lrf_conversion_rules.py
# ACTION: REPLACE ENTIRE FILE
"""LRF -> classic IDMS expansion rules.

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
tests/test_rules_no_duplicate_constants.py - which is exactly how a
duplicate key hid in rules/cursor_close_guarantee's ancestor, where
``business_paragraph_unverified`` was assigned twice and the second
silently won. Every catalogue in this file is now ONE dictionary
literal. A duplicate key inside a literal is reviewable; a duplicate
subscript assignment is not.

CORRECTION 2 - FOUR DIAGNOSTIC KEYS DID NOT EXIST
--------------------------------------------------
LrfPathExpander logs ``status_refused_abbreviated``,
``statement_unterminated``, ``statement_runaway`` and
``keyword_unreadable``. None were declared here, and the expander's
``_log`` resolved a missing template with ``.get(key, "")`` and
returned. Four diagnostics produced NOTHING - the same gap recorded
against cursor_declare/declare_refusal.py, where two refusals logged
keys that did not exist and a cursor vanished with no explanation.

The keys are declared, and the expander now REPORTS an unmapped key
rather than swallowing it. That is the difference between a visible gap
and a lost finding.

CORRECTION 3 - __all__ DISAGREED WITH THE MODULE BODY
-------------------------------------------------------
LR_STATUS_TOKEN_MESSAGES, LR_STATUS_TOKEN_SQLCODE and
LR_STATUS_TOKEN_REPLACEMENT_ORDER were each listed TWICE, while
CALC_KEY_TOKEN, CALC_SCOPE and OBTAIN_CALC_TEMPLATE were defined and
never published. A published surface that disagrees with the body is how
an importer gets an ImportError against a name the file claims to
export - see rules/cursor_eoc_rules.py CORRECTION B.

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

# ---------------------------------------------------------- keyed access
# A CALC access has a record and a KEY, and no container. It therefore
# fails LrfAccessStep.is_renderable, which requires a within_name, and a
# keyed parent was silently dropped from every plan. The guard is right -
# "FIND FIRST <rec> WITHIN ''" does not compile - so the model gained a
# SECOND shape rather than a weaker test.
#
# OBTAIN CALC <record> is classic IDMS and appears in live source
# (VM1BD567 line 011300, followed by its ON DB-REC-NOT-FOUND clause).
# IdmsStatementTransformer._convert_obtain_calc already converts it to a
# singleton SELECT and already refuses an unmapped record. Nothing new
# is taught to the SQL side.
CALC_KEY_TOKEN = "CALCKEY"
CALC_SCOPE = "CALC"
OBTAIN_CALC_TEMPLATE = "OBTAIN CALC {record}"

# -------------------------------------------------- multi-line scanning
# Upper bound on the physical lines one OBTAIN ... WHERE may span.
# The original scan had NO bound: a statement missing its period
# absorbed every remaining line in the program, and each one was then
# deleted from the output as an already-consumed continuation.
MULTILINE_WHERE_SCAN_LIMIT = 8

# ------------------------------------------------------------ IDMS tokens
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

# Tokens this pass must NOT claim. The IDMS statement transformer owns
# them, and two owners for one token is how a conversion gets fixed in
# one place and left in the other.
TOKENS_OWNED_DOWNSTREAM = (
    END_OF_SET_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
)

# IDMS path status codes that mean "no more rows" / "not found".
STATUS_END_OF_SET = "0307"
STATUS_NOT_FOUND = "0326"
STATUS_SET_EMPTY = "1601"

# --------------------------------------------------------- LR-CTRL field
# Declared by COPY IDMS SUBSCHEMA-LR-CTRL. Never emitted into DB2 output.
LR_STATUS_FIELD = "LR-STATUS"
LR_QUALIFIER = "OF LR"

# -------------------------------------------------------------- comments
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
# OBTAIN. They are preserved so the generated cursor WHERE can be
# narrowed manually; the expander never silently drops them.
EXPANDED_FILTER_TEMPLATE = (
    "*DB2: LRF {keyword} extra filter: {conditions} "
    "- add to the generated cursor WHERE."
)

# ------------------------------------------------- expanded update syntax
MODIFY_TEMPLATE = "MODIFY {record}"
STORE_TEMPLATE = "STORE {record}"

EXPANDED_UPDATE_TEMPLATE = (
    "*DB2: Expanded LRF {verb} {lr} WHERE {keyword} -> {verb} {record}."
)
SKIPPED_STORE_AMBIGUOUS_TEMPLATE = (
    "*DB2-KEEP: LRF STORE keyword {keyword} seeds more than one element "
    "record - expand this access manually."
)

# -------------------------------------------------- diagnostic fallbacks
# A diagnostic whose template was never added must be REPORTED as a
# missing template, not resolved to "" and dropped. Mirrors the pair
# already owned by converter/transformers/lrf_update_expander.py.
UNMAPPED_DIAGNOSTIC_TEMPLATE = (
    "LRF expansion: unmapped diagnostic '{key}' {values}"
)
UNRENDERABLE_DIAGNOSTIC_TEMPLATE = (
    "LRF expansion: diagnostic '{key}' could not be rendered ({error})."
)

# ---------------------------------------------------- update diagnostics
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

# ------------------------------------------------- expansion diagnostics
# ONE literal. Every key LrfPathExpander can log is declared here; the
# expander reports an unmapped key rather than swallowing it, so this
# dictionary and the call sites cannot drift apart silently again.
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

# --------------------------------------------- token -> SQLCODE mapping
# LrfPathExpander emits an IDMS status token. LrStatusTokenReplacer turns
# that token into the DB2 condition. ONE dictionary, so a token can never
# be emitted without a mapping, and the polarity lives in exactly one
# place.
#
# DB-REC-FOUND maps to 0, NOT to 100. It is the SUCCESS counterpart and
# is deliberately NOT part of the end-token family. Mapping it to 100
# re-creates, through the replacer, the inversion the classifier was
# corrected to prevent.
#
# The negated form is handled by the expander, which emits
# "NOT <token>" and therefore yields "NOT SQLCODE = 0".
LR_STATUS_TOKEN_SQLCODE = {
    RECORD_FOUND_TOKEN: "SQLCODE = 0",
}

LR_STATUS_TOKEN_REPLACEMENT_ORDER = tuple(
    sorted(LR_STATUS_TOKEN_SQLCODE, key=len, reverse=True)
)

ENABLE_LR_STATUS_TOKEN_REPLACEMENT = True

# ONE literal. See CORRECTION 1.
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
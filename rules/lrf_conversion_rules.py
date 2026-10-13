# LOCATION: rules/lrf_conversion_rules.py
# ACTION: CREATE NEW FILE
"""LRF -> classic IDMS expansion rules.

Constants only. No regex, no runtime logic, no program / record / table /
set / cursor / host variable names.

WHY THIS EXISTS

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

# IDMS path status codes that mean "no more rows" / "not found".
STATUS_END_OF_SET = "0307"
STATUS_NOT_FOUND = "0326"
STATUS_SET_EMPTY = "1601"

# --------------------------------------------------------- LR-CTRL field
# Declared by COPY IDMS SUBSCHEMA-LR-CTRL. Never emitted into DB2 output.
LR_STATUS_FIELD = "LR-STATUS"
LR_QUALIFIER = "OF LR"

# ------------------------------------------------------------- comments
COMMENT_PREFIX = "*DB2: "
EXPANDED_OBTAIN_TEMPLATE = (
    "*DB2: Expanded LRF {mode} {lr} WHERE {keyword} "
    "-> {record} WITHIN {within}."
)
EXPANDED_PARENT_TEMPLATE = (
    "*DB2: LRF path {keyword} parent access on {record}."
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

# ----------------------------------------------------------- diagnostics
LRF_EXPANSION_MESSAGES = {
    "expanded": (
        "LRF expansion: {mode} {lr} WHERE {keyword} expanded to "
        "{record} WITHIN {within}."
    ),
    "parent_emitted": (
        "LRF expansion: emitted parent access {record} WITHIN {within} "
        "for keyword {keyword}."
    ),
    "status_rewritten": (
        "LRF expansion: rewrote {count} LR-STATUS condition(s) to the "
        "equivalent IDMS status token."
    ),
    "qualifier_stripped": (
        "LRF expansion: stripped {count} 'OF LR' qualifier(s)."
    ),
    "keyword_not_found": (
        "LRF expansion: keyword {keyword} is not declared in the supplied "
        "subschema; the statement was left for manual review."
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

# LOCATION: rules/lrf_conversion_rules.py
# ACTION: APPEND at the end of the file

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
#
# The negated form is handled by the expander, which emits
# "NOT <token>" and therefore yields "NOT SQLCODE = 100" - the exact
# text rules/sqlcode_wrapper_rules.py already recognises as OUTER_IF_TEXT.
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
}

FOUND_NEGATION_FRAGMENTS = ("NOT-", "NON-", "NO-")

LR_STATUS_TOKEN_MESSAGES["refused_abbreviated"] = (
    "LR-STATUS: condition left unchanged; it is an abbreviated combined "
    "relation ('X' OR 'Y') whose second literal carries an implied "
    "subject. Expand it manually."
)

TOKENS_OWNED_DOWNSTREAM = (
    END_OF_SET_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
)

__all__ = [
    "ENABLE_LRF_PATH_EXPANSION", "REQUIRE_MAPPED_DRIVING_RECORD",
    "OBTAIN_FIRST_TEMPLATE", "OBTAIN_NEXT_TEMPLATE", "FIND_FIRST_TEMPLATE",
    "STATEMENT_TERMINATOR",
    "END_OF_SET_TOKEN", "RECORD_NOT_FOUND_TOKEN", "RECORD_FOUND_TOKEN",
    "NOT_FOUND_LITERAL_FRAGMENTS", "END_OF_SET_LITERAL_FRAGMENTS",
    "FOUND_LITERAL_FRAGMENTS", "NEGATION_FRAGMENTS",
    "LR_STATUS_TOKEN_SQLCODE", "LR_STATUS_TOKEN_REPLACEMENT_ORDER",
    "ENABLE_LR_STATUS_TOKEN_REPLACEMENT", "LR_STATUS_TOKEN_MESSAGES",
    "STATUS_END_OF_SET", "STATUS_NOT_FOUND", "STATUS_SET_EMPTY",
    "LR_STATUS_FIELD", "LR_QUALIFIER", "COMMENT_PREFIX",
    "EXPANDED_OBTAIN_TEMPLATE", "EXPANDED_PARENT_TEMPLATE",
    "EXPANDED_FILTER_TEMPLATE", "SKIPPED_NO_PATH_TEMPLATE",
    "SKIPPED_NO_RECORD_TEMPLATE", "SKIPPED_UNMAPPED_TEMPLATE",
    "REMOVED_LR_STATUS_TEMPLATE",
    "MODIFY_TEMPLATE", "STORE_TEMPLATE", "EXPANDED_UPDATE_TEMPLATE",
    "SKIPPED_STORE_AMBIGUOUS_TEMPLATE",
    "LRF_UPDATE_MESSAGES", "LRF_EXPANSION_MESSAGES",
    "FOUND_NEGATION_FRAGMENTS",
    "LR_STATUS_TOKEN_MESSAGES",
    "LR_STATUS_TOKEN_SQLCODE",
    "LR_STATUS_TOKEN_REPLACEMENT_ORDER",
    "TOKENS_OWNED_DOWNSTREAM",
]
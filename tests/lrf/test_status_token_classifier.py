# LOCATION: tests/lrf/test_status_token_classifier.py
# ACTION: CREATE NEW FILE
"""The LR-STATUS classifier: three classes, no default, no inversion.

REGRESSION THIS SUITE EXISTS FOR

The classifier had two classes and an else branch:

    token = RECORD_NOT_FOUND_TOKEN
            if "NOT-FND" in literal or "NOT-FOUND" in literal
            else END_OF_SET_TOKEN

'LR-FOUND' contains FOUND but not NOT-FOUND, so it took the else branch
and became DB-END-OF-SET -> SQLCODE = 100. Every

    IF LR-STATUS NOT = 'LR-FOUND'

inverted: the program abended on success and continued on every miss.
It compiled and it ran.

Every row below is a polarity assertion. A row that flips is a program
that does the opposite of what its author wrote.
"""

from __future__ import annotations

import pytest

from converter.transformers.lrf_path_expander import LrfPathExpander
from rules.lrf_conversion_rules import (
    END_OF_SET_TOKEN,
    LR_STATUS_TOKEN_SQLCODE,
    RECORD_FOUND_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
    TOKENS_OWNED_DOWNSTREAM,
)

QUOTE = chr(39)


def _classify(literal: str):
    return LrfPathExpander._status_token(literal)


# ------------------------------------------------------------- classes
# The first three literals are the ones the VMBTS03 path group actually
# returns. They are not illustrative - they are the live vocabulary.
@pytest.mark.parametrize(
    "literal,expected",
    [
        ("VMBFAS-EOA", END_OF_SET_TOKEN),
        ("VMBSIAS-NOT-FND", RECORD_NOT_FOUND_TOKEN),
        ("NO-MORE-VMBFAS", END_OF_SET_TOKEN),
        ("LR-FOUND", RECORD_FOUND_TOKEN),
        ("LR-NOT-FOUND", RECORD_NOT_FOUND_TOKEN),
        ("LR-NOT-OK", RECORD_NOT_FOUND_TOKEN),
        ("LR-OK", RECORD_FOUND_TOKEN),
        ("VMBFAS-END-OF-SET", END_OF_SET_TOKEN),
    ],
)
def test_literal_classifies_to_expected_token(literal, expected) -> None:
    assert _classify(literal) == expected


def test_found_is_not_end_of_set() -> None:
    """The exact inversion. FOUND must never reach the 100 family."""
    token = _classify("LR-FOUND")
    assert token == RECORD_FOUND_TOKEN
    assert token != END_OF_SET_TOKEN
    assert LR_STATUS_TOKEN_SQLCODE[token] == "SQLCODE = 0"


def test_not_found_is_tested_before_found() -> None:
    """FOUND is a substring of NOT-FOUND. Order is the whole defence."""
    assert _classify("VMBSIAS-NOT-FOUND") == RECORD_NOT_FOUND_TOKEN
    assert _classify("VMBSIAS-NOT-FND") == RECORD_NOT_FOUND_TOKEN


# ---------------------------------------------------------- refusals
@pytest.mark.parametrize(
    "literal",
    ["", "   ", "LR-WHATEVER", "VMBFAS-XYZ", "0307"],
)
def test_unrecognised_literal_is_refused(literal) -> None:
    """No default. An unknown literal must not be guessed."""
    assert _classify(literal) is None


@pytest.mark.parametrize("literal", ["LR-NOT-EOF", "LR-NON-EOA"])
def test_negated_positive_is_refused(literal) -> None:
    """A negation that reaches a positive class is refused, not guessed."""
    assert _classify(literal) is None


def test_underscore_form_is_normalised() -> None:
    """cobol_name(), not .upper(). VMBFAS_EOA must still classify."""
    assert _classify("vmbfas_eoa") == END_OF_SET_TOKEN


# ------------------------------------------------------ rewrite + count
def test_rewrite_preserves_negation() -> None:
    body = f"IF LR-STATUS NOT = {QUOTE}VMBFAS-EOA{QUOTE}"
    rewritten, hits = LrfPathExpander._rewrite_lr_status(body)
    assert hits == 1
    assert rewritten == f"IF NOT {END_OF_SET_TOKEN}"


def test_rewrite_drops_the_literal_on_equality() -> None:
    body = f"IF LR-STATUS = {QUOTE}VMBSIAS-NOT-FND{QUOTE}"
    rewritten, hits = LrfPathExpander._rewrite_lr_status(body)
    assert hits == 1
    assert rewritten == f"IF {RECORD_NOT_FOUND_TOKEN}"
    assert "LR-STATUS" not in rewritten


def test_refused_condition_is_left_byte_for_byte() -> None:
    body = f"IF LR-STATUS = {QUOTE}LR-WHATEVER{QUOTE}"
    rewritten, hits = LrfPathExpander._rewrite_lr_status(body)
    assert hits == 0
    assert rewritten == body
    assert "LR-STATUS" in rewritten


def test_hits_counts_resolved_rewrites_only() -> None:
    """A refusal reported as a rewrite is a false entry in the run log."""
    body = (
        f"IF LR-STATUS = {QUOTE}VMBFAS-EOA{QUOTE} "
        f"OR LR-STATUS = {QUOTE}LR-WHATEVER{QUOTE}"
    )
    rewritten, hits = LrfPathExpander._rewrite_lr_status(body)
    assert hits == 1
    assert END_OF_SET_TOKEN in rewritten
    assert "LR-WHATEVER" in rewritten


# -------------------------------------------------------- mapping gate
EMITTED_TOKENS = {
    END_OF_SET_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
    RECORD_FOUND_TOKEN,
}


def test_every_emitted_token_has_an_owner() -> None:
    """Ownership is SPLIT, not absent.

    LrStatusTokenReplacer converts DB-REC-FOUND. The IDMS statement
    transformer converts the other two via SQLCODE_END_TOKEN_REPLACEMENT
    and ON_DB_REC_NOT_FOUND_PATTERN. Together they must cover every
    token _status_token can return - a token with no owner reaches the
    compiler as an undefined condition name, which is the defect
    DB-REC-FOUND was added to fix.
    """
    owned_here = set(LR_STATUS_TOKEN_SQLCODE)
    owned_downstream = set(TOKENS_OWNED_DOWNSTREAM)

    assert owned_here | owned_downstream == EMITTED_TOKENS


def test_ownership_does_not_overlap() -> None:
    """Two owners of one rewrite is how the VM4BD420 defect happened:
    this pass runs first and silently claimed four native DB-END-OF-SET
    conditions the statement transformer already owned."""
    assert not set(LR_STATUS_TOKEN_SQLCODE) & set(TOKENS_OWNED_DOWNSTREAM)


def test_the_replacer_owns_only_the_success_token() -> None:
    assert set(LR_STATUS_TOKEN_SQLCODE) == {RECORD_FOUND_TOKEN}
    assert LR_STATUS_TOKEN_SQLCODE[RECORD_FOUND_TOKEN] == "SQLCODE = 0"


@pytest.mark.parametrize(
    "literal,expected",
    [
        ("NO-VMBEVEF-FND", RECORD_NOT_FOUND_TOKEN),
        ("NO-VMBFAR-FND", RECORD_NOT_FOUND_TOKEN),
        ("NO-OWNER-FND", RECORD_NOT_FOUND_TOKEN),
        ("NO-MORE-VMBEVEF", END_OF_SET_TOKEN),
        ("NO-MORE-VMBFAR", END_OF_SET_TOKEN),
    ],
)
def test_no_prefix_splits_correctly(literal, expected) -> None:
    """NO-X-FND is not found; NO-MORE-X is end of set. Same prefix."""
    assert _classify(literal) == expected


def test_abbreviated_combined_relation_is_refused() -> None:
    body = (
        f"IF LR-STATUS = {QUOTE}VMBEFF-NOT-FND{QUOTE} "
        f"OR {QUOTE}LR-ERROR{QUOTE}"
    )
    rewritten, hits = LrfPathExpander._rewrite_lr_status(body)
    assert hits == 0
    assert rewritten == body

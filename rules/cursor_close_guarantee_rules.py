# FILE: rules/cursor_close_guarantee_rules.py
# ACTION: REPLACE ENTIRE FILE

"""Cursor close-guarantee rules.

Constants only. No regex, no runtime logic, no program / paragraph /
record / table / cursor / host variable names.

WHY THIS EXISTS
---------------
`CursorFlowComposer` handles two loop idioms (INLINE and SPAN). When a
program matches neither - as every LRF-expanded program did - it logged
`no_loop_for_cursor` as a WARNING and emitted:

    PERFORM 710-OPEN-<cursor>.
    PERFORM 720-FETCH-<cursor>.        <- primes once, never loops
    ...
    PERFORM 720-FETCH-<cursor>.        <- orphan repeat fetch

with `730-CLOSE-<cursor>` declared but never performed. The cursor is
opened, read twice and leaked. This pass is the last-resort guarantee
that produces the manual reference shape:

    PERFORM 710-OPEN-<cursor>.
    PERFORM 720-FETCH-<cursor> UNTIL <cursor>-EOC.
    PERFORM 730-CLOSE-<cursor>.

and drives the business paragraph from the FETCH paragraph:

    EVALUATE SQLCODE
      WHEN ZERO
           PERFORM <business> THRU <business>-EXIT

CORRECTION A - end-of-cursor vocabulary had two owners
------------------------------------------------------
EOC_CONDITION_TEMPLATE and LEGACY_EOC_CONDITIONS were IMPORTED from
rules.cursor_eoc_rules and then REDEFINED below, so the import was dead
and silently shadowed - and the two definitions had DIFFERENT contents
(the local one knew the '+100' forms, the shared one did not). The
`# noqa: F401` on the import suppressed the one lint that would have
reported it. rules/cursor_eoc_rules.py is now the single owner; the
'+100' forms were moved there and these names are re-exported from here
so existing importers keep working.

CORRECTION B - EOC_CONDITION_SUFFIX was exported but never defined
-------------------------------------------------------------------
__all__ advertised the name while the module body did not define it.
Any importer written against the published surface got ImportError.
It is now re-exported from its owner.

CORRECTION C - the message catalogue was built by post-hoc assignment
----------------------------------------------------------------------
Four `CURSOR_CLOSE_GUARANTEE_MESSAGES[key] = ...` blocks followed the
dictionary literal, and one key (business_paragraph_unverified) was
assigned TWICE - the second silently shadowing the first. Subscript
assignment is invisible to tests/test_rules_no_duplicate_constants.py.
Per the rule stated in rules/cursor_declaration_messages.py, the
catalogue is now ONE dictionary literal. A duplicate key inside a
literal is reviewable; a duplicate subscript assignment is not.

CORRECTION D - already_driven_by_span
---------------------------------------
New key. FetchBusinessBinder refuses to bind the WHEN ZERO branch when
an EXTERNAL loop already drives the business paragraph to this cursor's
end-of-cursor condition. Without this key the refusal would be silent,
and a silent pass cannot be reviewed.
"""

from __future__ import annotations

from rules.cursor_eoc_rules import (
    EOC_CONDITION_SUFFIX,
    EOC_CONDITION_TEMPLATE,
    LEGACY_EOC_CONDITIONS,
)

#
# Master switches
#
ENFORCE_CURSOR_CLOSE_GUARANTEE = True

# Convert a primed-but-unlooped fetch into PERFORM <fetch> UNTIL <eoc>.
SYNTHESISE_MISSING_DRIVING_LOOP = True

# Rewrite the FETCH paragraph WHEN ZERO branch to drive the business
# paragraph that used to carry the OBTAIN NEXT.
ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH = True

# Refuse to bind WHEN ZERO when an external loop already drives the
# business paragraph on this cursor's end-of-cursor condition. Binding
# both ends creates a mutual PERFORM that compiles clean and hangs.
REFUSE_BIND_WHEN_EXTERNALLY_DRIVEN = True

# Emit PERFORM <para> THRU <para>-EXIT when the exit paragraph exists.
PREFER_THRU_EXIT_PARAGRAPH = True

#
# Cursor paragraph operations
#
OPERATION_OPEN = "OPEN"
OPERATION_FETCH = "FETCH"
OPERATION_CLOSE = "CLOSE"
REQUIRED_OPERATIONS = (OPERATION_OPEN, OPERATION_FETCH, OPERATION_CLOSE)

#
# Generated statements
#
PERFORM_FETCH_UNTIL_TEMPLATE = "PERFORM {fetch} UNTIL {condition}."
PERFORM_CLOSE_TEMPLATE = "PERFORM {close}."
PERFORM_BUSINESS_TEMPLATE = "PERFORM {paragraph}"
PERFORM_BUSINESS_THRU_TEMPLATE = "PERFORM {paragraph} THRU {through}"
UNTIL_TEMPLATE = "UNTIL {condition}"

EXIT_PARAGRAPH_SUFFIX = "-EXIT"
STATEMENT_TERMINATOR = "."

# How far ahead of a PERFORM the UNTIL clause may sit on its own line.
#
# NOTE: rules/cursor_flow_rules.py declares its own UNTIL_LOOKAHEAD_LIMIT
# of 10 for a different question (correlating an OPEN with its FETCH).
# These are deliberately separate measurements; do not merge them without
# deciding which one each caller means.
UNTIL_LOOKAHEAD_LIMIT = 3

# Single word lines ending in a period that are NOT paragraph headers.
NON_PARAGRAPH_SINGLE_WORDS = frozenset({
    "CONTINUE",
    "END-EXEC",
    "END-EVALUATE",
    "END-IF",
    "END-PERFORM",
    "END-READ",
    "END-SEARCH",
    "END-STRING",
    "END-WRITE",
    "EXIT",
    "GOBACK",
    "STOP",
})

#
# Diagnostics - ONE literal. No post-hoc subscript assignment.
#
CURSOR_CLOSE_GUARANTEE_MESSAGES = {
    "loop_synthesised": (
        "Cursor close guarantee: cursor {cursor} had no driving loop; "
        "emitted PERFORM {fetch} UNTIL {condition} and PERFORM {close}."
    ),
    "condition_rewritten": (
        "Cursor close guarantee: rewrote the {cursor} loop exit condition "
        "to {condition}."
    ),
    "close_inserted": (
        "Cursor close guarantee: inserted PERFORM {close} after the "
        "{cursor} driving loop."
    ),
    "close_present": (
        "Cursor close guarantee: {close} is already performed; no "
        "insertion needed."
    ),
    "business_paragraph_bound": (
        "Cursor close guarantee: FETCH paragraph {fetch} now performs "
        "business paragraph {paragraph}."
    ),
    "business_paragraph_already_bound": (
        "Cursor close guarantee: {fetch} already performs {paragraph}; no "
        "change needed."
    ),
    "business_paragraph_unknown": (
        "Cursor close guarantee: could not identify the business "
        "paragraph for cursor {cursor}; WHEN ZERO left unchanged."
    ),
    "business_paragraph_unverified": (
        "Cursor close guarantee: candidate business paragraph {paragraph} "
        "for cursor {cursor} references neither its DCLGEN group nor a "
        "nested cursor; binding refused."
    ),
    "already_driven_by_span": (
        "Cursor close guarantee: business paragraph {paragraph} is "
        "already driven by an external SPAN loop on cursor {cursor}; "
        "the WHEN ZERO branch was left unchanged."
    ),
    "repeat_fetch_removed": (
        "Cursor close guarantee: removed the orphan repeat PERFORM "
        "{fetch} left by the converted OBTAIN NEXT."
    ),
    "when_zero_not_bindable": (
        "Cursor close guarantee: the WHEN ZERO branch of {fetch} holds no "
        "CONTINUE to replace; left unchanged."
    ),
    "no_open_perform": (
        "Cursor close guarantee: cursor {cursor} has OPEN/FETCH/CLOSE "
        "paragraphs but is never opened; left untouched for review."
    ),
    "no_driving_loop": (
        "Cursor close guarantee: cursor {cursor} has no driving loop and "
        "synthesis is disabled; left untouched for review."
    ),
    "incomplete_paragraph_set": (
        "Cursor close guarantee: cursor {cursor} does not have a complete "
        "OPEN/FETCH/CLOSE paragraph set; skipped."
    ),
    "bind_missing_argument": (
        "Cursor close guarantee: cannot bind - fetch paragraph {fetch}, "
        "business paragraph {paragraph}."
    ),
    "fetch_paragraph_not_found": (
        "Cursor close guarantee: FETCH paragraph {fetch} was not found in "
        "the program; WHEN ZERO left unchanged."
    ),
}

__all__ = [
    "ENFORCE_CURSOR_CLOSE_GUARANTEE",
    "SYNTHESISE_MISSING_DRIVING_LOOP",
    "ENFORCE_FETCH_DRIVES_BUSINESS_PARAGRAPH",
    "REFUSE_BIND_WHEN_EXTERNALLY_DRIVEN",
    "PREFER_THRU_EXIT_PARAGRAPH",
    "OPERATION_OPEN",
    "OPERATION_FETCH",
    "OPERATION_CLOSE",
    "REQUIRED_OPERATIONS",
    "EOC_CONDITION_TEMPLATE",
    "EOC_CONDITION_SUFFIX",
    "LEGACY_EOC_CONDITIONS",
    "PERFORM_FETCH_UNTIL_TEMPLATE",
    "PERFORM_CLOSE_TEMPLATE",
    "PERFORM_BUSINESS_TEMPLATE",
    "PERFORM_BUSINESS_THRU_TEMPLATE",
    "UNTIL_TEMPLATE",
    "EXIT_PARAGRAPH_SUFFIX",
    "STATEMENT_TERMINATOR",
    "UNTIL_LOOKAHEAD_LIMIT",
    "NON_PARAGRAPH_SINGLE_WORDS",
    "CURSOR_CLOSE_GUARANTEE_MESSAGES",
]
# LOCATION: rules/cursor_loop_rules.py
# ACTION: REPLACE ENTIRE FILE
"""Cursor driving-loop rules.

Constants only. No regex, no runtime logic, no program / paragraph /
record / table / cursor / host variable names.

WHY THIS EXISTS
---------------
rules/cursor_flow_rules.py describes ONE loop idiom:

    PERFORM 710-OPEN-<cursor>.
    PERFORM 720-FETCH-<cursor>.
    PERFORM <business>
        UNTIL SQLCODE = 100.

Older programs - and every LRF program, which predates that convention -
drive the loop with a paragraph span:

    PERFORM <business> THRU <business>-EXIT
        UNTIL LR-STATUS = 'VMBFAS-EOA'.

with the OPEN and the priming FETCH in a DIFFERENT paragraph, which may
appear BEFORE or AFTER the loop in source order.

Restructuring a span loop would rewrite working business flow, which the
business-flow rule forbids. The SPAN strategy is therefore deliberately
conservative: it fixes the exit condition and guarantees the cursor is
closed, and changes nothing else.

CORRECTION 16-10 - THE EOC VOCABULARY WAS IMPORTED AND THEN RE-ASSIGNED
-----------------------------------------------------------------------
This module imported EOC_CONDITION_SUFFIX, EOC_CONDITION_TEMPLATE and
LEGACY_EOC_CONDITIONS from rules/cursor_eoc_rules.py - and then assigned
all three again further down. Python keeps the LAST assignment, so the
import was dead and the local copies were live.

TWO of the three local copies were byte-identical to the owner, which is
precisely what hid the third. The import looked inert because two thirds
of it genuinely were.

converter/composers/cursor_flow/loop_shape.py imports
LEGACY_EOC_CONDITIONS from HERE, so the loop classifier read the stale
local tuple. Adding a condition to the OWNER changed nothing, and the
symptom was silence: the classifier simply did not recognise the idiom
and no message said why.

Worse, tests/test_eoc_vocabulary_agrees_across_the_review_boundary.py
imports the OWNER. It certified an agreement between the reviewer and a
tuple the converter never read.

Same defect, same resolution, as the QUERYNO correction in
rules/db2_infrastructure_rules.py and the duplicate warning block it
documents.

NO CONSTANT IMPORTED ABOVE MAY BE ASSIGNED IN THIS FILE.
"""

from __future__ import annotations

# =====================================================================
# EOC vocabulary - OWNED by rules/cursor_eoc_rules.py
# =====================================================================
# RE-EXPORT ONLY. converter/composers/cursor_flow/loop_shape.py imports
# these names from this module, so the re-export is the reason the
# import exists. Assigning any of them below would shadow the owner and
# restore the defect described in the module docstring.
from rules.cursor_eoc_rules import (  # noqa: F401
    EOC_CONDITION_SUFFIX,
    EOC_CONDITION_TEMPLATE,
    LEGACY_EOC_CONDITIONS,
)

# ---------------------------------------------------------------- master
ENFORCE_SPAN_LOOP_REWRITE = True

# A leftover OBTAIN NEXT may only be stripped when the loop it belonged to
# was ACTUALLY converted. Stripping it without a plan deletes the only
# FETCH inside the loop and the program never advances.
REQUIRE_PLAN_FOR_OBTAIN_NEXT_CLEANUP = True

# ----------------------------------------------------------- loop kinds
LOOP_KIND_INLINE = "INLINE"   # PERFORM <para> [UNTIL ...]
LOOP_KIND_SPAN = "SPAN"       # PERFORM <para> THRU <para> [UNTIL ...]

# --------------------------------------------------------- correlation
# Whole program is searched in BOTH directions. A span loop legitimately
# precedes the paragraph that opens the cursor.
SEARCH_BOTH_DIRECTIONS = True

# 0 disables the distance ceiling. A ceiling only hides correlation bugs.
MAX_CORRELATION_DISTANCE = 0

# Window used when checking whether a CLOSE is already performed.
CLOSE_PRESENCE_WINDOW = 40

# ---------------------------------------------------------- statements
UNTIL_TEMPLATE = "UNTIL {condition}"
UNTIL_TERMINATED_TEMPLATE = "UNTIL {condition}."
PERFORM_CLOSE_TEMPLATE = "PERFORM {paragraph}."

STATEMENT_TERMINATOR = "."

# ---------------------------------------------------------- diagnostics
# SPAN-ONLY BY DESIGN.
#
# CursorFlowComposer runs two strategies. Strategy 1 (INLINE) uses the
# older plan discoverer keyed on rules/cursor_flow_rules.py and reports
# through that module. Strategy 2 (SPAN) uses LoopShapeScanner and
# reports through the catalogue below.
#
# "scanned" counts BOTH kinds because LoopShapeScanner sees both, but no
# message here describes an inline conversion - because this package
# never performs one. An inline loop that the older discoverer does not
# recognise is counted here and acted on by nobody, and the only trace
# is "obtain_next_retained". That gap is tracked as #D2.
CURSOR_LOOP_MESSAGES = {
    "scanned": (
        "Cursor flow: found {inline} inline loop(s) and {span} span loop(s)."
    ),
    "span_plan": (
        "Cursor flow: correlated cursor {cursor} with span loop "
        "PERFORM {paragraph} THRU {through}."
    ),
    "condition_rewritten": (
        "Cursor flow: rewrote span loop exit condition to {condition}."
    ),
    "close_inserted": (
        "Cursor flow: inserted {paragraph} after the span loop."
    ),
    "close_present": (
        "Cursor flow: {paragraph} already performed; no insertion needed."
    ),
    "no_loop_for_cursor": (
        "Cursor flow: cursor {cursor} has no recognised driving loop; "
        "the generated OBTAIN NEXT was left in place for manual review."
    ),
    "obtain_next_retained": (
        "Cursor flow: no cursor loop was converted, so generated fetch "
        "calls were retained."
    ),
}

# =====================================================================
# END OF FILE
# =====================================================================
# NO CONSTANT MAY BE ADDED BELOW THIS LINE, and in particular none of
# the three names imported at the top. An append lands here, and an
# append is exactly what produced the shadowed EOC vocabulary that this
# file just had removed.
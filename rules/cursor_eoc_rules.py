# LOCATION: rules/cursor_eoc_rules.py
# ACTION: CREATE NEW FILE
"""The end-of-cursor vocabulary. ONE definition.

Constants only.

LEGACY_EOC_CONDITIONS was declared three times with three different
contents:

    rules/cursor_close_guarantee_rules.py   6 entries, with +100 forms
    rules/cursor_loop_rules.py              4 entries, +100 forms absent
    review/standards/cobol_standards.py     2 entries, WHOLE STATEMENTS

so whether "UNTIL SQLCODE = +100" counted as a legacy exit test depended
on which sibling a composer imported. cursor_flow/loop_shape.py could
not see it; cursor_close_guarantee/line_utils.py could.

The review copy was a different CONCEPT sharing the name, and is now
review.standards.cobol_standards.LEGACY_EOC_LOOP_STATEMENTS. review
must never import from the converter, so it keeps its own copy - but it
must carry the same vocabulary in statement form.

This tuple is a SUPERSET. Adding a spelling is safe. Removing one
silently stops rewriting a loop.
"""

from __future__ import annotations

LEGACY_EOC_CONDITIONS = (
    "SQLCODE = 100",
    "SQLCODE=100",
    "DB-END-OF-SET",
    "DB-REC-NOT-FOUND",
    "ERROR-STATUS",
)

EOC_CONDITION_TEMPLATE = "{cursor}-EOC"
EOC_CONDITION_SUFFIX = "-EOC"

__all__ = [
    "EOC_CONDITION_SUFFIX",
    "EOC_CONDITION_TEMPLATE",
    "LEGACY_EOC_CONDITIONS",
]
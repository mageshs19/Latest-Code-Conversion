# LOCATION: rules/unnecessary_comments_rules.py
# ACTION: CREATE NEW FILE
"""Generated comment cleanup policy.

Constants only. No regex, no runtime logic, no program / record / table
/ cursor / host variable names. The patterns live in
patterns/cobol_patterns.py.
"""

from __future__ import annotations

# A removal the operator does not need told about in the delivered
# source: "COMMIT removed", "Removed residual IDMS ...". The conversion
# log already records it.
REMOVE_NOISE_MARKERS = True

# A conversion breadcrumb: "Converted OBTAIN FIRST ...". Useful while
# reviewing a conversion, noise in a delivered program. Set False to
# keep the breadcrumbs during a review cycle.
REMOVE_TRACE_MARKERS = True

# DB2-KEEP flags a business line a human must review. Never removed.
MARKER_CLEANUP_MESSAGE = "Removed {count} generated DB2 marker comment(s)."

__all__ = [
    "REMOVE_NOISE_MARKERS",
    "REMOVE_TRACE_MARKERS",
    "MARKER_CLEANUP_MESSAGE",
]
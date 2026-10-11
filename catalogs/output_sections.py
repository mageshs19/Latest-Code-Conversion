# LOCATION: catalogs/output_sections.py
# ACTION: REPLACE ENTIRE FILE

"""Output section titles and generated block markers.

Generators and composers must import section labels from this catalog
instead of hardcoding generated block titles inside logic classes.

Constants only. No regex, no runtime logic, no program / record / table /
cursor / host variable names.

CORRECTION - two markers were declared outside the marker block
----------------------------------------------------------------
DB2_GENERATED_WORKING_STORAGE_MARKER was appended in the middle of the
MARKER_SHORT_FORMS region, and the same literal ALSO existed in
rules/structural_safety_rules.py. One string, two owners, one edit away
from drifting - and because the rules copy carried no comment
indicator, the banner reached the output as

    000870     DB2 GENERATED WORKING STORAGE
    000880 01  WS-DB2-GENERATED.

which is not a data description and will not compile.

Both generated-group titles now live here, beside every other marker.
rules/structural_safety_rules.py imports them and wraps them with
COMMENT_MARKER_TEMPLATE, so the indicator can no longer be forgotten.
"""

from __future__ import annotations

# =====================================================================
# Generated block markers
# =====================================================================
DB2_INFRASTRUCTURE_MARKER = (
    "DB2 SQLCA, SQL ERROR WORKING STORAGE, DCLGEN INCLUDES, AND CURSOR FLAGS"
)

DB2_SQL_ERROR_LOCATION_MARKER = "DB2 SQL ERROR LOCATION"

DB2_CURSOR_FLAGS_MARKER = "DB2 CURSOR END-OF-CURSOR FLAGS"
DB2_CURSOR_DECLARATIONS_MARKER = "DB2 CURSOR DECLARATIONS"
DB2_CURSOR_PARAGRAPH_MARKER = (
    "DB2 GENERATED CURSOR OPEN FETCH CLOSE PARAGRAPHS"
)

DB2_GENERATED_TIMESTAMP_MARKER = (
    "DB2 GENERATED TIMESTAMP AND AUDIT WORKING STORAGE"
)

# The work group the structural-safety pass creates for generated
# working-storage fields, and the group the counter pass creates.
# Consumed by rules/structural_safety_rules.py.
DB2_GENERATED_WORKING_STORAGE_MARKER = "DB2 GENERATED WORKING STORAGE"
DB2_GENERATED_ROW_COUNTERS_MARKER = "DB2 GENERATED ROW COUNTERS"

# =====================================================================
# Marker comment geometry
# =====================================================================
# A marker comment must fit the 65-column body window (cols 8-72).
# DB2_INFRASTRUCTURE_MARKER is 70 characters, so the old
# "*{title:<62}*" template overflowed and wrapped onto a second line:
#
#     *DB2 SQLCA, SQL ERROR WORKING STORAGE, DCLGEN INCLUDES, AND CURSOR
#     *FLAGS*
#
# The template no longer pads to a fixed trailing star, and long titles
# are truncated at the body width by the emitting helper rather than
# wrapping into a broken second comment line.
#
# The leading '*' is the COLUMN 7 INDICATOR. Every marker must be
# rendered through this template; a bare title written straight into
# WORKING-STORAGE is a compile error.
COMMENT_BODY_WIDTH = 65
COMMENT_MARKER_TEMPLATE = "*{title}"
COMMENT_RULE_LINE = "*" + "-" * (COMMENT_BODY_WIDTH - 2) + "*"

# Short form used when the full marker will not fit.
DB2_INFRASTRUCTURE_MARKER_SHORT = "DB2 INFRASTRUCTURE - SQLCA, INCLUDES, FLAGS"

COMMENT_TITLE_WIDTH = COMMENT_BODY_WIDTH - 2

# Long marker -> short marker. Keyed on the long form so a caller never
# has to know a fallback exists.
MARKER_SHORT_FORMS = {
    DB2_INFRASTRUCTURE_MARKER: DB2_INFRASTRUCTURE_MARKER_SHORT,
}

# Last resort when even the short form does not fit. Truncation is
# visible and deliberate; a wrapped banner is neither.
MARKER_TRUNCATION_SUFFIX = "..."

MARKER_MESSAGES = {
    "short_form_used": (
        "DB2 infrastructure: marker {length} characters exceeds the "
        "{width}-column banner window; used the short form."
    ),
    "truncated": (
        "DB2 infrastructure: marker {length} characters exceeds the "
        "{width}-column banner window and has no short form; truncated."
    ),
}

# =====================================================================
# Infrastructure include names
# =====================================================================
SQLERRWS_INCLUDE_NAME = "SQLERRWS"
SQLCA_INCLUDE_NAME = "SQLCA"
SQLERROR_INCLUDE_NAME = "SQLERROR"

# Includes that are DB2 infrastructure, never DCLGEN table includes.
INFRASTRUCTURE_INCLUDE_NAMES = frozenset(
    {
        SQLCA_INCLUDE_NAME,
        SQLERRWS_INCLUDE_NAME,
        SQLERROR_INCLUDE_NAME,
        "GEN",
    }
)

# Manual reference emits a single-line include, not a three-line block.
INCLUDE_SINGLE_LINE = True
INCLUDE_STATEMENT_TEMPLATE = "EXEC SQL INCLUDE {name} END-EXEC."

# =====================================================================
# SQL-LOCATION
# =====================================================================
SQL_LOCATION_FIELD_NAME = "SQL-LOCATION"
SQL_LOCATION_PICTURE = "PIC X(40) VALUE SPACES."

# --- SQL-LOCATION ownership -------------------------------------------
# SQLERRWS declares SQL-LOCATION. The converter must NOT declare it
# again: a duplicate data-name is a compile error, and the COBOL team's
# manual reference program carries no local 01 SQL-LOCATION entry.
#
# Consumed by:
#   converter/generators/db2_infrastructure/
#       infrastructure_block_builder.py
DECLARE_SQL_LOCATION_FIELD = False

# =====================================================================
# DCLGEN
# =====================================================================
DCLGEN_GROUP_PREFIX = "DCL"
DCLGEN_INITIALIZE_TEMPLATE = "INITIALIZE {group}"
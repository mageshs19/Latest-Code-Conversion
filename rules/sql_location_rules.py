# LOCATION: rules/sql_location_rules.py
# ACTION: REPLACE ENTIRE FILE

"""Single owner of the MOVE ... TO SQL-LOCATION vocabulary.

CORRECTION - the templates were scoped to cursors, so the update path
             re-implemented them
--------------------------------------------------------------------
SQL_LOCATION_* lived in rules/cursor_paragraph_rules.py. An update-path
module cannot reasonably import "cursor_paragraph" rules to render a
non-cursor MOVE, so three emitters appeared instead of one:

    converter/generators/cursor_paragraph/cursor_sql_location.py
        correct - honours SQL_LOCATION_USES_PARAGRAPH_NUMBER

    converter/composers/update_sql_cleanup/modify_update_rewriter.py:95
    converter/generators/sql/sql_statement_builder.py:113, :177
        inline f-strings, hardcoding the COBOL field name inside a
        logic layer, and passing the RECORD name where a paragraph
        identity belongs:

            MOVE 'UPDATE-VMBFAR' TO SQL-LOCATION.

Every site occurrence is a NUMBER, and the number is the paragraph's own
prefix:

    VMDZ1567 (manual reference)   MOVE 1100 TO SQL-LOCATION
    VMDZ4302                      MOVE 700 / 710 / 720 TO SQL-LOCATION

The field is therefore almost certainly numeric. It cannot be proven
here: SQLERRWS is absent from mainframe/workspace, so no declaration is
available to read.

WHY THE NAME FALLBACK SURVIVES THIS EDIT
    Twenty tests reference SQL-LOCATION. None reference
    SQL_LOCATION_NAME_TEMPLATE, but a test asserting generated TEXT
    would still break. EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER is
    therefore True here - current behaviour, byte for byte. Flipping it
    to False is a SECOND change, made only after those twenty tests have
    been read, exactly as EMIT_SQL_LOCATION in restart_standard_rules.py
    taught.

CORRECTION 2 - the legacy label had to survive the unification
--------------------------------------------------------------
The update emitters build their location from the RECORD, not a
paragraph. Deleting that outright would have changed generated text in
the same commit that unified ownership, making any test failure
impossible to attribute. LEGACY_RECORD_LOCATION_TEMPLATE keeps the old
label as the FALLBACK identity, so the unification is provably inert and
the numeric form switches on by itself once a numbered paragraph is
supplied.
"""

from __future__ import annotations

# The COBOL field. Declared by the SQLERRWS copybook, never by us.
SQL_LOCATION_FIELD = "SQL-LOCATION"

# The site contract: move the paragraph's numeric prefix.
SQL_LOCATION_USES_PARAGRAPH_NUMBER = True

# Column alignment between the number and TO, as the manual reference
# writes it: "MOVE 700    TO SQL-LOCATION".
SQL_LOCATION_NUMBER_PAD = "    "

SQL_LOCATION_NUMBER_TEMPLATE = "MOVE {number}{pad}TO {field}"
SQL_LOCATION_NAME_TEMPLATE = "MOVE '{name}' TO {field}"

# A paragraph label is NUMBER-WORDS, e.g. 1100-UPDATE-VMBFAR.
PARAGRAPH_NUMBER_SEPARATOR = "-"

# False = refuse to emit rather than write an unproven alphanumeric
# literal into a field whose site usage is numeric. NOT yet flipped.
EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER = True

# The pre-unification label the update emitters built from the record.
# Used ONLY when no paragraph identity is available. See CORRECTION 2.
LEGACY_RECORD_LOCATION_TEMPLATE = "{operation}-{record}"
LEGACY_OPERATION_UPDATE = "UPDATE"
LEGACY_OPERATION_INSERT = "INSERT"
LEGACY_OPERATION_DELETE = "DELETE"

__all__ = [
    "EMIT_SQL_LOCATION_WITHOUT_PARAGRAPH_NUMBER",
    "LEGACY_OPERATION_INSERT",
    "LEGACY_OPERATION_UPDATE",
    "LEGACY_RECORD_LOCATION_TEMPLATE",
    "PARAGRAPH_NUMBER_SEPARATOR",
    "SQL_LOCATION_FIELD",
    "SQL_LOCATION_NAME_TEMPLATE",
    "SQL_LOCATION_NUMBER_PAD",
    "SQL_LOCATION_NUMBER_TEMPLATE",
    "SQL_LOCATION_USES_PARAGRAPH_NUMBER",
]
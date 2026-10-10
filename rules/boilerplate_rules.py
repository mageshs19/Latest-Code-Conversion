# LOCATION: rules/boilerplate_rules.py
# ACTION: CREATE NEW FILE

"""Configuration for COBOL boilerplate generator."""

# DCLGEN and infrastructure includes to add after WORKING-STORAGE
BOILERPLATE_DCLGEN_INCLUDES = [
    "SQLERRWS",
    "SQLCA",
]

# Indent for EXEC SQL INCLUDE statements (must align with COBOL Area B)
BOILERPLATE_INCLUDE_INDENT = "    "

# END PROGRAM statement (aligned to Area B)
BOILERPLATE_END_PROGRAM = "END PROGRAM."

# Messages
BOILERPLATE_MESSAGES = {
    "includes_added": "Boilerplate: DCLGEN includes added ({count} lines)",
    "includes_exist": "Boilerplate: DCLGEN includes already present; skipped",
    "end_program_added": "Boilerplate: END PROGRAM statement added",
    "end_program_exists": "Boilerplate: END PROGRAM statement already exists; skipped",
    "no_working_storage": "Boilerplate: WORKING-STORAGE SECTION not found; includes not added",
    "no_procedure_division": "Boilerplate: PROCEDURE DIVISION not found; includes not added",
}

__all__ = [
    "BOILERPLATE_DCLGEN_INCLUDES",
    "BOILERPLATE_INCLUDE_INDENT",
    "BOILERPLATE_END_PROGRAM",
    "BOILERPLATE_MESSAGES",
]

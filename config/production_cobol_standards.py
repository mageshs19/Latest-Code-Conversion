"""
PRODUCTION COBOL STANDARDS CONFIGURATION

This configuration file defines how the converter generates production-ready
COBOL code that meets all standards for Issues 1-5 and Changes 1-2.

This file is used by the converter pipeline to ensure all generated code:
1. Has centralized initialization (100-INITIALIZE)
2. Has organized WORKING-STORAGE in 10 sections
3. Has structured PROCEDURE DIVISION with standard flow
4. Has proper audit trail (timestamps, counters)
5. Has no hardcoded values
6. Follows COBOL standards

ACTIVATION: Enable this in the conversion pipeline:
  from config.production_cobol_standards import PRODUCTION_STANDARDS
  pipeline.apply_standards(PRODUCTION_STANDARDS)

FILE LOCATION: config/production_cobol_standards.py
"""

# ============================================================================
# INITIALIZATION STANDARDS
# ============================================================================

INITIALIZATION_CONFIG = {
    # Centralize all INITIALIZE statements to 100-INITIALIZE
    "centralize_initialization": True,
    
    # Ensure INITIALIZE runs only once, at startup
    "initialize_once_only": True,
    
    # Remove INITIALIZE from fetch loops
    "remove_initialize_from_loops": True,
    
    # Remove standalone INITIALIZE blocks
    "remove_standalone_blocks": True,
    
    # Create 100-INITIALIZE if it doesn't exist
    "create_100_initialize": True,
    
    # Include program constant initialization
    "initialize_program_constant": True,
    
    # Call timestamp function in initialization
    "call_timestamp_in_init": True,
}

# ============================================================================
# WORKING-STORAGE STANDARDS
# ============================================================================

WORKING_STORAGE_CONFIG = {
    # Organize declarations into 10 standard sections
    "organize_into_sections": True,
    
    # Add section separators for clarity
    "add_section_separators": True,
    
    # Standard section order
    "section_order": [
        "CONTROL-FIELDS",
        "COUNTER-FIELDS",
        "TIMESTAMP-FIELDS",
        "DATUMVELDEN",
        "DATE-CONVERSION-HELPERS",
        "STATUS-FLAGS",
        "WORK-FIELDS",
        "PARAMETER-DATA",
        "IMPORTED-SECTIONS",
        "DCLGEN-GROUPS",
    ],
    
    # Ensure these fields always exist
    "required_fields": {
        "CONTROL-FIELDS": ["CS-PROGRAM"],
        "COUNTER-FIELDS": ["WS-NB-OUTPUT-COUNT"],
        "TIMESTAMP-FIELDS": ["TS-SYSTEM", "TS-TIMESTAMP"],
        "DATUMVELDEN": ["DA-CCYYMMDD", "DA-DD-MM-CCYY"],
    },
    
    # Field alignment standards
    "field_alignment": {
        "CS-PROGRAM": {"chars": 28, "pic": "X(8)", "value": "DYNAMIC"},
        "counters": {"chars": 20, "pic": "9(7)", "comp3": True},
        "timestamps": {"chars": 20, "format": "CCYY-MM-DD-HH.MI.SS.TT"},
    },
}

# ============================================================================
# PROCEDURE DIVISION STANDARDS
# ============================================================================

PROCEDURE_DIVISION_CONFIG = {
    # Create standard paragraph flow
    "standard_flow": True,
    
    # Standard paragraph order
    "paragraph_order": [
        "100-INITIALIZE",
        "200-OPEN-CURSORS",
        "300-MAIN-PROCESSING",
        "400-CLOSE-CURSORS",
        "500-DISPLAY-TOTALS",
        "600-GET-TIMESTAMP",  # Generic
    ],
    
    # 100-INITIALIZE contents
    "initialize_paragraph": {
        "initialize_dclgen": True,
        "set_program_name": True,
        "get_timestamp": True,
        "order": ["DCLGEN_INIT", "PROGRAM_NAME", "TIMESTAMP"],
    },
    
    # 200-OPEN-CURSORS mapping
    "open_cursors_paragraph": {
        "collect_710_paragraphs": True,
        "auto_generate": True,
    },
    
    # 300-MAIN-PROCESSING mapping
    "main_processing_paragraph": {
        "collect_720_paragraphs": True,
        "auto_generate": True,
    },
    
    # 400-CLOSE-CURSORS mapping
    "close_cursors_paragraph": {
        "collect_730_paragraphs": True,
        "auto_generate": True,
    },
    
    # 500-DISPLAY-TOTALS contents
    "display_totals_paragraph": {
        "call_timestamp": True,
        "display_counters": True,
        "display_status": True,
    },
    
    # 600-GET-TIMESTAMP (generic, same in all programs)
    "timestamp_paragraph": {
        "generate_if_missing": True,
        "use_generic_template": True,
        "format": "CCYY-MM-DD-HH.MI.SS.TT",
    },
}

# ============================================================================
# COUNTER TRACKING STANDARDS
# ============================================================================

COUNTER_CONFIG = {
    # Generate counter fields
    "generate_counters": True,
    
    # Counter for each cursor
    "counter_per_cursor": True,
    
    # Counter for output records
    "output_record_counter": True,
    
    # Counter field properties
    "counter_properties": {
        "type": "PIC 9(7) COMP-3",
        "initial_value": "ZEROES",
        "alignment": 20,
    },
    
    # Where to increment counters
    "increment_locations": {
        "fetch_success": "After SQLCODE = 0 in fetch",
        "write_success": "After successful WRITE",
    },
    
    # Display counters
    "display_counters": True,
    "display_location": "500-DISPLAY-TOTALS",
}

# ============================================================================
# TIMESTAMP STANDARDS
# ============================================================================

TIMESTAMP_CONFIG = {
    # Generate timestamp fields
    "generate_fields": True,
    
    # Timestamp capture
    "capture_at_startup": True,
    "capture_at_end": True,
    
    # Timestamp field structure
    "ts_system": {
        "raw_current_date": True,
        "format": "CCYYDDMMHHMMSSTT",
    },
    
    "ts_timestamp": {
        "formatted": True,
        "format": "CCYY-MM-DD-HH.MI.SS.TT",
        "separators": ["-", "-", ".", ".", "."],
    },
    
    # Timestamp paragraph (600-GET-TIMESTAMP)
    "timestamp_paragraph": {
        "generic": True,  # Same in all programs
        "moves_per_field": 9,  # 9 MOVE statements
        "location": "After 500-DISPLAY-TOTALS",
    },
}

# ============================================================================
# SQL STANDARDS
# ============================================================================

SQL_CONFIG = {
    # Validate SQL organization
    "validate_sql": True,
    
    # DCLGEN includes
    "dclgen_includes": {
        "location": "After WORKING-STORAGE",
        "validate_presence": True,
        "format": "EXEC SQL INCLUDE {group} END-EXEC",
    },
    
    # SQLCA include
    "sqlca_include": {
        "required": True,
        "location": "After DCLGEN groups",
    },
    
    # SQL block formatting
    "sql_formatting": {
        "indent": 4,
        "one_statement_per_line": True,
        "validate_end_exec": True,
    },
}

# ============================================================================
# CODE QUALITY STANDARDS
# ============================================================================

CODE_QUALITY_CONFIG = {
    # No hardcoded program names
    "no_hardcoded_program_names": True,
    
    # No hardcoded group names
    "no_hardcoded_group_names": True,
    
    # Qualified field references
    "qualified_field_references": True,
    
    # Documentation comments
    "add_db2_comments": True,
    "comment_marker": "*DB2:",
    
    # Line numbers (COBOL fixed format)
    "line_numbers": "6-digit",
    
    # Indentation standards
    "indentation": {
        "procedure_division": 4,
        "statements": 4,
        "nested_blocks": 8,
    },
    
    # Section organization
    "section_separators": True,
    "separator_format": "*-------- {name} --------*",
}

# ============================================================================
# AUDIT TRAIL STANDARDS
# ============================================================================

AUDIT_TRAIL_CONFIG = {
    # Enable audit trail
    "enable_audit_trail": True,
    
    # Timestamp logging
    "log_start_time": True,
    "log_end_time": True,
    
    # Processing counters
    "track_processing": True,
    "counters": {
        "input_records": True,
        "output_records": True,
        "errors": False,  # Optional
    },
    
    # Display format
    "display_format": "COBOL DISPLAY statement",
    "log_location": "500-DISPLAY-TOTALS",
}

# ============================================================================
# VALIDATION RULES
# ============================================================================

VALIDATION_RULES = {
    # Mandatory checks (failures halt conversion)
    "mandatory_checks": [
        "100-INITIALIZE exists",
        "PROCEDURE DIVISION structured",
        "No INITIALIZE in fetch loops",
        "WORKING-STORAGE organized",
    ],
    
    # Warning checks (don't halt, but report)
    "warning_checks": [
        "CS-PROGRAM constant present",
        "Counters present for each cursor",
        "Timestamps captured",
        "600-GET-TIMESTAMP exists",
        "500-DISPLAY-TOTALS exists",
    ],
    
    # Enhancement checks (optional improvements)
    "enhancement_checks": [
        "Section separators present",
        "DB2 comments present",
        "Consistent formatting",
    ],
}

# ============================================================================
# MASTER CONFIGURATION OBJECT
# ============================================================================

PRODUCTION_STANDARDS = {
    "name": "Production COBOL Standards v1.0",
    "description": "Issues 1-5, Changes 1-2 - Production-Ready Code",
    "effective_date": "2026-10-08",
    
    "components": {
        "initialization": INITIALIZATION_CONFIG,
        "working_storage": WORKING_STORAGE_CONFIG,
        "procedure_division": PROCEDURE_DIVISION_CONFIG,
        "counters": COUNTER_CONFIG,
        "timestamps": TIMESTAMP_CONFIG,
        "sql": SQL_CONFIG,
        "code_quality": CODE_QUALITY_CONFIG,
        "audit_trail": AUDIT_TRAIL_CONFIG,
    },
    
    "validation": VALIDATION_RULES,
    
    # Enable/disable entire standards package
    "enabled": True,
    
    # Apply standards to all programs by default
    "apply_to_all_programs": True,
    
    # Program-specific overrides (if needed)
    "program_overrides": {},
    
    # Logging
    "logging": {
        "enabled": True,
        "level": "INFO",
        "log_each_step": True,
    },
}

# ============================================================================
# HOW TO USE THIS CONFIGURATION
# ============================================================================

"""
USAGE EXAMPLES:

1. Load and apply in converter:
    from config.production_cobol_standards import PRODUCTION_STANDARDS
    
    pipeline = ConversionPipeline()
    pipeline.apply_standards(PRODUCTION_STANDARDS)
    output = pipeline.convert(input_program)

2. Check specific configuration:
    from config.production_cobol_standards import PROCEDURE_DIVISION_CONFIG
    
    print(PROCEDURE_DIVISION_CONFIG["paragraph_order"])
    # Output: ['100-INITIALIZE', '200-OPEN-CURSORS', ...]

3. Access component configuration:
    from config.production_cobol_standards import PRODUCTION_STANDARDS
    
    init_config = PRODUCTION_STANDARDS["components"]["initialization"]
    if init_config["centralize_initialization"]:
        # Run initialization centralizer

4. Validate output against standards:
    from config.production_cobol_standards import VALIDATION_RULES
    
    issues = validate_program(output, VALIDATION_RULES["mandatory_checks"])
    if issues:
        raise ConversionError(f"Failed validation: {issues}")

SECTION DEPENDENCIES:

- initialization depends on: procedure_division
- working_storage depends on: counters, timestamps
- procedure_division depends on: initialization
- counters depend on: working_storage
- timestamps depend on: working_storage
- sql depends on: working_storage
- audit_trail depends on: counters, timestamps

RECOMMENDED EXECUTION ORDER:

1. Apply working_storage standards (organize sections)
2. Apply initialization standards (centralize to 100-INITIALIZE)
3. Apply counter standards (declare + increment)
4. Apply timestamp standards (declare + capture)
5. Apply procedure_division standards (structure flow)
6. Apply sql standards (validate organization)
7. Apply code_quality standards (formatting, comments)
8. Validate against validation_rules
9. Check audit_trail requirements

CUSTOMIZATION:

To modify standards for specific needs:
    custom_standards = PRODUCTION_STANDARDS.copy()
    custom_standards["components"]["counters"]["counter_per_cursor"] = False
    pipeline.apply_standards(custom_standards)

To disable specific standards:
    PRODUCTION_STANDARDS["enabled"] = False
    # Or specific components:
    PRODUCTION_STANDARDS["components"]["timestamps"]["enabled"] = False
"""

# ============================================================================
# VERSION AND HISTORY
# ============================================================================

VERSION = "1.0.0"
CREATED_DATE = "2026-10-08"
LAST_UPDATED = "2026-10-08"

STANDARDS_DOCUMENTS = [
    "rules/ISSUES_1_TO_5_MASTER_INDEX.py",
    "rules/db2_date_conversion_standards.py",
    "rules/field_mapping_standards.py",
    "rules/initialization_placement_rules.py",
    "rules/cobol_standard_initialization_rules.py",
    "rules/timestamp_conversion_standards.py",
    "rules/counter_rules.py",
    "rules/CONVERTER_IMPLEMENTATION_GUIDE.py",
    "rules/BEFORE_AFTER_COMPARISON.py",
    "manual_conventions/DEFERRED_DECISIONS.md",
]

GENERATOR_FILES = [
    "converter/generators/initialization_centralizer.py",
    "converter/generators/working_storage_organizer.py",
    "converter/generators/procedure_division_organizer.py",
    "converter/generators/converter_pipeline_integration.py",
    "config/production_cobol_standards.py",
]

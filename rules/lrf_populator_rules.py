# LOCATION: rules/lrf_populator_rules.py
# ACTION: REPLACE ENTIRE FILE
"""LRF host-variable populator rules, geometry and diagnostics.

Constants only. No regex, no parser logic, no service logic, and no
program / paragraph / record / table / DCLGEN / cursor / host-variable
names. Every name arrives as a format placeholder.

WHY THIS MODULE EXISTS

The populator reported a single opaque token, 'no_lrf_markers', for
eight different outcomes. A pass that cannot distinguish those cannot be
reviewed. Each outcome now has its own sentence.

GEOMETRY NOTE

A COBOL record is four fixed column ranges:

    1-6    left sequence
    7      indicator
    8-72   body        <- 65 columns, the only part generated here
    73-80  right sequence

LRF_BODY_WIDTH mirrors the site constant. If rules/fixed_format_rules.py
publishes BODY_WIDTH, import it here and delete the local copy - one
owner per constant. Locate it with:

    Select-String -Path rules\\*.py -Pattern 'BODY_WIDTH|BODY_LAST_COLUMN'
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Switches
# ---------------------------------------------------------------------

ENABLE_LRF_HOST_POPULATION = True

# A path that resolves WITHIN an AREA is an unqualified sweep: it has no
# parent record and no set. That is a RESOLVED path, not a failure.
ALLOW_AREA_SWEEP_PATHS = True

# Never invent a parent, a set, a host group or a key column.
REFUSE_ON_UNRESOLVED_PATH = True

# ---------------------------------------------------------------------
# Fixed-format geometry (columns 8-72)
# ---------------------------------------------------------------------

LRF_LEFT_SEQUENCE_WIDTH = 6
LRF_RIGHT_SEQUENCE_WIDTH = 8
LRF_BODY_WIDTH = 65
LRF_RECORD_WIDTH = (
    LRF_LEFT_SEQUENCE_WIDTH + 1 + LRF_BODY_WIDTH + LRF_RIGHT_SEQUENCE_WIDTH
)  # 80

LRF_COMMENT_INDICATOR = "*"
LRF_BLANK_INDICATOR = " "

# Area B for generated procedure statements: column 12.
LRF_STATEMENT_INDENT = " " * 4
LRF_COMMENT_INDENT = " " * 4

# A generated line that will not fit the body window is REFUSED and
# reported. Truncation produces an undefined data name; overflow pushes
# the right sequence out of columns 73-80.
ENFORCE_LRF_BODY_WIDTH = True

# ---------------------------------------------------------------------
# Defensive attribute probing
#
# The LRF domain model is owned by converter/domain/models.py. This pass
# READS it and must not break when a field is renamed, so candidate
# names are listed here rather than hardcoded in the generator.
# ---------------------------------------------------------------------

LRF_COMMAND_RECORD_ATTRIBUTES = (
    "record",
    "record_name",
    "target_record",
    "element_record",
)

LRF_COMMAND_WITHIN_ATTRIBUTES = (
    "within",
    "within_name",
    "set_name",
    "area_name",
    "container",
)

LRF_CURSOR_BY_RECORD_METHODS = (
    "cursor_name_for_record",
    "cursor_for_record",
)
LRF_TABLE_BY_RECORD_METHODS = (
    "table_for_record",
    "table_name_for_record",
    "resolve_table",
    "table_name",
)
LRF_CURSOR_BY_TABLE_METHODS = (
    "cursor_name_from_table",
    "cursor_for_table",
    "cursor_name",
)
LRF_HOST_GROUP_BY_TABLE_METHODS = (
    "group_for_table",
    "host_group_for_table",
)

LRF_PATH_COMMAND_ATTRIBUTES = ("commands", "path_commands", "steps")

# An IDMS area name is a site naming convention, not a COBOL rule. The
# classification is only a HINT: when it does not apply, the container is
# reported without claiming set or area, and no parent is assumed.
LRF_AREA_NAME_PREFIXES = ("AR-", "AR_")

# ---------------------------------------------------------------------
# Diagnostics - one key per outcome
# ---------------------------------------------------------------------

LRF_POPULATOR_MESSAGES = {
    "disabled": (
        "LRF populator: pass disabled by configuration; no host variable "
        "initialisation was generated."
    ),
    "empty_program": (
        "LRF populator: no program text supplied; nothing to populate."
    ),
    "no_markers": (
        "LRF populator: no LRF expansion marker found in the generated "
        "program; nothing to populate."
    ),
    "marker_unreadable": (
        "LRF populator: line {line} carries the text 'Expanded LRF' but "
        "does not match the shared marker format; left unchanged. The "
        "marker format or the shared pattern has drifted."
    ),
    "continuation_missing": (
        "LRF populator: wrapped LRF marker at line {line} has no "
        "continuation record on the following line; left unchanged."
    ),
    "no_lrf_repository": (
        "LRF populator: no LRF repository was supplied, so the parsed "
        "subschema cannot be consulted. Target records are taken from "
        "the marker; set and parent are unknown."
    ),
    "path_lookup_failed": (
        "LRF populator: the LRF repository rejected a lookup for path "
        "keyword {keyword} ({reason}); path treated as unresolved."
    ),
    "path_unresolved": (
        "LRF populator: path keyword {keyword} of logical record "
        "{record} is not in the parsed subschema; refused rather than "
        "guess."
    ),
    "path_fields_unknown": (
        "LRF populator: path keyword {keyword} was found but its "
        "navigation commands expose no readable record or container "
        "attribute; refused rather than guess."
    ),
    "area_sweep": (
        "LRF populator: path keyword {keyword} resolves to an "
        "unqualified sweep within area {area}; no parent record and no "
        "set."
    ),
    "set_resolved": (
        "LRF populator: path keyword {keyword} resolves to {record} "
        "within set {set_name}; parent record {parent}."
    ),
    "container_unclassified": (
        "LRF populator: path keyword {keyword} resolves to {record} "
        "within {container}, which is neither a known set nor a known "
        "area; no parent is assumed."
    ),
    "no_cursor_for_record": (
        "LRF populator: record {record} has no generated cursor; marker "
        "at line {line} left unchanged."
    ),
    "cursor_lookup_failed": (
        "LRF populator: the cursor lookup for record {record} failed "
        "({reason}); marker at line {line} left unchanged."
    ),
    "no_host_variable_resolver": (
        "LRF populator: no host variable resolver was supplied; no "
        "initialisation can be generated."
    ),
    "host_group_not_found": (
        "LRF populator: cursor {cursor} has no DCLGEN host group; no "
        "initialisation generated."
    ),
    "cursor_declare_not_found": (
        "LRF populator: no DECLARE statement was found for cursor "
        "{cursor}; its predicate cannot be read."
    ),
    "no_predicate": (
        "LRF populator: cursor {cursor} declares no WHERE clause, so it "
        "takes no parameter; nothing to load before OPEN."
    ),
    "parent_unknown": (
        "LRF populator: cursor {cursor} needs {count} key value(s) but "
        "its path has no parent record; refused rather than guess where "
        "the values come from."
    ),
    "perform_open_not_found": (
        "LRF populator: no PERFORM of the OPEN paragraph for cursor "
        "{cursor} was found after the marker; nothing injected."
    ),
    "geometry_refused": (
        "LRF populator: a generated line for cursor {cursor} is {width} "
        "columns and exceeds the {limit}-column body window; the whole "
        "block was refused rather than truncated ({body})."
    ),
    "injection_planned": (
        "LRF populator: cursor {cursor} will be initialised with "
        "{count} generated line(s) before its OPEN."
    ),
    "populated": (
        "LRF populator: cursor {cursor} initialised from host group "
        "{group} with {moves} move(s) before OPEN."
    ),
    "scan_summary": (
        "LRF populator: {examined} marker(s) examined, {bound} bound to "
        "a cursor, {refused} refused."
    ),
    "injection_summary": (
        "LRF populator: {cursors} cursor(s) received generated "
        "initialisation; {lines} line(s) inserted."
    ),
    "perform_open_before_marker": (
        "LRF populator: the OPEN of cursor {cursor} is performed at line "
        "{line}, ahead of the marker. Injecting there - the host group "
        "must be loaded before the cursor opens, not before the OBTAIN."
    ),
    "parent_not_declared": (
        "LRF populator: cursor {cursor} needs values from record "
        "{record}, but that record is not declared in the converted "
        "program; refused rather than emit a MOVE that cannot compile."
    ),
}


__all__ = [
    "ALLOW_AREA_SWEEP_PATHS",
    "ENABLE_LRF_HOST_POPULATION",
    "ENFORCE_LRF_BODY_WIDTH",
    "LRF_AREA_NAME_PREFIXES",
    "LRF_BLANK_INDICATOR",
    "LRF_BODY_WIDTH",
    "LRF_COMMAND_RECORD_ATTRIBUTES",
    "LRF_COMMAND_WITHIN_ATTRIBUTES",
    "LRF_COMMENT_INDENT",
    "LRF_COMMENT_INDICATOR",
    "LRF_LEFT_SEQUENCE_WIDTH",
    "LRF_PATH_COMMAND_ATTRIBUTES",
    "LRF_POPULATOR_MESSAGES",
    "LRF_RECORD_WIDTH",
    "LRF_RIGHT_SEQUENCE_WIDTH",
    "LRF_STATEMENT_INDENT",
    "REFUSE_ON_UNRESOLVED_PATH",
    "LRF_HOST_GROUP_BY_TABLE_METHODS"
]
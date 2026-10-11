# LOCATION: rules/legacy_restart_rules.py
# ACTION: REPLACE ENTIRE FILE

"""Stand-down policy for the LEGACY restart generator.

CONSTANTS ONLY. No regex, no logic, no program, paragraph, record,
table, DCLGEN or host variable name.

WHY THIS MODULE IS SO SMALL
---------------------------
An earlier draft of this file carried geometry, data-description
templates, SQL clause templates, SQLCODE routing and checkpoint policy.
Every one of those already exists and is tested:

    rules/restart_standard_rules.py      routing, scheme, thresholds
    rules/restart_sql_templates.py       SELECT / UPDATE / INSERT shape
    rules/restart_storage_templates.py   working-storage shape
    rules/restart_statement_templates.py statement shape
    catalogs/restart_paragraph_catalog.py paragraph names, QUERYNO

Re-declaring them here would have produced a THIRD restart generator.
Two was already one too many: the legacy generator emitted
700-RESTART-CONTROL performing 810-/820-, the metadata pass regenerated
those handlers as 710-/720-, and the output carried a PERFORM of a
paragraph that no longer existed.

This module therefore owns exactly one decision: WHEN the legacy
generator may run. The answer is "almost never".

NO CONSTANT MAY BE ASSIGNED TWICE IN THIS FILE.
"""

from __future__ import annotations

# =====================================================================
# Rule statements (documentation surface, asserted by the review engine)
# =====================================================================
LEGACY_RESTART_RULES = [
    "The metadata-driven restart pass is the only restart owner.",
    "The legacy generator authors no table, column, host or paragraph name.",
    "The legacy generator measures nothing; the resolver measures.",
    "The legacy generator stands down when a restart context exists.",
    "The legacy generator stands down for a retrieval program.",
    "The legacy generator stands down when its switch is off.",
    "Every stand-down is reported; a silent skip cannot be reviewed.",
    "A legacy residue found in the text is reported, never patched here.",
]

# =====================================================================
# Master switch
# =====================================================================
# OFF, and intended to stay off. The metadata-driven pass
# (restart_injection / RestartStageAdapter) resolves every name from
# Sheet Mapping, the DCLGEN role and the converted source, and measures
# the checkpoint payload from the restart record layout.
#
# Turning this on reinstates a generator that:
#   * hardcoded the restart table, host record and six column names,
#   * seeded a fresh run's record COUNT with the payload LENGTH,
#   * referenced two working-storage fields it never declared,
#   * declared a second EOF switch over the source's own,
#   * spliced blocks by character offset, dragging the next line's
#     sequence number into the body,
#   * and performed handlers under a numbering scheme the owner pass
#     regenerates under different names.
#
# None of that is repaired by this module. The switch exists so the
# behaviour can be reproduced deliberately for a regression baseline,
# not so it can be used.
ENABLE_LEGACY_RESTART_GENERATOR = False

# Report legacy restart residue found in the incoming text. Detection
# only - removal belongs to LegacyRestartCleanup (M9a).
REPORT_LEGACY_RESIDUE = True

# =====================================================================
# Stand-down reasons
# =====================================================================
STAND_DOWN_REASONS = {
    "switch_off": (
        "ENABLE_LEGACY_RESTART_GENERATOR is off; the metadata-driven "
        "pass owns restart control"
    ),
    "context_present": (
        "a restart context exists; the metadata-driven pass owns "
        "restart control"
    ),
    "retrieval": "the program is not an update program",
    "owner_paragraph_present": (
        "the owner pass has already injected {paragraph}"
    ),
    "empty_source": "the source is empty",
}

# =====================================================================
# Residue detection
# =====================================================================
# The eight-series handler names the legacy generator used. Their
# presence WITHOUT a matching definition is the dangling-PERFORM defect.
# Detection only; this tuple is never a removal list.
LEGACY_HANDLER_NUMBER_PREFIXES = ("810-", "820-")

# A PERFORM whose target is absent is a compile error, so it is worth a
# distinct message from "residue found".
REPORT_DANGLING_PERFORM = True

# =====================================================================
# Diagnostics - ONE dictionary literal
# =====================================================================
LEGACY_RESTART_MESSAGES = {
    "stood_down": "Legacy restart: stood down because {reason}.",
    "residue_found": (
        "Legacy restart: {count} legacy restart line(s) found in the "
        "text; LegacyRestartCleanup owns their removal."
    ),
    "dangling_perform": (
        "Legacy restart: PERFORM {paragraph} has no matching paragraph "
        "definition; this will not compile. It is residue of the "
        "eight-series handler scheme."
    ),
    "no_residue": "Legacy restart: no legacy restart residue found.",
    "enabled_warning": (
        "Legacy restart: ENABLE_LEGACY_RESTART_GENERATOR is ON. This "
        "generator authors names it has no authority over and is kept "
        "only for regression baselining."
    ),
}

__all__ = [
    "LEGACY_RESTART_RULES",
    "ENABLE_LEGACY_RESTART_GENERATOR",
    "REPORT_LEGACY_RESIDUE",
    "STAND_DOWN_REASONS",
    "LEGACY_HANDLER_NUMBER_PREFIXES",
    "REPORT_DANGLING_PERFORM",
    "LEGACY_RESTART_MESSAGES",
]
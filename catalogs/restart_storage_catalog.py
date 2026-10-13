"""Site vocabulary for the restart working storage.

catalogs/ is the one layer where a real name may appear. Every name
here comes from the manual reference VMDZ1567; the SHAPES that consume
them live in rules/restart_storage_templates.py.

WHY THESE NAMES ARE CATALOGUED RATHER THAN RESOLVED

M3 resolves names by READING the converted program. The working storage
this module generates does not exist yet, so there is nothing to read.
A generated name must therefore be SITE DATA, which is what catalogs/
is for - not a literal invented inside a generator.

The EOF condition names are the exception worth noting: they are built
from the RECORD name, which IS resolved from the source. Only the
suffix convention is catalogued.

CORRECTION - the catalogue was written but never consulted

RestartNameResolver._declared_or_blank() returned a name ONLY when the
program already declared it. For a converted program it does not: these
fields are exactly what RestartStorageInjector is about to create. So
eleven names resolved empty, RestartConfig became unusable, and
RestartInjectionComposer refused - BEFORE the injector that would have
declared them ever ran:

    Restart resolver: commit_counter unresolved; refused to invent a value.
    Restart resolver: restart_record unresolved; refused to invent a value.
    Restart resolver: read_count_size unresolved; refused to invent a value.
    -> Restart injection: ... no restart family emitted.

The same shape as the applicability gate: the thing being tested is
created by the step the test blocks.

GENERATED_STORAGE_FIELDS names which roles the injector creates, so the
resolver can distinguish "absent because the program does not use it"
from "absent because we have not written it yet". Nothing is invented:
a generated name is SUPPLIED from this file and REPORTED as defaulted.

No logic, no regex. Data only.
"""

from __future__ import annotations

# =====================================================================
# Group names
# =====================================================================
SWITCH_GROUP = "WS-SWITCHES"
HELP_GROUP = "HELP-VARIABLE"
DATE_GROUP = "WS-DATE-CONVERSION"

# =====================================================================
# The EOF switch and its condition names
# =====================================================================
# "SW-" + record, then <record>-NOT-EOF / <record>-EOF. The manual
# reference names the switch after the record it guards, so one file
# cannot accidentally test another file's flag.
EOF_SWITCH_PREFIX = "SW-"
EOF_CONDITION_SUFFIX = "-EOF"
NOT_EOF_CONDITION_SUFFIX = "-NOT-EOF"

# =====================================================================
# Which role names the storage injector CREATES
# =====================================================================
# A role listed here may be answered from the catalogue when the source
# does not declare it, because this generator is about to declare it.
#
# A role NOT listed here must come from the source and is refused when
# absent - file_name, record_name, read_paragraph, process_paragraph,
# program_constant, error_paragraph and abend_module are all properties
# of the program, not of the restart mechanism.
GENERATED_STORAGE_FIELDS = (
    "run_date_field",       # DATE_GROUP
    "input_counter",        # HELP_GROUP
    "commit_counter",       # HELP_GROUP
    "input_save_area",      # HELP_GROUP
    "restart_record",       # HELP_GROUP
    "restart_key_field",    # HELP_GROUP
    "read_count_field",     # HELP_GROUP
)

# The EOF pair is built from the resolved record name, not catalogued,
# so it is listed separately: the SUFFIX is site data, the NAME is not.
GENERATED_EOF_CONDITIONS = (
    "eof_condition",
    "not_eof_condition",
)

# =====================================================================
# Checkpoint payload geometry - MEASURED first, catalogued as fallback
# =====================================================================
# The payload length is the sum of these two PICTURE sizes. When the
# program already declares the fields the resolver MEASURES them and
# these values are never used. They exist so a program that does not yet
# carry the restart record can still be sized.
#
# Both are taken from the manual reference VMDZ1567:
#
#     03  NB-READ      PIC 9(15).
#     03  KY-RESTART   PIC X(1200).
#
# 15 + 1200 = 1215, which is the payload length the resolver measured on
# the programs that already carried the record.
DEFAULT_READ_COUNT_SIZE = 15
DEFAULT_RESTART_KEY_SIZE = 1200

# =====================================================================
# The date conversion group, verbatim from the manual reference.
# =====================================================================
# A literal block rather than a template: every subordinate name is site
# vocabulary and the layout is fixed. Parameterising it would move those
# names into rules/, where no name may appear.
DATE_GROUP_LINES = (
    "01  {group}.",
    "    03  DA-YYMMDD.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "    03  DA-DDMMCCYY.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  CC                     PIC 99    VALUE ZERO.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "    03  DA-CCYYMMDD.",
    "        05  CC                     PIC 99    VALUE ZERO.",
    "        05  YY                     PIC 99    VALUE ZERO.",
    "        05  MM                     PIC 99    VALUE ZERO.",
    "        05  DD                     PIC 99    VALUE ZERO.",
    "    03  DA-CCYYMMDD-R REDEFINES DA-CCYYMMDD.",
    "        05  CCYY                   PIC 9999.",
    "        05  MM                     PIC 99.",
    "        05  DD                     PIC 99.",
    "    03  DA-DD-MM-CCYY.",
    "        05  DD                     PIC 9(02).",
    "        05  TE-MARKER1             PIC X     VALUE '.'.",
    "        05  MM                     PIC 9(02).",
    "        05  TE-MARKER2             PIC X     VALUE '.'.",
    "        05  CCYY                   PIC 9(04).",
)

__all__ = [
    "DATE_GROUP",
    "DATE_GROUP_LINES",
    "DEFAULT_READ_COUNT_SIZE",
    "DEFAULT_RESTART_KEY_SIZE",
    "EOF_CONDITION_SUFFIX",
    "EOF_SWITCH_PREFIX",
    "GENERATED_EOF_CONDITIONS",
    "GENERATED_STORAGE_FIELDS",
    "HELP_GROUP",
    "NOT_EOF_CONDITION_SUFFIX",
    "SWITCH_GROUP",
]
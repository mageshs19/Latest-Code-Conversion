# LOCATION: converter/generators/restart/restart_storage_builder.py
# ACTION: REPLACE ENTIRE FILE
"""Builds the WORKING-STORAGE the restart family depends on.

    01 <switch group>     the EOF switch and its two 88-levels
    01 <help group>       restart record, save area, counters
    01 <date group>       the date conversion layout

WHY THIS EXISTS

SelectParagraphGenerator - the legacy path - emits all three as a side
effect of generating restart paragraphs. Gating it to stop the duplicate
DZ01RSTV include, the FILE SECTION damage and the dead 810/820 twins
also removed the storage, leaving DA-CCYYMMDD undefined and the audit
columns unpopulated. Five defects traded for three worse ones.

This module takes ownership of the storage so the gate becomes safe.

MEASURED, NOT DECLARED

The two lengths come from RestartProgramNames, where M3 measured them
from the source PICTUREs. A program whose restart key is 800 bytes gets
PIC X(800); the manual reference's 1200 is not a constant here.

REFUSE, DO NOT INVENT

A name the resolver could not establish, or a size it could not
measure, produces NO storage and one message per cause. Half a layout
is worse than none: the generated paragraphs would MOVE into fields
that do not exist.

THE EOF SWITCH IS NAMED AFTER THE RECORD

<record>-EOF / <record>-NOT-EOF, switch SW-<record>, per the manual.
One file cannot then test another file's flag. The record name is
RESOLVED; only the affixes are catalogued.

CORRECTION - "RESOLVED" meant MEASURED, not DERIVED

RestartNameResolver measures record_name by reading the source text
during the FINISHING phase - before UpdateInputRecordRenamer performs
the VM..BD../VM..BZ..->VMDZ.. derivation in POSTPROCESS. _record() then
composed SW-VMBD205I / VMBD205I-EOF / VMBD205I-NOT-EOF: internally
consistent with each other (switch_group() builds all three from ONE
_record() call), but carrying the SOURCE spelling into generated DB2
COBOL.

Proven on disk (VM1BD567_13-10-2026_072742.cbl): the program's restart
storage was injected TWICE during the same conversion, each time from
a DIFFERENT _record() snapshot (VMBD205I, then VMDZ205I, after an
interleaved rename pass touched the bare record references elsewhere
in the text). Because _record() never derived its own answer, the two
injections produced two DIFFERENT, non-idempotent switch groups instead
of the SAME group twice - which is what let the duplicate survive
whatever "already declared" check should have caught it.

Neither downstream renamer can repair a compound built on the record
name after the fact:

    UpdateInputRecordRenamer.WORD_RECORD_PATTERN_TEMPLATE
        (?<![A-Z0-9-]){name}(?![A-Z0-9-])
        - blocks a match with a hyphen on EITHER side, so it can touch
          neither "SW-VMBD205I" (hyphen before) nor "VMBD205I-EOF"
          (hyphen after).

    CopybookReferenceRenamer.WORD_REFERENCE_PATTERN_TEMPLATE
        (?<![A-Z0-9-]){name}(?![A-Z0-9])
        - allows a trailing hyphen (so "VMBD205I-EOF" renames), but
          still blocks a leading one, so "SW-VMBD205I" is untouched
          regardless of which renamer runs.

Patching either renamer to recognise this ONE catalogued prefix would
couple generic rename logic to a restart-specific convention, and would
still leave every OTHER future compound convention exposed to the same
class of defect. The record name is this builder's OWN input; deriving
it HERE, once, in the ONE place all three names are composed, is the
root fix - every caller (however many times it is invoked) now gets a
name that is consistent with itself and with every other invocation,
which is the actual property PERFORM ... UNTIL / SET depend on.

GEOMETRY IS NOT OURS

Lines carry meaningful RELATIVE indent. Area B alignment and the
sequence area are applied by the shared passes the retrieval path
already uses.
"""

from __future__ import annotations

from catalogs.restart_storage_catalog import (
    DATE_GROUP,
    DATE_GROUP_LINES,
    EOF_CONDITION_SUFFIX,
    EOF_SWITCH_PREFIX,
    HELP_GROUP,
    NOT_EOF_CONDITION_SUFFIX,
    SWITCH_GROUP,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.services.name_derivation_resolver import NameDerivationResolver
from rules.restart_storage_templates import (
    ENFORCE_RESTART_STORAGE,
    EOF_FALSE_VALUE,
    EOF_TRUE_VALUE,
    HELP_GROUP_TEMPLATE,
    RESTART_STORAGE_MESSAGES,
    SWITCH_GROUP_TEMPLATE,
)

# Names and measurements this builder cannot render without.
REQUIRED_NAMES = (
    "record_name",
    "restart_record",
    "read_count_field",
    "restart_key_field",
    "input_save_area",
    "commit_counter",
    "input_counter",
)
REQUIRED_SIZES = (
    "read_count_size",
    "restart_key_size",
)


class RestartStorageBuilder:
    """Renders the restart working storage, or refuses and says why."""

    def __init__(
        self,
        config: RestartConfig,
        name_derivation_resolver: NameDerivationResolver | None = None,
    ) -> None:
        self.config = config
        self.messages: list[str] = []
        # CORRECTION: injected, not hardcoded. Defaults to the same
        # generic VM..BD../VM..BZ..->VMDZ.. resolver UpdateInputRecord
        # Renamer and CopybookReferenceRenamer already use, so every
        # owner of this derivation rule agrees on one implementation.
        self._name_resolver = name_derivation_resolver or NameDerivationResolver()

    #
    # Public surface
    #
    def build(self) -> tuple[str, ...]:
        """Every group, in declaration order. Empty when refused."""
        self.messages = []

        if not ENFORCE_RESTART_STORAGE:
            self._log("disabled")
            return ()

        if not self._usable():
            return ()

        lines: list[str] = []
        lines.extend(self.switch_group())
        lines.append("")
        lines.extend(self.help_group())
        lines.append("")
        lines.extend(self.date_group())

        self._log(
            "built",
            count=len([line for line in lines if line.strip()]),
            groups=", ".join((SWITCH_GROUP, HELP_GROUP, DATE_GROUP)),
        )
        return tuple(lines)

    def switch_group(self) -> tuple[str, ...]:
        """The EOF switch and its two condition names."""
        values = {
            "switch_group": SWITCH_GROUP,
            "eof_switch": self.eof_switch(),
            "eof_condition": self.eof_condition(),
            "not_eof_condition": self.not_eof_condition(),
            "eof_true": EOF_TRUE_VALUE,
            "eof_false": EOF_FALSE_VALUE,
        }
        return tuple(line.format(**values) for line in SWITCH_GROUP_TEMPLATE)

    def help_group(self) -> tuple[str, ...]:
        """Restart record, input save area and the two counters."""
        names = self.config.names
        values = {
            "help_group": HELP_GROUP,
            "restart_record": names.restart_record,
            "read_count_field": names.read_count_field,
            "read_count_size": names.read_count_size,
            "restart_key_field": names.restart_key_field,
            "restart_key_size": names.restart_key_size,
            "input_save_area": names.input_save_area,
            "commit_counter": names.commit_counter,
            "input_counter": names.input_counter,
        }
        return tuple(line.format(**values) for line in HELP_GROUP_TEMPLATE)

    def date_group(self) -> tuple[str, ...]:
        """The date conversion layout, from the catalog."""
        return tuple(
            line.format(group=DATE_GROUP) for line in DATE_GROUP_LINES
        )

    #
    # Names built from the RESOLVED record name
    #
    def eof_switch(self) -> str:
        record = self._record()
        return f"{EOF_SWITCH_PREFIX}{record}" if record else ""

    def eof_condition(self) -> str:
        record = self._record()
        return f"{record}{EOF_CONDITION_SUFFIX}" if record else ""

    def not_eof_condition(self) -> str:
        record = self._record()
        return f"{record}{NOT_EOF_CONDITION_SUFFIX}" if record else ""

    def _record(self) -> str:
        """The record name every generated identifier in this group is
        built on - DERIVED to its final DB2 spelling.

        CORRECTION (NEW-2): this used to return
        self.config.names.record_name verbatim. That value is MEASURED
        from the source during the FINISHING phase, before the
        VM..BD../VM..BZ..->VMDZ.. rename runs in POSTPROCESS, so every
        name this builder composes (SW-<record>, <record>-EOF,
        <record>-NOT-EOF) carried the SOURCE spelling into generated
        DB2 COBOL. Deriving HERE - the one place all three names are
        composed - guarantees eof_switch()/eof_condition()/
        not_eof_condition() always agree with each other AND with any
        other invocation of this builder against the same config,
        however many times the storage injection runs.

        derive() returns a non-matching name unchanged (e.g. a file
        name like OPERATIES, or an already-derived VMDZ... name), so
        this is always safe to apply unconditionally.
        """
        source = str(self.config.names.record_name or "").strip().upper()
        if not source:
            return ""
        derived = self._name_resolver.derive(source)
        return str(derived or source).strip().upper()

    #
    # Gate
    #
    def _usable(self) -> bool:
        names = self.config.names
        refused = False

        for name in REQUIRED_NAMES:
            if not str(getattr(names, name, "") or "").strip():
                self._log("refused", name=name)
                refused = True

        for size in REQUIRED_SIZES:
            if int(getattr(names, size, 0) or 0) <= 0:
                self._log("unmeasured", name=size)
                refused = True

        return not refused

    #
    # Reporting
    #
    def _log(self, key: str, **values) -> None:
        template = RESTART_STORAGE_MESSAGES.get(str(key or ""), "")
        if template:
            self.messages.append(template.format(**values))


__all__ = [
    "REQUIRED_NAMES",
    "REQUIRED_SIZES",
    "RestartStorageBuilder",
]
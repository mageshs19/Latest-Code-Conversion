# LOCATION: converter/generators/restart/restart_storage_builder.py
# ACTION: CREATE NEW FILE
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

    def __init__(self, config: RestartConfig) -> None:
        self.config = config
        self.messages: list[str] = []

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
        return str(self.config.names.record_name or "").strip().upper()

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
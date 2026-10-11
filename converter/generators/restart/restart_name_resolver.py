# LOCATION: converter/generators/restart/restart_name_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""Resolves the program-side names the restart templates need.

RESPONSIBILITY

Read a converted COBOL source and establish, from the source itself:

    file name, record name, reader paragraph, EOF / NOT-EOF condition
    names, business processing paragraph, input counter, commit counter,
    input save area, checkpoint payload field names AND THEIR PICTURE
    SIZES, program constant, run date field, SQL error paragraph, abend
    module.

REFUSE, DO NOT GUESS

An unresolved name is returned empty, an unmeasured size is returned
zero, and both are REPORTED.

FALLBACK POLICY

A catalog default is applied ONLY when the name is also DECLARED in the
source.

MEASURE, DO NOT ASSUME

The checkpoint payload length is the sum of the PICTURE sizes of the two
restart-record subfields. Those sizes are read here.

CORRECTION - the EOF pair was matched by NAME SHAPE, not by meaning

    EOF_SUFFIX    = "-EOF"
    NOT_EOF_INFIX = "-NOT-EOF"

A program declaring the manual convention resolves:

    88 VMDZ205I-NOT-EOF VALUE 'N'    -> contains "-NOT-EOF"  OK
    88 VMDZ205I-EOF     VALUE 'Y'    -> ends with "-EOF"     OK

A program declaring the shorter, equally legal form resolves NOTHING:

    88 NOT-EOF VALUE 'N'   "-NOT-EOF" in "NOT-EOF"    -> False
    88 EOF     VALUE 'Y'   "EOF".endswith("-EOF")     -> False

Four names then collapse from one naming mismatch, because record_name
and read_paragraph are derived downstream of the condition pair.

Matching a NAME SHAPE is enforcing a convention. The MEANING of the
pair is carried by the VALUE: the condition that is true at end of file
is the one whose 88 carries the end-of-file value. That is a
MEASUREMENT, which is what this module is for.

Resolution order, so no program that resolves today can change:

    1. the documented convention, exactly as before,
    2. failing that, the 88-levels subordinate to the switch named in
       the reader's AT END, paired by VALUE.

Step 2 is scoped to that switch on purpose. A blind VALUE scan would
pick up any other 'Y'/'N' flag in the DATA DIVISION - a restart-found
switch, a status flag - and bind the loop to the wrong condition.

No program, paragraph, record, table, cursor or host variable name is
hardcoded. Regex lives in patterns/restart_patterns.py, constants in
rules/restart_standard_rules.py, vocabulary in catalogs/.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from catalogs.restart_paragraph_catalog import (
    DEFAULT_ABEND_MODULE,
    DEFAULT_COMMIT_COUNTER,
    DEFAULT_ERROR_PARAGRAPH,
    DEFAULT_INPUT_COUNTER,
    DEFAULT_INPUT_SAVE_AREA,
    DEFAULT_PROGRAM_CONSTANT,
    DEFAULT_READ_COUNT_FIELD,
    DEFAULT_READ_PARAGRAPH,
    DEFAULT_RESTART_KEY_FIELD,
    DEFAULT_RESTART_RECORD,
    DEFAULT_RUN_DATE_FIELD,
)
from converter.generators.restart.restart_config import RestartProgramNames
from patterns.restart_patterns import (
    ELEMENTARY_ITEM_PATTERN,
    FD_PATTERN,
    LEVEL_88_PATTERN,
    OPEN_INPUT_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PERFORM_UNTIL_PATTERN,
    PICTURE_SIZE_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    READ_INTO_PATTERN,
    SQL_INCLUDE_PATTERN,
)
from rules.restart_standard_rules import RESTART_PARAGRAPH_PREFIXES

EOF_SUFFIX = "-EOF"
NOT_EOF_INFIX = "-NOT-EOF"
EOF_TRUE_VALUE = "Y"
EOF_FALSE_VALUE = "N"
PICTURE_PREFIX = "PIC "
LEVEL_88 = "88"

# AT END MOVE 'Y' TO SW-EOF   /   AT END SET VMDZ205I-EOF TO TRUE
AT_END_MOVE_PATTERN = re.compile(
    r"\bAT\s+END\b.*?\bTO\s+(?P<switch>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)
AT_END_SET_PATTERN = re.compile(
    r"\bAT\s+END\b\s*SET\s+(?P<condition>[A-Z0-9][A-Z0-9-]*)\s+TO\s+TRUE",
    flags=re.IGNORECASE,
)


@dataclass
class ResolutionReport:
    """What was found, what was defaulted, what was refused."""

    resolved: dict[str, object]
    defaulted: list[str]
    refused: list[str]
    messages: list[str]


class RestartNameResolver:
    """Turns COBOL source lines into RestartProgramNames."""

    def __init__(self, line_utils) -> None:
        """`line_utils` is the SHARED retrieval utility."""
        self.line_utils = line_utils

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def resolve(
        self,
        lines: list[str],
    ) -> tuple[RestartProgramNames, ResolutionReport]:
        logical = self._logical_lines(lines)
        split = self._procedure_index(logical)
        data, procedure = logical[:split], logical[split:]

        declared = self._declared_items(data)

        file_name, record_name = self._file_and_record(data, procedure)
        eof, not_eof = self._eof_conditions(data, procedure)

        found: dict[str, object] = {
            "file_name": file_name,
            "record_name": record_name,
            "eof_condition": eof,
            "not_eof_condition": not_eof,
            "read_paragraph": self._read_paragraph(procedure),
            "process_paragraph": self._process_paragraph(procedure, eof),
            "program_constant": self._declared_or_blank(
                declared, DEFAULT_PROGRAM_CONSTANT
            ),
            "run_date_field": self._declared_or_blank(
                declared, DEFAULT_RUN_DATE_FIELD
            ),
            "input_counter": self._declared_or_blank(
                declared, DEFAULT_INPUT_COUNTER
            ),
            "commit_counter": self._declared_or_blank(
                declared, DEFAULT_COMMIT_COUNTER
            ),
            "input_save_area": self._declared_or_blank(
                declared, DEFAULT_INPUT_SAVE_AREA
            ),
            "restart_record": self._declared_or_blank(
                declared, DEFAULT_RESTART_RECORD
            ),
            "restart_key_field": self._declared_or_blank(
                declared, DEFAULT_RESTART_KEY_FIELD
            ),
            "read_count_field": self._declared_or_blank(
                declared, DEFAULT_READ_COUNT_FIELD
            ),
            "read_count_size": declared.get(DEFAULT_READ_COUNT_FIELD, 0),
            "restart_key_size": declared.get(DEFAULT_RESTART_KEY_FIELD, 0),
            "error_paragraph": self._error_paragraph(logical),
            "abend_module": self._declared_or_blank(
                declared, DEFAULT_ABEND_MODULE
            ),
        }

        names = RestartProgramNames(**found)
        return names, self._report(found, names)

    # -----------------------------------------------------------------
    # Line handling
    # -----------------------------------------------------------------

    def _logical_lines(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        for raw in lines or []:
            logical = str(self.line_utils.logical(raw) or "").strip()
            if not logical or self.line_utils.is_comment(logical):
                continue
            out.append(" ".join(logical.upper().split()))
        return out

    @staticmethod
    def _procedure_index(logical: list[str]) -> int:
        for index, line in enumerate(logical):
            if PROCEDURE_DIVISION_PATTERN.match(line):
                return index
        return len(logical)

    # -----------------------------------------------------------------
    # Declarations
    # -----------------------------------------------------------------

    @staticmethod
    def _declared_items(data: list[str]) -> dict[str, int]:
        """Declared name -> PICTURE size, 0 when the item is a group."""
        items: dict[str, int] = {}
        for line in data:
            match = ELEMENTARY_ITEM_PATTERN.match(line)
            if match:
                size = PICTURE_SIZE_PATTERN.match(
                    PICTURE_PREFIX + match.group("picture")
                )
                items[match.group("name")] = (
                    int(size.group("size")) if size else 0
                )
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0].isdigit():
                items.setdefault(parts[1].rstrip("."), 0)
        return items

    @staticmethod
    def _declared_or_blank(declared: dict[str, int], candidate: str) -> str:
        return candidate if candidate in declared else ""

    # -----------------------------------------------------------------
    # File, record, EOF
    # -----------------------------------------------------------------

    @staticmethod
    def _file_and_record(
        data: list[str],
        procedure: list[str],
    ) -> tuple[str, str]:
        for line in procedure:
            match = READ_INTO_PATTERN.match(line)
            if match:
                return match.group("file"), match.group("record")

        file_name = ""
        for line in procedure:
            match = OPEN_INPUT_PATTERN.match(line)
            if match:
                file_name = match.group("file")
                break

        if not file_name:
            for line in data:
                match = FD_PATTERN.match(line)
                if match:
                    file_name = match.group("file")
                    break

        return file_name, ""

    @classmethod
    def _eof_conditions(
        cls,
        data: list[str],
        procedure: list[str],
    ) -> tuple[str, str]:
        """The EOF / NOT-EOF pair, by convention or by measurement."""
        eof, not_eof = cls._eof_by_convention(data)
        if eof and not_eof:
            return eof, not_eof

        measured_eof, measured_not_eof = cls._eof_by_value(data, procedure)
        return eof or measured_eof, not_eof or measured_not_eof

    @staticmethod
    def _eof_by_convention(data: list[str]) -> tuple[str, str]:
        """The documented <record>-EOF / <record>-NOT-EOF naming."""
        eof = ""
        not_eof = ""
        for line in data:
            match = LEVEL_88_PATTERN.match(line)
            if not match:
                continue
            name, value = match.group("name"), match.group("value")
            if NOT_EOF_INFIX in name:
                not_eof = not_eof or name
            elif name.endswith(EOF_SUFFIX) and value == EOF_TRUE_VALUE:
                eof = eof or name
        return eof, not_eof

    @classmethod
    def _eof_by_value(
        cls,
        data: list[str],
        procedure: list[str],
    ) -> tuple[str, str]:
        """The 88-levels of the switch the reader sets at end of file.

        Scoped to that switch: a blind VALUE scan would bind the loop to
        a restart-found flag or any other 'Y'/'N' switch in the program.
        """
        condition = cls._at_end_condition(procedure)
        if condition:
            return condition, cls._sibling_of(data, condition)

        switch = cls._at_end_switch(procedure)
        if not switch:
            return "", ""

        eof = ""
        not_eof = ""
        for name, value in cls._conditions_under(data, switch):
            if value == EOF_TRUE_VALUE:
                eof = eof or name
            elif value == EOF_FALSE_VALUE:
                not_eof = not_eof or name
        return eof, not_eof

    @staticmethod
    def _at_end_switch(procedure: list[str]) -> str:
        """The field a reader MOVEs its end-of-file value into."""
        for line in procedure:
            match = AT_END_MOVE_PATTERN.search(line)
            if match:
                return match.group("switch").upper().rstrip(".")
        return ""

    @staticmethod
    def _at_end_condition(procedure: list[str]) -> str:
        """The 88 a reader SETs TO TRUE at end of file."""
        for line in procedure:
            match = AT_END_SET_PATTERN.search(line)
            if match:
                return match.group("condition").upper().rstrip(".")
        return ""

    @staticmethod
    def _conditions_under(
        data: list[str],
        switch: str,
    ) -> list[tuple[str, str]]:
        """(name, value) of every 88 subordinate to `switch`."""
        out: list[tuple[str, str]] = []
        inside = False
        for line in data:
            parts = line.split()
            if not parts:
                continue

            if parts[0] == LEVEL_88:
                if inside:
                    match = LEVEL_88_PATTERN.match(line)
                    if match:
                        out.append(
                            (match.group("name"), match.group("value"))
                        )
                continue

            if parts[0].isdigit():
                inside = (
                    len(parts) >= 2
                    and parts[1].rstrip(".").upper() == switch
                )
        return out

    @classmethod
    def _sibling_of(cls, data: list[str], condition: str) -> str:
        """The other 88 declared beside `condition`."""
        group: list[str] = []
        for line in data:
            parts = line.split()
            if not parts:
                continue
            if parts[0] == LEVEL_88:
                match = LEVEL_88_PATTERN.match(line)
                if match:
                    group.append(match.group("name"))
                continue
            if parts[0].isdigit():
                if condition in group:
                    break
                group = []

        for name in group:
            if name != condition:
                return name
        return ""

    # -----------------------------------------------------------------
    # Paragraphs
    # -----------------------------------------------------------------

    @staticmethod
    def _read_paragraph(procedure: list[str]) -> str:
        headers = [
            match.group("name")
            for line in procedure
            if (match := PARAGRAPH_HEADER_PATTERN.match(line))
        ]
        if DEFAULT_READ_PARAGRAPH in headers:
            return DEFAULT_READ_PARAGRAPH
        for index, line in enumerate(procedure):
            if READ_INTO_PATTERN.match(line):
                return RestartNameResolver._owner(procedure, index)
        return ""

    @staticmethod
    def _owner(procedure: list[str], index: int) -> str:
        owner = ""
        for position in range(index):
            match = PARAGRAPH_HEADER_PATTERN.match(procedure[position])
            if match:
                owner = match.group("name")
        return owner

    @staticmethod
    def _process_paragraph(procedure: list[str], eof: str) -> str:
        for line in procedure:
            match = PERFORM_UNTIL_PATTERN.match(line)
            if not match:
                continue
            name = match.group("paragraph")
            if RestartNameResolver._is_infrastructure(name):
                continue
            if eof and eof not in match.group("condition"):
                continue
            return name
        return ""

    @staticmethod
    def _is_infrastructure(name: str) -> bool:
        return any(
            name.startswith(prefix) for prefix in RESTART_PARAGRAPH_PREFIXES
        )

    @staticmethod
    def _error_paragraph(logical: list[str]) -> str:
        """The SQL error paragraph, only when its include is present."""
        for line in logical:
            match = SQL_INCLUDE_PATTERN.match(line)
            if match and match.group("name") == DEFAULT_ERROR_PARAGRAPH:
                return DEFAULT_ERROR_PARAGRAPH
        return ""

    # -----------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------

    @staticmethod
    def _report(
        found: dict[str, object],
        names: RestartProgramNames,
    ) -> ResolutionReport:
        refused = list(names.missing())
        messages = [
            f"Restart resolver: {key} unresolved; refused to invent a value."
            for key in refused
        ]
        messages.extend(
            f"Restart resolver: {key} = {value}"
            for key, value in sorted(found.items())
            if value
        )
        return ResolutionReport(
            resolved={k: v for k, v in found.items() if v},
            defaulted=[],
            refused=refused,
            messages=messages,
        )


__all__ = ["ResolutionReport", "RestartNameResolver"]
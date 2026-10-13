"""Resolves the program-side names the restart templates need.

RESPONSIBILITY

Read a converted COBOL source and establish, from the source itself:

    file name, record name, reader paragraph, EOF / NOT-EOF condition
    names, business processing paragraph, input counter, commit counter,
    input save area, checkpoint payload field names AND THEIR PICTURE
    SIZES, program constant, run date field, SQL error paragraph, abend
    module.

OWNERSHIP, NOT DECLARATION

    PROGRAM-owned   file_name, record_name, read_paragraph,
                    process_paragraph, program_constant,
                    error_paragraph, abend_module
                    -> read from the source, REFUSED when absent.

    GENERATOR-owned catalogs.restart_storage_catalog
                    .GENERATED_STORAGE_FIELDS, the two picture sizes
                    and the EOF pair
                    -> MEASURED when already declared, otherwise
                       SUPPLIED from the catalogue and reported in
                       ResolutionReport.defaulted.

The earlier policy - "a catalog default is applied ONLY when the name is
also DECLARED" - was right for a name the program owns and wrong for a
name this generator owns. Seven working-storage fields are created by
RestartStorageInjector; requiring them to be declared first meant they
resolved empty, RestartConfig became unusable, and
RestartInjectionComposer refused BEFORE the injector that declares them
ever ran.

CORRECTION A - a SUPPLIED name was used to FILTER a measurement

_process_paragraph rejects a loop whose condition does not mention the
EOF condition. It was handed the FINAL pair, which may be a name this
generator is about to write. VMDZ1567 loops on

    PERFORM VERWERKING UNTIL SW-EOF = 'Y'.

and the built VMBD205I-EOF is not in that text, so the only business
paragraph in the program was rejected and the whole family refused.

A measurement is filtered by a measurement. _eof_measured() returns what
the SOURCE declares; _eof_conditions() adds the built fallback for the
GENERATED code. Only the first may filter a reading of the source.

CORRECTION B - only READ ... INTO was recognised

VMDZ1526 reads with

    READ INFIL
       AT END MOVE +1 TO SW-EOF.

and declares the record on its FD:

    FD  INFIL
        DATA RECORD IS VMDZ205I.

That is standard COBOL. The resolver saw no INTO, returned an empty
record_name, and refused - taking read_paragraph and the EOF pair with
it, because both are derived from it. One gap, four refusals.

CORRECTION C - the EOF pair was matched by NAME SHAPE, not by meaning

    EOF_SUFFIX    = "-EOF"
    NOT_EOF_INFIX = "-NOT-EOF"

A program declaring the manual convention resolves:

    88 VMDZ205I-NOT-EOF VALUE 'N'    -> contains "-NOT-EOF"  OK
    88 VMDZ205I-EOF     VALUE 'Y'    -> ends with "-EOF"     OK

A program declaring the shorter, equally legal form resolves NOTHING:

    88 NOT-EOF VALUE 'N'   "-NOT-EOF" in "NOT-EOF"    -> False
    88 EOF     VALUE 'Y'   "EOF".endswith("-EOF")     -> False

The MEANING of the pair is carried by the VALUE: the condition true at
end of file is the one whose 88 carries the end-of-file value.

Resolution order, so no program that resolves today can change:

    1. the documented convention,
    2. the 88-levels subordinate to the switch named in the reader's
       AT END, paired by VALUE,
    3. BUILT from the resolved record name using the catalogued
       suffixes - the pair RestartStorageInjector will declare. A
       program using a bare 77-level switch with no 88s reaches step 3.

Steps 2 and 3 are scoped on purpose. A blind VALUE scan would pick up
any other 'Y'/'N' flag and bind the loop to the wrong condition.

MEASURE, DO NOT ASSUME

The checkpoint payload length is the sum of the PICTURE sizes of the two
restart-record subfields. They are read here when the fields exist; the
catalogued sizes are used only when they do not, and are reported.

CORRECTION D - record_name does NOT get VM..BD../VM..BZ.. derivation
HERE

A prior edit added a _derive_lines() pass that ran NameDerivationResolver
over the whole text before measurement, so record_name would come out
already VMDZ-spelled. That broke this module's own ownership contract
above: record_name is PROGRAM-owned, read from the source AS IT IS,
never decorated. The edit also left the file with a duplicate
`from __future__ import annotations` (illegal after other imports have
already executed - a SyntaxError on real import, invisible to
ast.parse(), which does not enforce future-statement placement the way
compile()/import does) and a call to self._name_resolver, which was
never actually assigned once the duplicate header got partially cleaned
up - NameError waiting to happen the moment any record name matched the
derivable shape.

The derivation this was trying to achieve belongs - and already lives,
tested - in RestartStorageBuilder._record(), the one place SW-<record>,
<record>-EOF and <record>-NOT-EOF are actually composed
(tests/restart/test_m5_storage_builder_derives_record.py). This module
goes back to measuring record_name faithfully; RestartStorageBuilder
derives it when building generated identifiers from it. One owner per
concern.

CORRECTION E - WITHDRAWN. A run_date_source entry was added here

run_date_field is resolved by this module, carried by RestartConfig and
MOVEd into the checkpoint date column by CONTROL_TEMPLATE - but nothing
writes a value INTO it, so the checkpoint key is built from an unprimed
field. That defect is real and still open.

The attempted fix added three names here - run_date_source,
date_staging_field, date_staging_redefines - and to
RestartProgramNames.REQUIRED. That was the error. REQUIRED drives
missing() -> is_complete() -> is_usable(), and the injection composer
refuses when is_usable() is False, so three names that cannot resolve
for every accepted program silenced the ENTIRE restart family and failed
roughly a hundred tests that had nothing to do with dates.
test_eighteen_entries_are_required exists to catch exactly that.

The entries are withdrawn. When the priming is attempted again it must
not enlarge REQUIRED: the artefact evidence shows the existing date
realignment pass already emits the correct three-MOVE sequence whenever
the SOURCE of a DB2 DATE move is an 8-byte CCYYMMDD field, so the fix is
to change what CONTROL_TEMPLATE moves FROM, not to add new names here.

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
from catalogs.restart_storage_catalog import (
    DEFAULT_READ_COUNT_SIZE,
    DEFAULT_RESTART_KEY_SIZE,
    EOF_CONDITION_SUFFIX,
    GENERATED_STORAGE_FIELDS,
    NOT_EOF_CONDITION_SUFFIX,
)
from converter.generators.restart.restart_config import RestartProgramNames
from converter.services import name_derivation_resolver  # noqa: F401 - kept for callers that introspect this module's imports; unused here, see CORRECTION D
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

# READ <file>, with or without INTO. The INTO form is matched first by
# READ_INTO_PATTERN; this catches the equally legal form where the
# record is declared on the FD. See CORRECTION B.
READ_PATTERN = re.compile(
    r"^READ\s+(?P<file>[A-Z0-9][A-Z0-9-]*)\b",
    flags=re.IGNORECASE,
)

# Anchored, so LABEL RECORD IS STANDARD cannot satisfy it.
DATA_RECORD_PATTERN = re.compile(
    r"^DATA\s+RECORDS?\s+(?:IS|ARE)\s+(?P<record>[A-Z0-9][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

FD_BLOCK_TERMINATORS = ("FD", "SD", "WORKING-STORAGE", "LINKAGE", "PROCEDURE")


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
        self._defaulted: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def resolve(
        self,
        lines: list[str],
    ) -> tuple[RestartProgramNames, ResolutionReport]:
        self._defaulted = []

        logical = self._logical_lines(lines)
        split = self._procedure_index(logical)
        data, procedure = logical[:split], logical[split:]
        declared = self._declared_items(data)

        file_name, record_name = self._file_and_record(data, procedure)

        # Measured first, built second. Only the MEASURED pair may
        # filter a reading of the source - see CORRECTION A.
        measured_eof, measured_not_eof = self._eof_measured(data, procedure)
        eof, not_eof = self._eof_conditions(
            (measured_eof, measured_not_eof), record_name
        )

        found: dict[str, object] = {
            # --- PROGRAM-owned: read, or refused -----------------------
            "file_name": file_name,
            "record_name": record_name,
            "read_paragraph": self._read_paragraph(procedure),
            "process_paragraph": self._process_paragraph(
                procedure, measured_eof
            ),
            "program_constant": self._declared_or_blank(
                declared, DEFAULT_PROGRAM_CONSTANT
            ),
            "error_paragraph": self._error_paragraph(logical),
            "abend_module": self._declared_or_blank(
                declared, DEFAULT_ABEND_MODULE
            ),
            # --- GENERATOR-owned: measured, or supplied -----------------
            "eof_condition": eof,
            "not_eof_condition": not_eof,
            "run_date_field": self._declared_or_generated(
                declared, DEFAULT_RUN_DATE_FIELD, "run_date_field"
            ),
            "input_counter": self._declared_or_generated(
                declared, DEFAULT_INPUT_COUNTER, "input_counter"
            ),
            "commit_counter": self._declared_or_generated(
                declared, DEFAULT_COMMIT_COUNTER, "commit_counter"
            ),
            "input_save_area": self._declared_or_generated(
                declared, DEFAULT_INPUT_SAVE_AREA, "input_save_area"
            ),
            "restart_record": self._declared_or_generated(
                declared, DEFAULT_RESTART_RECORD, "restart_record"
            ),
            "restart_key_field": self._declared_or_generated(
                declared, DEFAULT_RESTART_KEY_FIELD, "restart_key_field"
            ),
            "read_count_field": self._declared_or_generated(
                declared, DEFAULT_READ_COUNT_FIELD, "read_count_field"
            ),
            "read_count_size": self._measured_or_catalogued(
                declared,
                DEFAULT_READ_COUNT_FIELD,
                DEFAULT_READ_COUNT_SIZE,
                "read_count_size",
            ),
            "restart_key_size": self._measured_or_catalogued(
                declared,
                DEFAULT_RESTART_KEY_FIELD,
                DEFAULT_RESTART_KEY_SIZE,
                "restart_key_size",
            ),
        }
        names = RestartProgramNames(
            **{
                k: v
                for k, v in found.items()
                if k in RestartProgramNames.REQUIRED
            }
        )
        return names, self._report(found, names, self._defaulted)

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
        """A PROGRAM-owned name. Absent means absent."""
        return candidate if candidate in declared else ""

    def _declared_or_generated(
        self,
        declared: dict[str, int],
        candidate: str,
        role: str,
    ) -> str:
        """A GENERATOR-owned name.

        Declared -> use it. Absent and listed in GENERATED_STORAGE_FIELDS
        -> supply the catalogued name, because RestartStorageInjector is
        about to declare exactly that. Absent and NOT listed -> refuse.
        """
        if candidate in declared:
            return candidate
        if role in GENERATED_STORAGE_FIELDS:
            self._defaulted.append(role)
            return candidate
        return ""

    def _measured_or_catalogued(
        self,
        declared: dict[str, int],
        field: str,
        fallback: int,
        role: str,
    ) -> int:
        """A PICTURE size. Measured when present, catalogued when not."""
        size = int(declared.get(field, 0) or 0)
        if size > 0:
            return size
        self._defaulted.append(role)
        return int(fallback)

    # -----------------------------------------------------------------
    # File and record
    # -----------------------------------------------------------------

    @classmethod
    def _file_and_record(
        cls,
        data: list[str],
        procedure: list[str],
    ) -> tuple[str, str]:
        """The input file and the record the reader populates.

        See CORRECTION B: a bare READ is as legal as READ ... INTO.
        """
        for line in procedure:
            match = READ_INTO_PATTERN.match(line)
            if match:
                return match.group("file"), match.group("record")

        file_name = ""
        for line in procedure:
            match = READ_PATTERN.match(line)
            if match:
                file_name = match.group("file")
                break

        if not file_name:
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

        return file_name, cls._fd_record(data, file_name)

    @staticmethod
    def _fd_record(data: list[str], file_name: str) -> str:
        """The record declared under FD <file_name>.

        DATA RECORD IS <name> when stated, otherwise the first 01 inside
        the FD block. Returns "" when the FD is not found, so the caller
        still refuses rather than guessing.
        """
        wanted = str(file_name or "").strip().upper()
        if not wanted:
            return ""

        inside = False
        for line in data:
            parts = line.split()
            if not parts:
                continue

            fd = FD_PATTERN.match(line)
            if fd:
                inside = fd.group("file").upper() == wanted
                continue

            if not inside:
                continue

            stated = DATA_RECORD_PATTERN.match(line)
            if stated:
                return stated.group("record").upper().rstrip(".")

            if parts[0] == "01" and len(parts) >= 2:
                return parts[1].rstrip(".").upper()

            if parts[0] in FD_BLOCK_TERMINATORS:
                break

        return ""

    # -----------------------------------------------------------------
    # EOF conditions
    # -----------------------------------------------------------------

    def _eof_measured(
        self,
        data: list[str],
        procedure: list[str],
    ) -> tuple[str, str]:
        """The pair the SOURCE declares. Empty when it declares none.

        Measurement only - never the built fallback. Anything that
        filters a reading of the source must use THIS: a name we are
        about to generate does not appear in a loop the programmer
        already wrote. See CORRECTION A.
        """
        eof, not_eof = self._eof_by_convention(data)
        if eof and not_eof:
            return eof, not_eof

        measured_eof, measured_not_eof = self._eof_by_value(data, procedure)
        return eof or measured_eof, not_eof or measured_not_eof

    def _eof_conditions(
        self,
        measured: tuple[str, str],
        record_name: str,
    ) -> tuple[str, str]:
        """The pair the GENERATED family will use."""
        eof, not_eof = measured
        if eof and not_eof:
            return eof, not_eof

        built_eof, built_not_eof = self._eof_by_record(record_name)
        if not eof and built_eof:
            self._defaulted.append("eof_condition")
            eof = built_eof
        if not not_eof and built_not_eof:
            self._defaulted.append("not_eof_condition")
            not_eof = built_not_eof

        return eof, not_eof

    @staticmethod
    def _eof_by_record(record_name: str) -> tuple[str, str]:
        """<record>-EOF / <record>-NOT-EOF, the catalogued convention."""
        record = str(record_name or "").strip().upper()
        if not record:
            return "", ""
        return (
            f"{record}{EOF_CONDITION_SUFFIX}",
            f"{record}{NOT_EOF_CONDITION_SUFFIX}",
        )

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
        """The 88-levels of the switch the reader sets at end of file."""
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
        """The paragraph that owns the READ - either READ form."""
        headers = [
            match.group("name")
            for line in procedure
            if (match := PARAGRAPH_HEADER_PATTERN.match(line))
        ]
        if DEFAULT_READ_PARAGRAPH in headers:
            return DEFAULT_READ_PARAGRAPH
        for index, line in enumerate(procedure):
            if READ_INTO_PATTERN.match(line) or READ_PATTERN.match(line):
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
    def _process_paragraph(procedure: list[str], measured_eof: str) -> str:
        """The business loop.

        `measured_eof` is what the SOURCE declares, never the built
        pair - see CORRECTION A.
        """
        for line in procedure:
            match = PERFORM_UNTIL_PATTERN.match(line)
            if not match:
                continue
            name = match.group("paragraph")
            if RestartNameResolver._is_infrastructure(name):
                continue
            if measured_eof and measured_eof not in match.group("condition"):
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
        defaulted: list[str],
    ) -> ResolutionReport:
        refused = list(names.missing())
        unique_defaults = sorted(set(defaulted))

        messages = [
            f"Restart resolver: {key} unresolved; refused to invent a value."
            for key in refused
        ]
        messages.extend(
            f"Restart resolver: {key} = {found.get(key)} "
            "(supplied from the catalogue; the storage injector will "
            "declare it)."
            for key in unique_defaults
        )
        messages.extend(
            f"Restart resolver: {key} = {value}"
            for key, value in sorted(found.items())
            if value and key not in unique_defaults
        )
        return ResolutionReport(
            resolved={k: v for k, v in found.items() if v},
            defaulted=unique_defaults,
            refused=refused,
            messages=messages,
        )


__all__ = ["ResolutionReport", "RestartNameResolver"]
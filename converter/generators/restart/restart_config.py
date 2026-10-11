# LOCATION: converter/generators/restart/restart_config.py
# ACTION: REPLACE ENTIRE FILE
"""Immutable configuration consumed by every restart builder.

RESPONSIBILITY

Hold the resolved names and render the placeholder dictionary that the
templates in rules/restart_statement_templates.py expect. Nothing else.
No file is read, no source is parsed, no COBOL is emitted here.

WHY FROZEN

Three builders and one injector share this object. A mutable config let
an earlier pass change a name under a later one, which is how a
paragraph ended up performed under one name and declared under another.
Frozen removes the failure mode rather than documenting it.

TWO VALUES THIS CLASS REFUSES TO AUTHOR

    payload length - MEASURED from the two restart-record pictures
    retention      - SUPPLIED with the restart DCLGEN role

Both were once constants in rules/. A program whose restart record used
a different layout would then have had the wrong length written into its
checkpoint row, silently.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded. Defaults come from catalogs/, policy from rules/.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import ClassVar, Mapping

from catalogs.restart_paragraph_catalog import (
    PARAGRAPH_NAME_TEMPLATE,
    PARAGRAPH_SUFFIXES,
    QUERYNO_INSERT,
    QUERYNO_SELECT,
    QUERYNO_UPDATE,
    TABLE_PARAGRAPH_NAME_TEMPLATE,
    TABLE_SUFFIXED_ROLES,
    RestartDclgenRole,
)
from rules.restart_standard_rules import (
    COMMIT_TEST_THRESHOLD,
    DEFAULT_PARAGRAPH_SCHEME,
    DEFAULT_PHASE_NUMBER,
    ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT,
    PARAGRAPH_NUMBER_SCHEMES,
    REQUIRE_RETENTION_FROM_METADATA,
    RESTART_PARAGRAPH_ROLES,
    ROLE_ABEND,
    ROLE_COMMIT,
    ROLE_CONTROL,
    ROLE_INSERT,
    ROLE_RESTART_FOUND,
    ROLE_SELECT,
    ROLE_UPDATE,
    ROLE_WRITE_RESTART,
    SQLCODE_NOT_FOUND,
    SQLCODE_OK,
    STATUS_COMPLETE,
    STATUS_INCOMPLETE,
)
from rules.restart_statement_templates import COMPLETE_RUN_MESSAGE


@dataclass(frozen=True)
class RestartProgramNames:
    """Names and measurements that belong to the program being converted.

    Every entry is resolved from the source. An empty string, or a zero
    size, means "not resolved": it is reported, never guessed.
    """

    program_constant: str = ""
    run_date_field: str = ""
    file_name: str = ""
    record_name: str = ""
    read_paragraph: str = ""
    process_paragraph: str = ""
    eof_condition: str = ""
    not_eof_condition: str = ""
    input_counter: str = ""
    commit_counter: str = ""
    input_save_area: str = ""
    restart_record: str = ""
    restart_key_field: str = ""
    read_count_field: str = ""
    read_count_size: int = 0
    restart_key_size: int = 0
    error_paragraph: str = ""
    abend_module: str = ""

    REQUIRED: ClassVar[tuple[str, ...]] = (
        "program_constant",
        "run_date_field",
        "file_name",
        "record_name",
        "read_paragraph",
        "process_paragraph",
        "eof_condition",
        "not_eof_condition",
        "input_counter",
        "commit_counter",
        "input_save_area",
        "restart_record",
        "restart_key_field",
        "read_count_field",
        "read_count_size",
        "restart_key_size",
        "error_paragraph",
        "abend_module",
    )

    def missing(self) -> tuple[str, ...]:
        """Names and sizes the resolver could not establish."""
        out: list[str] = []
        for name in self.REQUIRED:
            value = getattr(self, name, "")
            if isinstance(value, int):
                if value <= 0:
                    out.append(name)
                continue
            if not str(value).strip():
                out.append(name)
        return tuple(out)

    def is_complete(self) -> bool:
        return not self.missing()


def build_paragraph_names(
    role: RestartDclgenRole,
    scheme: str = DEFAULT_PARAGRAPH_SCHEME,
) -> dict[str, str]:
    """Role -> paragraph name, for one numbering scheme."""
    numbers = PARAGRAPH_NUMBER_SCHEMES[scheme]
    names: dict[str, str] = {}

    for role_key in RESTART_PARAGRAPH_ROLES:
        number = numbers[role_key]
        suffix = PARAGRAPH_SUFFIXES[role_key]

        if role_key in TABLE_SUFFIXED_ROLES:
            names[role_key] = TABLE_PARAGRAPH_NAME_TEMPLATE.format(
                number=number,
                suffix=suffix,
                table=role.table_name,
            )
            continue

        names[role_key] = PARAGRAPH_NAME_TEMPLATE.format(
            number=number,
            suffix=suffix,
        )

    return names


@dataclass(frozen=True)
class RestartConfig:
    """Everything the restart builders need, resolved and immutable."""

    role: RestartDclgenRole
    names: RestartProgramNames
    paragraphs: Mapping[str, str]

    scheme: str = DEFAULT_PARAGRAPH_SCHEME
    phase_number: int = DEFAULT_PHASE_NUMBER

    queryno_select: int = QUERYNO_SELECT
    queryno_update: int = QUERYNO_UPDATE
    queryno_insert: int = QUERYNO_INSERT

    # -----------------------------------------------------------------
    # Construction
    # -----------------------------------------------------------------

    @classmethod
    def build(
        cls,
        role: RestartDclgenRole,
        names: RestartProgramNames,
        scheme: str = DEFAULT_PARAGRAPH_SCHEME,
    ) -> "RestartConfig":
        if scheme not in PARAGRAPH_NUMBER_SCHEMES:
            raise ValueError(f"unknown paragraph scheme: {scheme!r}")
        return cls(
            role=role,
            names=names,
            paragraphs=build_paragraph_names(role, scheme),
            scheme=scheme,
        )

    def with_names(self, names: RestartProgramNames) -> "RestartConfig":
        """A copy carrying freshly resolved program names."""
        return replace(self, names=names)

    # -----------------------------------------------------------------
    # Derived values
    # -----------------------------------------------------------------

    @property
    def payload_full_length(self) -> int:
        """Sum of the two restart-record subfield pictures."""
        return self.names.read_count_size + self.names.restart_key_size

    @property
    def payload_length_on_insert(self) -> int:
        return self.payload_full_length

    @property
    def payload_length_on_commit(self) -> int:
        if ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT:
            return self.payload_full_length
        return self.names.read_count_size

    @property
    def retention_days(self) -> int:
        return self.role.retention_days

    def paragraph(self, role: str) -> str:
        return self.paragraphs[role]

    def missing(self) -> tuple[str, ...]:
        return self.names.missing()

    def is_usable(self) -> bool:
        if REQUIRE_RETENTION_FROM_METADATA and self.retention_days <= 0:
            return False
        return self.names.is_complete()

    # -----------------------------------------------------------------
    # Template surface
    # -----------------------------------------------------------------

    def placeholders(self) -> dict[str, object]:
        """The single dictionary every template is rendered against."""
        role, names = self.role, self.names
        return {
            # paragraphs
            "control_paragraph": self.paragraph(ROLE_CONTROL),
            "select_paragraph": self.paragraph(ROLE_SELECT),
            "update_paragraph": self.paragraph(ROLE_UPDATE),
            "insert_paragraph": self.paragraph(ROLE_INSERT),
            "restart_found_paragraph": self.paragraph(ROLE_RESTART_FOUND),
            "write_restart_paragraph": self.paragraph(ROLE_WRITE_RESTART),
            "commit_paragraph": self.paragraph(ROLE_COMMIT),
            "abend_paragraph": self.paragraph(ROLE_ABEND),
            "error_paragraph": names.error_paragraph,
            # restart table
            "restart_table": role.table_name,
            "restart_group": role.host_record,
            "program_id_field": role.program_field,
            "phase_field": role.phase_field,
            "date_field": role.date_field,
            "status_field": role.status_field,
            "retention_field": role.retention_field,
            "payload_group": role.payload_group,
            "payload_length_field": role.payload_len_field,
            "payload_text_field": role.payload_text_field,
            # program names
            "program_constant": names.program_constant,
            "run_date_field": names.run_date_field,
            "file_name": names.file_name,
            "record_name": names.record_name,
            "read_paragraph": names.read_paragraph,
            "process_paragraph": names.process_paragraph,
            "eof_condition": names.eof_condition,
            "not_eof_condition": names.not_eof_condition,
            "input_counter": names.input_counter,
            "commit_counter": names.commit_counter,
            "input_save_area": names.input_save_area,
            "restart_record": names.restart_record,
            "restart_key_field": names.restart_key_field,
            "read_count_field": names.read_count_field,
            "abend_module": names.abend_module,
            # policy
            "phase_number": self.phase_number,
            "retention_days": self.retention_days,
            "status_complete": STATUS_COMPLETE,
            "status_incomplete": STATUS_INCOMPLETE,
            "sqlcode_ok": SQLCODE_OK,
            "sqlcode_not_found": SQLCODE_NOT_FOUND,
            "commit_threshold": COMMIT_TEST_THRESHOLD,
            "payload_length_insert": self.payload_length_on_insert,
            "payload_length_commit": self.payload_length_on_commit,
            "complete_message": COMPLETE_RUN_MESSAGE,
            # queryno
            "queryno_select": self.queryno_select,
            "queryno_update": self.queryno_update,
            "queryno_insert": self.queryno_insert,
            # filled by the main-flow builder
            "totals_block": "",
        }


__all__ = [
    "RestartConfig",
    "RestartProgramNames",
    "build_paragraph_names",
]
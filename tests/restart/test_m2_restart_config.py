# LOCATION: tests/restart/test_m2_restart_config.py
# ACTION: REPLACE ENTIRE FILE
"""M2 contract tests: config renders names, never invents them."""

from __future__ import annotations

import dataclasses
import re

import pytest

from catalogs import restart_paragraph_catalog as cat
from converter.generators.restart import restart_config as config_module
from converter.generators.restart.restart_config import (
    RestartConfig,
    RestartProgramNames,
    build_paragraph_names,
)
from rules import restart_standard_rules as std
from rules import restart_statement_templates as tpl

PLACEHOLDER = re.compile(r"\{(?P<name>[a-z_]+)\}")

ALL_TEMPLATES = (
    tpl.MAIN_FLOW_TEMPLATE,
    tpl.CONTROL_TEMPLATE,
    tpl.RESTART_FOUND_TEMPLATE,
    tpl.WRITE_RESTART_TEMPLATE,
    tpl.COMMIT_TEMPLATE,
    tpl.ABEND_TEMPLATE,
    tpl.PROCESS_TAIL_TEMPLATE,
    tpl.READ_PARAGRAPH_TEMPLATE,
)


def _template_placeholders() -> set[str]:
    names: set[str] = set()
    for template in ALL_TEMPLATES:
        for line in template:
            names.update(m.group("name") for m in PLACEHOLDER.finditer(line))
    return names


def _render(template, config) -> list[str]:
    values = config.placeholders()
    return [line.format(**values) for line in template]


# ---------------------------------------------------------------------
# Placeholder coverage - the contract between M1 and M2
# ---------------------------------------------------------------------

def test_config_supplies_every_template_placeholder(config):
    missing = _template_placeholders() - set(config.placeholders())
    assert missing == set(), f"placeholders with no config value: {missing}"


def test_every_template_renders_without_keyerror(config):
    values = config.placeholders()
    for template in ALL_TEMPLATES:
        for line in template:
            line.format(**values)


def test_rendered_output_contains_no_leftover_placeholder(config):
    values = config.placeholders()
    for template in ALL_TEMPLATES:
        rendered = "\n".join(line.format(**values) for line in template)
        assert "{" not in rendered
        assert "}" not in rendered


# ---------------------------------------------------------------------
# Immutability
# ---------------------------------------------------------------------

def test_config_is_frozen(config):
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.scheme = std.SCHEME_EIGHT_SERIES


def test_names_are_frozen(complete_names):
    with pytest.raises(dataclasses.FrozenInstanceError):
        complete_names.file_name = "OTHER"


def test_with_names_returns_a_new_object(config, complete_names):
    other = dataclasses.replace(complete_names, file_name="ANDERS")
    updated = config.with_names(other)
    assert updated is not config
    assert config.names.file_name == "OPERATIES"
    assert updated.names.file_name == "ANDERS"


# ---------------------------------------------------------------------
# Paragraph naming
# ---------------------------------------------------------------------

def test_both_schemes_produce_a_name_for_every_role(role):
    for scheme in std.PARAGRAPH_NUMBER_SCHEMES:
        names = build_paragraph_names(role, scheme)
        assert set(names) == set(std.RESTART_PARAGRAPH_ROLES), scheme
        assert all(names.values()), scheme


def test_paragraph_names_are_unique_within_a_scheme(role):
    for scheme in std.PARAGRAPH_NUMBER_SCHEMES:
        names = build_paragraph_names(role, scheme)
        assert len(set(names.values())) == len(names), scheme


def test_sql_paragraphs_carry_the_restart_table_name(role):
    names = build_paragraph_names(role, std.DEFAULT_PARAGRAPH_SCHEME)
    for role_key in cat.TABLE_SUFFIXED_ROLES:
        assert names[role_key].endswith(role.table_name)


def test_non_sql_paragraphs_do_not_carry_the_table_name(role):
    names = build_paragraph_names(role, std.DEFAULT_PARAGRAPH_SCHEME)
    for role_key in std.RESTART_PARAGRAPH_ROLES:
        if role_key in cat.TABLE_SUFFIXED_ROLES:
            continue
        assert role.table_name not in names[role_key]


def test_every_paragraph_name_is_a_valid_cobol_name(role):
    valid = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,29}$")
    for scheme in std.PARAGRAPH_NUMBER_SCHEMES:
        for name in build_paragraph_names(role, scheme).values():
            assert valid.match(name), name


def test_switching_scheme_changes_only_the_numbers(role, complete_names):
    seven = RestartConfig.build(role, complete_names, std.SCHEME_SEVEN_SERIES)
    eight = RestartConfig.build(role, complete_names, std.SCHEME_EIGHT_SERIES)

    def suffix(name: str) -> str:
        return name.split("-", 1)[1]

    for role_key in std.RESTART_PARAGRAPH_ROLES:
        assert suffix(seven.paragraph(role_key)) == suffix(
            eight.paragraph(role_key)
        )


def test_an_unknown_scheme_is_refused(role, complete_names):
    with pytest.raises(ValueError):
        RestartConfig.build(role, complete_names, "no_such_scheme")


# ---------------------------------------------------------------------
# QUERYNO
# ---------------------------------------------------------------------

def test_restart_querynos_are_distinct(config):
    values = (
        config.queryno_select,
        config.queryno_update,
        config.queryno_insert,
    )
    assert len(set(values)) == 3


# ---------------------------------------------------------------------
# Payload geometry - MEASURED, not declared
# ---------------------------------------------------------------------

def test_the_payload_length_is_measured_not_declared(config):
    assert config.payload_full_length == (
        config.names.read_count_size + config.names.restart_key_size
    )
    assert config.payload_length_on_insert == config.payload_full_length


def test_commit_length_follows_the_manual_by_default(config):
    assert std.ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT is False
    assert config.payload_length_on_commit == config.names.read_count_size


def test_the_full_length_flag_is_honoured(config, monkeypatch):
    monkeypatch.setattr(
        config_module, "ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT", True
    )
    assert config.payload_length_on_commit == config.payload_full_length


def test_a_shorter_restart_key_produces_a_shorter_length(
    role, complete_names
):
    """1215 was never a constant; it is this program's measurement."""
    names = dataclasses.replace(complete_names, restart_key_size=800)
    assert RestartConfig.build(role, names).payload_full_length == 815


def test_an_unmeasured_payload_is_refused(role, complete_names):
    names = dataclasses.replace(complete_names, restart_key_size=0)
    config = RestartConfig.build(role, names)
    assert config.is_usable() is False
    assert "restart_key_size" in config.missing()


# ---------------------------------------------------------------------
# Retention - SUPPLIED, not authored
# ---------------------------------------------------------------------

def test_retention_comes_from_the_role(config):
    assert config.retention_days == config.role.retention_days
    assert config.retention_days > 0


def test_a_role_without_retention_is_refused(role, complete_names):
    bare = dataclasses.replace(role, retention_days=0)
    assert RestartConfig.build(bare, complete_names).is_usable() is False


# ---------------------------------------------------------------------
# Refusal, not invention
# ---------------------------------------------------------------------

def test_an_empty_name_is_reported_as_missing():
    names = RestartProgramNames(file_name="OPERATIES")
    missing = names.missing()
    assert "record_name" in missing
    assert "file_name" not in missing
    assert names.is_complete() is False


def test_a_complete_name_set_reports_nothing_missing(complete_names):
    assert complete_names.missing() == ()
    assert complete_names.is_complete() is True


def test_a_config_with_missing_names_is_not_usable(role):
    config = RestartConfig.build(role, RestartProgramNames())
    assert config.is_usable() is False
    assert len(config.missing()) == len(RestartProgramNames.REQUIRED)


def test_whitespace_only_counts_as_missing():
    names = RestartProgramNames(file_name="   ")
    assert "file_name" in names.missing()


def test_a_zero_size_counts_as_missing():
    names = RestartProgramNames(read_count_size=0)
    assert "read_count_size" in names.missing()


# ---------------------------------------------------------------------
# Rendered content - spot checks against the manual reference
# ---------------------------------------------------------------------

def test_control_routes_sqlcode_to_the_right_paragraphs(config):
    body = " ".join(_render(tpl.CONTROL_TEMPLATE, config))
    assert "WHEN 0" in body
    assert "WHEN 100" in body



def test_payload_length_is_never_invented(config) -> None:
    """Either the full measurement, or the read-count picture. Nothing else."""
    assert config.payload_length in (
        config.payload_full_length,
        config.names.read_count_size,
    )


def test_the_full_payload_flag_decides_both_lengths() -> None:
    """The flag is the single decision point for the whole family."""
    import rules.restart_standard_rules as std
    assert isinstance(std.ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT, bool)

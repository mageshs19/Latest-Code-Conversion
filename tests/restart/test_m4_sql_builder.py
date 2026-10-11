# LOCATION: tests/restart/test_m4_sql_builder.py
# ACTION: CREATE NEW FILE
"""M4 contract tests: the three restart SQL paragraphs."""

from __future__ import annotations

import ast
import dataclasses
import inspect

import pytest

from catalogs import restart_paragraph_catalog as cat
from converter.generators.restart import restart_sql_builder as builder_module
from converter.generators.restart.restart_sql_builder import (
    RestartSqlBuilder,
    SqlParagraph,
    VERB_INSERT,
    VERB_SELECT,
    VERB_UPDATE,
)
from rules import restart_sql_templates as sqltpl
from rules import restart_standard_rules as std


@pytest.fixture
def builder(config):
    return RestartSqlBuilder(config)


@pytest.fixture
def paragraphs(builder):
    return {p.role: p for p in builder.build_all()}


def _joined(paragraph: SqlParagraph) -> str:
    return "\n".join(paragraph.lines())


def _bodies(paragraph: SqlParagraph) -> list[str]:
    return [line.strip() for line in paragraph.body if line.strip()]


def _when_other_block(bodies: list[str]) -> list[str]:
    start = bodies.index(sqltpl.WHEN_OTHER.strip()) + 1
    stop = bodies.index(sqltpl.EVALUATE_CLOSE)
    return bodies[start:stop]


# ---------------------------------------------------------------------
# Architecture contract
# ---------------------------------------------------------------------

def test_sql_templates_define_no_regex():
    source = inspect.getsource(sqltpl)
    assert "import re" not in source
    assert "re.compile" not in source


def test_sql_templates_all_is_sorted_and_complete():
    assert sqltpl.__all__ == sorted(sqltpl.__all__)
    assert len(sqltpl.__all__) == len(set(sqltpl.__all__))
    for name in sqltpl.__all__:
        assert hasattr(sqltpl, name), name


def test_catalog_all_is_sorted_and_free_of_duplicates():
    """A duplicated export hides the name that was meant to be added."""
    assert cat.__all__ == sorted(cat.__all__)
    assert len(cat.__all__) == len(set(cat.__all__))
    for name in cat.__all__:
        assert hasattr(cat, name), name


def test_sql_templates_assign_no_constant_twice():
    tree = ast.parse(inspect.getsource(sqltpl))
    seen: set[str] = set()
    duplicates: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                if target.id in seen:
                    duplicates.append(target.id)
                seen.add(target.id)
    assert duplicates == []


def test_sql_templates_carry_no_site_names():
    source = inspect.getsource(sqltpl).upper()
    for token in ("DCLDZ", "DZ01RST", "DZBFAR", "VMDZ", "NM_ID_RS"):
        assert token not in source, token


# ---------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------

def test_three_paragraphs_are_produced(paragraphs):
    assert set(paragraphs) == {
        std.ROLE_SELECT,
        std.ROLE_UPDATE,
        std.ROLE_INSERT,
    }


def test_each_paragraph_header_matches_the_config(config, paragraphs):
    for role, paragraph in paragraphs.items():
        assert paragraph.lines()[0] == f"{config.paragraph(role)}."


def test_each_paragraph_ends_with_a_lone_period(paragraphs):
    for paragraph in paragraphs.values():
        assert paragraph.body[-1] == sqltpl.PARAGRAPH_TERMINATOR_LINE


def test_no_scope_terminator_carries_a_period(paragraphs):
    """A period inside EVALUATE closes the scope and orphans END-EVALUATE."""
    for paragraph in paragraphs.values():
        for line in _bodies(paragraph):
            assert line not in ("END-EXEC.", "END-EVALUATE.")


def test_only_one_period_per_paragraph(paragraphs):
    for paragraph in paragraphs.values():
        lone = [l for l in _bodies(paragraph) if l == "."]
        assert len(lone) == 1


def test_each_paragraph_carries_a_debug_trace(config, paragraphs):
    for role, paragraph in paragraphs.items():
        assert config.paragraph(role) in paragraph.debug_trace


def test_exec_sql_is_balanced(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        assert body.count(sqltpl.EXEC_SQL_OPEN) == 1
        assert body.count(sqltpl.EXEC_SQL_CLOSE) == 1


def test_evaluate_is_balanced(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        assert body.count(sqltpl.EVALUATE_OPEN) == 1
        assert body.count(sqltpl.EVALUATE_CLOSE) == 1


def test_evaluate_follows_end_exec(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        assert body.index(sqltpl.EXEC_SQL_CLOSE) < body.index(
            sqltpl.EVALUATE_OPEN
        )


def test_paragraphs_are_frozen(paragraphs):
    with pytest.raises(dataclasses.FrozenInstanceError):
        paragraphs[std.ROLE_SELECT].name = "OTHER"


# ---------------------------------------------------------------------
# SQL-LOCATION
# ---------------------------------------------------------------------

def test_sql_location_is_off_by_default(paragraphs):
    """The manual reference writes it in the business paragraph only."""
    assert std.EMIT_SQL_LOCATION is False
    for paragraph in paragraphs.values():
        assert "SQL-LOCATION" not in _joined(paragraph)


def test_sql_location_is_never_written_in_the_error_branch():
    assert std.EMIT_SQL_LOCATION_IN_ERROR_BRANCH is False


@pytest.fixture
def located(config, monkeypatch):
    monkeypatch.setattr(builder_module, "EMIT_SQL_LOCATION", True)
    return {
        p.role: p for p in RestartSqlBuilder(config).build_all()
    }


def test_when_enabled_it_is_written_once_at_paragraph_entry(located):
    for paragraph in located.values():
        body = _bodies(paragraph)
        moves = [l for l in body if l.endswith("TO SQL-LOCATION")]
        assert len(moves) == 1
        assert body.index(moves[0]) < body.index(sqltpl.EXEC_SQL_OPEN)


def test_when_enabled_the_error_branch_does_not_restate_it(located):
    for paragraph in located.values():
        block = _when_other_block(_bodies(paragraph))
        assert not any(l.endswith("TO SQL-LOCATION") for l in block)


def test_when_enabled_the_value_is_the_paragraph_number(config, located):
    for role, paragraph in located.items():
        number = config.paragraph(role).split("-", 1)[0]
        assert f"MOVE {number} TO SQL-LOCATION" in _joined(paragraph)


# ---------------------------------------------------------------------
# SELECT
# ---------------------------------------------------------------------

def test_select_reads_every_column(config, paragraphs):
    text = _joined(paragraphs[std.ROLE_SELECT])
    for column in config.role.columns():
        assert column in text


def test_select_binds_every_host_field(config, paragraphs):
    text = _joined(paragraphs[std.ROLE_SELECT])
    group = config.role.host_record
    for field in config.role.host_fields():
        assert f":{group}.{field}" in text


def test_select_column_and_into_counts_match(config, paragraphs):
    """INTO hosts only. WHERE predicates also reference the group."""
    body = _bodies(paragraphs[std.ROLE_SELECT])
    marker = f":{config.role.host_record}."
    into_lines = [l for l in body if marker in l and "=" not in l]
    assert len(into_lines) == len(config.role.columns())


def test_select_references_the_group_once_per_column_and_key(
    config, paragraphs
):
    """Six INTO hosts plus three key predicates."""
    text = _joined(paragraphs[std.ROLE_SELECT])
    expected = len(config.role.columns()) + len(config.role.key_pairs())
    assert text.count(f":{config.role.host_record}.") == expected

def test_select_treats_not_found_as_normal(paragraphs):
    body = _bodies(paragraphs[std.ROLE_SELECT])
    assert f"WHEN {std.SQLCODE_OK}" in body
    assert f"WHEN {std.SQLCODE_NOT_FOUND}" in body


def test_select_names_the_table_in_from(config, paragraphs):
    assert f"FROM {config.role.table_name}" in _joined(
        paragraphs[std.ROLE_SELECT]
    )


def test_select_binds_the_payload_group_not_a_subfield(config, paragraphs):
    """DB2 binds the whole VARCHAR, not the -LEN / -TEXT subfields."""
    text = _joined(paragraphs[std.ROLE_SELECT])
    group = config.role.host_record
    assert f":{group}.{config.role.payload_group}" in text
    assert f":{group}.{config.role.payload_len_field}" not in text
    assert f":{group}.{config.role.payload_text_field}" not in text


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------

def test_update_sets_payload_and_status_only(config, paragraphs):
    body = _bodies(paragraphs[std.ROLE_UPDATE])
    set_lines = [l for l in body if l.startswith(("SET ", ", "))]
    assert len(set_lines) == 2
    joined = " ".join(set_lines)
    assert config.role.payload_column in joined
    assert config.role.status_column in joined


def test_update_never_sets_a_key_column(config, paragraphs):
    body = _bodies(paragraphs[std.ROLE_UPDATE])
    set_lines = [l for l in body if l.startswith(("SET ", ", "))]
    joined = " ".join(set_lines)
    for column, _field in config.role.key_pairs():
        assert column not in joined


def test_update_treats_not_found_as_an_error(paragraphs):
    body = _bodies(paragraphs[std.ROLE_UPDATE])
    assert f"WHEN {std.SQLCODE_NOT_FOUND}" not in body


def test_update_names_the_table(config, paragraphs):
    assert f"UPDATE {config.role.table_name}" in _joined(
        paragraphs[std.ROLE_UPDATE]
    )


# ---------------------------------------------------------------------
# INSERT
# ---------------------------------------------------------------------

def test_insert_lists_every_column(config, paragraphs):
    text = _joined(paragraphs[std.ROLE_INSERT])
    for column in config.role.columns():
        assert column in text


def test_insert_column_and_value_counts_match(config, paragraphs):
    text = _joined(paragraphs[std.ROLE_INSERT])
    expected = len(config.role.columns())
    assert text.count(f":{config.role.host_record}.") == expected


def test_insert_parentheses_are_balanced(paragraphs):
    text = _joined(paragraphs[std.ROLE_INSERT])
    assert text.count("(") == text.count(")")


def test_insert_has_a_values_keyword(paragraphs):
    body = _bodies(paragraphs[std.ROLE_INSERT])
    assert sqltpl.INSERT_VALUES_KEYWORD.strip() in body


def test_insert_names_the_table(config, paragraphs):
    assert f"INSERT INTO {config.role.table_name}" in _joined(
        paragraphs[std.ROLE_INSERT]
    )


def test_insert_has_no_where_clause(paragraphs):
    body = _bodies(paragraphs[std.ROLE_INSERT])
    assert not any(line.startswith("WHERE") for line in body)


# ---------------------------------------------------------------------
# WHERE
# ---------------------------------------------------------------------

@pytest.mark.parametrize(
    "role_key", [std.ROLE_SELECT, std.ROLE_UPDATE]
)
def test_the_key_predicates_are_complete(config, paragraphs, role_key):
    text = _joined(paragraphs[role_key])
    group = config.role.host_record
    for column, host in config.role.key_pairs():
        assert f"{column} = :{group}.{host}" in text


@pytest.mark.parametrize(
    "role_key", [std.ROLE_SELECT, std.ROLE_UPDATE]
)
def test_exactly_three_predicates(config, paragraphs, role_key):
    body = _bodies(paragraphs[role_key])
    predicates = [l for l in body if l.startswith(("WHERE ", "AND "))]
    assert len(predicates) == len(config.role.key_pairs())


@pytest.mark.parametrize(
    "role_key, verb",
    [
        (std.ROLE_SELECT, VERB_SELECT),
        (std.ROLE_UPDATE, VERB_UPDATE),
        (std.ROLE_INSERT, VERB_INSERT),
    ],
)
def test_the_error_text_names_the_verb_and_table(
    config, paragraphs, role_key, verb
):
    block = _when_other_block(_bodies(paragraphs[role_key]))
    assert any(
        verb in line and config.role.table_name in line for line in block
    )



# ---------------------------------------------------------------------
# QUERYNO
# ---------------------------------------------------------------------

def test_every_statement_carries_a_queryno(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        assert any(line.startswith("QUERYNO") for line in body)


def test_the_queryno_precedes_end_exec(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        queryno = next(
            i for i, l in enumerate(body) if l.startswith("QUERYNO")
        )
        assert queryno < body.index(sqltpl.EXEC_SQL_CLOSE)


def test_the_three_querynos_are_distinct(paragraphs):
    numbers = []
    for paragraph in paragraphs.values():
        line = next(
            l for l in _bodies(paragraph) if l.startswith("QUERYNO")
        )
        numbers.append(line.split()[1])
    assert len(set(numbers)) == 3


def test_each_queryno_matches_the_config(config, paragraphs):
    expected = {
        std.ROLE_SELECT: config.queryno_select,
        std.ROLE_UPDATE: config.queryno_update,
        std.ROLE_INSERT: config.queryno_insert,
    }
    for role, paragraph in paragraphs.items():
        assert f"QUERYNO {expected[role]}" in _joined(paragraph)


# ---------------------------------------------------------------------
# Error branch
# ---------------------------------------------------------------------



def test_perform_error_paragraph_is_the_last_statement(config, paragraphs):
    for paragraph in paragraphs.values():
        block = _when_other_block(_bodies(paragraph))
        assert block[-1] == f"PERFORM {config.names.error_paragraph}"


def test_the_error_branch_has_exactly_two_statements(paragraphs):
    """DISPLAY then PERFORM. Nothing else, by default."""
    for paragraph in paragraphs.values():
        assert len(_when_other_block(_bodies(paragraph))) == 2


def test_continue_is_the_normal_branch_body(paragraphs):
    for paragraph in paragraphs.values():
        body = _bodies(paragraph)
        assert sqltpl.BRANCH_CONTINUE.strip() in body


# ---------------------------------------------------------------------
# Messages and determinism
# ---------------------------------------------------------------------

def test_the_build_is_reported(builder):
    builder.build_all()
    assert any("generated 3 paragraph" in m for m in builder.messages)


def test_messages_are_reset_between_builds(builder):
    builder.build_all()
    first = len(builder.messages)
    builder.build_all()
    assert len(builder.messages) == first


def test_building_twice_produces_identical_output(config):
    first = RestartSqlBuilder(config).build_all()
    second = RestartSqlBuilder(config).build_all()
    assert first == second


def test_a_different_scheme_changes_only_the_paragraph_names(
    role, complete_names
):
    from converter.generators.restart.restart_config import RestartConfig

    seven = RestartSqlBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_SEVEN_SERIES)
    ).build_all()
    eight = RestartSqlBuilder(
        RestartConfig.build(role, complete_names, std.SCHEME_EIGHT_SERIES)
    ).build_all()

    for a, b in zip(seven, eight):
        assert a.role == b.role
        assert a.body == b.body
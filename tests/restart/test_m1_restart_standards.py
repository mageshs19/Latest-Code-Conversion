# LOCATION: tests/restart/test_m1_restart_standards.py
# ACTION: REPLACE ENTIRE FILE
"""M1 contract tests: the standards layer holds shape, not names.

CORRECTION - the payload geometry test asserted deleted constants

PAYLOAD_FULL_LENGTH, PAYLOAD_COUNTER_DIGITS and PAYLOAD_KEY_DIGITS no
longer exist. The checkpoint payload length is MEASURED from the two
restart-record pictures, and the retention value is SUPPLIED with the
restart DCLGEN role. Both tests below now assert the opposite of what
the old one did: that this layer owns NEITHER value.
"""

from __future__ import annotations

import ast
import inspect
import re

import pytest

from patterns import restart_patterns as pat
from rules import restart_standard_rules as std
from rules import restart_statement_templates as tpl


RULES_MODULES = (std, tpl)


# ---------------------------------------------------------------------
# Architecture contract
# ---------------------------------------------------------------------

@pytest.mark.parametrize("module", RULES_MODULES)
def test_rules_modules_define_no_regex(module):
    """rules/ is constants only. Regex belongs in patterns/."""
    source = inspect.getsource(module)
    assert "import re" not in source
    assert "re.compile" not in source


@pytest.mark.parametrize("module", RULES_MODULES + (pat,))
def test_modules_declare_all(module):
    """A duplicated export hides the name that was meant to be added."""
    assert isinstance(getattr(module, "__all__", None), list)
    assert module.__all__ == sorted(module.__all__)
    assert len(module.__all__) == len(set(module.__all__))
    for name in module.__all__:
        assert hasattr(module, name), name


@pytest.mark.parametrize("module", RULES_MODULES + (pat,))
def test_no_constant_assigned_twice(module):
    """A second assignment silently overrides the reviewed value."""
    tree = ast.parse(inspect.getsource(module))
    seen: set[str] = set()
    duplicates: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id in seen:
                duplicates.append(target.id)
            seen.add(target.id)
    assert duplicates == []


def test_patterns_module_defines_no_business_constants():
    source = inspect.getsource(pat)
    assert "_RULES" not in source
    assert "TEMPLATE" not in source


# ---------------------------------------------------------------------
# Values this layer must NOT own
# ---------------------------------------------------------------------

def test_the_standards_layer_owns_no_retention_value():
    """The retention column is site data, supplied with the role."""
    source = inspect.getsource(std)
    assert "RETENTION_DAYS" not in source
    assert std.REQUIRE_RETENTION_FROM_METADATA is True


def test_the_standards_layer_owns_no_payload_length():
    """The length is measured from the source, never declared here."""
    source = inspect.getsource(std)
    assert "PAYLOAD_FULL_LENGTH" not in source
    assert "1215" not in source
    assert "1200" not in source


# ---------------------------------------------------------------------
# Policy values
# ---------------------------------------------------------------------

def test_status_values_are_distinct_single_characters():
    assert std.STATUS_INCOMPLETE != std.STATUS_COMPLETE
    assert len(std.STATUS_INCOMPLETE) == 1
    assert len(std.STATUS_COMPLETE) == 1


def test_commit_threshold_fires_on_the_frequency_record():
    assert std.COMMIT_TEST_THRESHOLD == std.COMMIT_FREQUENCY - 1


def test_restart_is_update_only():
    assert std.APPLIES_TO_UPDATE_PROGRAMS is True
    assert std.APPLIES_TO_RETRIEVAL_PROGRAMS is False


def test_sqlcode_routing_values():
    assert std.SQLCODE_OK == 0
    assert std.SQLCODE_NOT_FOUND == 100


def test_sql_location_is_never_restated_in_the_error_branch():
    """The reference writes it once, at paragraph entry."""
    assert std.EMIT_SQL_LOCATION_IN_ERROR_BRANCH is False


def test_the_commit_length_flag_defaults_to_the_manual():
    assert std.ENFORCE_FULL_PAYLOAD_LENGTH_ON_COMMIT is False


# ---------------------------------------------------------------------
# Paragraph roles and schemes
# ---------------------------------------------------------------------

def test_every_scheme_covers_every_role():
    for scheme, mapping in std.PARAGRAPH_NUMBER_SCHEMES.items():
        assert set(mapping) == set(std.RESTART_PARAGRAPH_ROLES), scheme


def test_default_scheme_exists():
    assert std.DEFAULT_PARAGRAPH_SCHEME in std.PARAGRAPH_NUMBER_SCHEMES


def test_every_scheme_number_is_covered_by_a_skip_prefix():
    prefixes = set(std.RESTART_PARAGRAPH_PREFIXES)
    for mapping in std.PARAGRAPH_NUMBER_SCHEMES.values():
        for number in mapping.values():
            assert f"{number}-" in prefixes, number


# ---------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------

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


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_templates_are_tuples_of_strings(template):
    assert isinstance(template, tuple)
    assert all(isinstance(line, str) for line in template)


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_templates_carry_no_hardcoded_names(template):
    """No DCLGEN group, table, program or host variable may appear."""
    body = " ".join(template).upper()
    for token in ("DCLDZ", "DZ01RST", "DZBFAR", "VMDZ", "WS-TELLER",
                  "WS-NB-", "VMDZ205I", "OPERATIES"):
        assert token not in body, token


@pytest.mark.parametrize("template", ALL_TEMPLATES)
def test_placeholders_are_snake_case(template):
    for line in template:
        for match in PLACEHOLDER.finditer(line):
            assert match.group("name").islower()


def test_main_flow_order_is_fixed():
    body = [line for line in tpl.MAIN_FLOW_TEMPLATE if line]
    assert body[0].startswith("OPEN INPUT")
    assert body[-1] == "STOP RUN."
    assert body[-2].startswith("CLOSE")
    control = next(i for i, l in enumerate(body) if "{control_paragraph}" in l)
    read = next(i for i, l in enumerate(body) if "{read_paragraph}" in l)
    process = next(i for i, l in enumerate(body) if "{process_paragraph}" in l)
    commit = next(i for i, l in enumerate(body) if "{commit_paragraph}" in l)
    assert control < read < process < commit


def test_restart_found_blocks_a_completed_run():
    body = " ".join(tpl.RESTART_FOUND_TEMPLATE)
    assert "{abend_paragraph}" in body
    assert "{read_count_field}" in body
    assert "TIMES" in body
    assert "{read_paragraph}" in body


def test_write_restart_initialises_the_key_and_zeroes_the_counter():
    body = " ".join(tpl.WRITE_RESTART_TEMPLATE)
    assert "INITIALIZE {restart_key_field}." in body
    assert "MOVE 0" in body
    assert "{payload_length_insert}" in body


def test_commit_saves_counter_and_key_before_updating():
    body = tpl.COMMIT_TEMPLATE
    counter = next(i for i, l in enumerate(body) if "{read_count_field}" in l)
    key = next(i for i, l in enumerate(body) if "{input_save_area}" in l)
    update = next(i for i, l in enumerate(body) if "{update_paragraph}" in l)
    assert counter < update
    assert key < update


def test_read_paragraph_increments_both_counters():
    body = " ".join(tpl.READ_PARAGRAPH_TEMPLATE)
    assert "ADD +1 TO {commit_counter}" in body
    assert "ADD +1 TO {input_counter}" in body
    assert "MOVE {record_name} TO {input_save_area}" in body


# ---------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------

def test_open_input_captures_the_file_name():
    assert pat.OPEN_INPUT_PATTERN.match("OPEN INPUT OPERATIES.").group(
        "file"
    ) == "OPERATIES"


def test_perform_until_captures_paragraph_and_condition():
    match = pat.PERFORM_UNTIL_PATTERN.match(
        "PERFORM VERWERKING UNTIL VMDZ205I-EOF."
    )
    assert match.group("paragraph") == "VERWERKING"
    assert match.group("condition") == "VMDZ205I-EOF"


def test_perform_until_supports_the_span_form():
    match = pat.PERFORM_UNTIL_PATTERN.match(
        "PERFORM BEHANDELING THRU BEHANDELING-EXIT UNTIL SW-EOC."
    )
    assert match.group("paragraph") == "BEHANDELING"


def test_read_into_captures_file_and_record():
    match = pat.READ_INTO_PATTERN.match("READ OPERATIES INTO VMDZ205I")
    assert match.group("file") == "OPERATIES"
    assert match.group("record") == "VMDZ205I"


def test_level_88_captures_name_and_value():
    match = pat.LEVEL_88_PATTERN.match("88 VMDZ205I-EOF VALUE 'Y'.")
    assert match.group("name") == "VMDZ205I-EOF"
    assert match.group("value") == "Y"


def test_the_77_picture_pattern_actually_matches():
    """It once read X$8$, where the dollar sign is an anchor."""
    match = pat.LEVEL_77_WITH_VALUE_PATTERN.match(
        "77 USERABEN PIC X(8) VALUE 'USERABEN'."
    )
    assert match is not None
    assert match.group("name") == "USERABEN"
    assert match.group("size") == "8"
    assert match.group("value") == "USERABEN"


@pytest.mark.parametrize(
    "clause, size",
    [
        ("PIC 9(15)", "15"),
        ("PIC X(1200)", "1200"),
        ("PIC 9(7) COMP-3", "7"),
        ("PICTURE IS X(4)", "4"),
    ],
)
def test_picture_size_is_measured(clause, size):
    assert pat.PICTURE_SIZE_PATTERN.match(clause).group("size") == size


def test_a_picture_without_a_repeat_has_no_size():
    assert pat.PICTURE_SIZE_PATTERN.match("PIC XXX") is None


def test_elementary_item_captures_name_and_picture():
    match = pat.ELEMENTARY_ITEM_PATTERN.match("03 KY-RESTART PIC X(1200).")
    assert match.group("name") == "KY-RESTART"
    assert match.group("picture").startswith("X(1200)")


def test_the_paragraph_number_is_captured():
    assert pat.PARAGRAPH_NUMBER_PATTERN.match(
        "700-SELECT-DZ01RSTV"
    ).group("number") == "700"


def test_a_paragraph_without_a_number_has_none():
    assert pat.PARAGRAPH_NUMBER_PATTERN.match("VERWERKING") is None


@pytest.mark.parametrize(
    "line",
    [
        "EXEC SQL INCLUDE SQLERROR END-EXEC.",
        "INCLUDE SQLERROR",
    ],
)
def test_the_include_pattern_accepts_both_shapes(line):
    assert pat.SQL_INCLUDE_PATTERN.match(line).group("name") == "SQLERROR"


def test_double_period_is_detected():
    assert pat.DOUBLE_PERIOD_PATTERN.search("MOVE 0 TO WS-TELLER..")
    assert not pat.DOUBLE_PERIOD_PATTERN.search("MOVE 0 TO WS-TELLER.")


def test_trailing_sequence_leak_is_detected():
    match = pat.TRAILING_SEQUENCE_LEAK_PATTERN.search(
        "EXEC SQL INCLUDE DZ01RSTV END-EXEC.008300"
    )
    assert match.group("leak") == "008300"


def test_orphan_scope_terminator_is_detected():
    assert pat.ORPHAN_SCOPE_TERMINATOR_PATTERN.match("END-IF.")
    assert not pat.ORPHAN_SCOPE_TERMINATOR_PATTERN.match("END-IF ALPHA.")


def test_paragraph_header_rejects_a_statement():
    assert pat.PARAGRAPH_HEADER_PATTERN.match("700-RESTART-CONTROL.")
    assert not pat.PARAGRAPH_HEADER_PATTERN.match("MOVE 0 TO WS-TELLER.")
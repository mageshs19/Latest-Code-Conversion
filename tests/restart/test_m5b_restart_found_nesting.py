# LOCATION: tests/restart/test_m5b_restart_found_nesting.py
# ACTION: CREATE NEW FILE
"""The restart_found paragraph's BLOCK STRUCTURE, not just its tokens.

WHY THIS FILE EXISTS

test_m5_flow_builder.py asserts presence:

    "PERFORM {read_count_field} OF " in text
    "END-PERFORM" in text
    config.names.input_counter in text

All three passed while the counter MOVE sat AFTER END-PERFORM, outside
the replay loop. Presence is not structure. These tests assert the index
order of the four markers, so the loop body can never silently lose a
statement again.

Asserted against the TEMPLATE CONSTANTS, not a rendered paragraph, so no
RestartConfig is required and BOTH owners are policed by one suite. Two
copies of one rule is how the previous defect survived review.
"""

from __future__ import annotations

import pytest

from rules import restart_statement_templates as tpl
from rules import update_standard_generator_templates as legacy


def _index(lines: list[str], needle: str) -> int:
    return next(i for i, line in enumerate(lines) if needle in line)


# ---------------------------------------------------------------- #
# The metadata-driven template (7-series, live)
# ---------------------------------------------------------------- #
@pytest.fixture
def body() -> list[str]:
    return list(tpl.RESTART_FOUND_TEMPLATE)


def test_the_loop_opens_before_the_reader_is_performed(body) -> None:
    assert _index(body, "TIMES") < _index(body, "{read_paragraph}")


def test_the_counter_move_is_inside_the_loop(body) -> None:
    """The defect this file exists for."""
    loop = _index(body, "TIMES")
    move = _index(body, "{input_counter}")
    close = _index(body, "END-PERFORM")
    assert loop < move < close


def test_the_loop_closes_before_the_if(body) -> None:
    assert _index(body, "END-PERFORM") < _index(body, "END-IF.")


def test_each_scope_is_closed_exactly_once(body) -> None:
    joined = " ".join(body)
    assert joined.count("END-PERFORM") == 1
    assert joined.count("END-IF") == 1


def test_the_paragraph_ends_on_a_terminated_sentence(body) -> None:
    """A bare scope terminator runs into the next paragraph header."""
    assert body[-1].rstrip().endswith(".")


def test_both_obligations_survive(body) -> None:
    """Block a completed run; reposition a resumed one."""
    joined = " ".join(body)
    assert "{abend_paragraph}" in joined
    assert "{read_count_field}" in joined


# ---------------------------------------------------------------- #
# The legacy template (8-series) must agree, or it will drift back
# ---------------------------------------------------------------- #
@pytest.fixture
def legacy_body() -> list[str]:
    return str(legacy.RESTART_FOUND_TEMPLATE).splitlines()


def test_the_legacy_copy_nests_the_move_the_same_way(legacy_body) -> None:
    loop = _index(legacy_body, "TIMES")
    move = _index(legacy_body, "{input_counter}")
    close = _index(legacy_body, "END-PERFORM")
    assert loop < move < close


def test_the_legacy_copy_closes_each_scope_once(legacy_body) -> None:
    joined = " ".join(legacy_body)
    assert joined.count("END-PERFORM") == 1
    assert joined.count("END-IF") == 1
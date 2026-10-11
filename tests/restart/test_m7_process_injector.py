# LOCATION: tests/restart/test_m7_process_injector.py
# ACTION: CREATE NEW FILE
"""M7 contract tests: the business processing paragraph.

The generated paragraph carried an orphan END-IF that stopped the
program compiling, and an EXEC SQL COMMIT that fired once per record
instead of once per hundred. Neither can survive this pass.
"""

from __future__ import annotations

import dataclasses

import pytest

from converter.composers.restart.process_paragraph_injector import (
    ProcessParagraphInjector,
)
from converter.generators.restart.restart_config import (
    RestartConfig,
    RestartProgramNames,
)
from rules import restart_standard_rules as std

BUSINESS = [
    "MOVE '1815' TO CT-TGDSERV-479BFAR OF DCLDZBFARTV",
    "MOVE TS-TIMESTAMP TO TS-UPDATE-479BFAR OF DCLDZBFARTV",
    "PERFORM 1100-UPDATE-VMBFAR",
]

COMMIT_BLOCK = [
    "EXEC SQL",
    "COMMIT",
    "END-EXEC.",
]


@pytest.fixture
def injector(config):
    return ProcessParagraphInjector(config)


def _logical(lines):
    return [" ".join(str(l).upper().split()) for l in lines if str(l).strip()]


# ---------------------------------------------------------------------
# The tail
# ---------------------------------------------------------------------

def test_the_commit_test_is_appended(config, injector):
    body = _logical(injector.inject(BUSINESS))
    expected = (
        f"IF {config.names.commit_counter} > {std.COMMIT_TEST_THRESHOLD}"
    )
    assert expected in body


def test_the_commit_paragraph_is_performed(config, injector):
    body = _logical(injector.inject(BUSINESS))
    assert f"PERFORM {config.paragraph(std.ROLE_COMMIT)}" in body


def test_the_tail_read_is_appended(config, injector):
    body = _logical(injector.inject(BUSINESS))
    assert body[-1] == f"PERFORM {config.names.read_paragraph}."


def test_the_commit_test_is_closed(injector):
    body = _logical(injector.inject(BUSINESS))
    assert "END-IF." in body


def test_the_commit_test_precedes_the_tail_read(config, injector):
    body = _logical(injector.inject(BUSINESS))
    test = next(i for i, l in enumerate(body) if l.startswith("IF "))
    read = next(
        i for i, l in enumerate(body)
        if l == f"PERFORM {config.names.read_paragraph}."
    )
    assert test < read


def test_the_business_lines_are_preserved(injector):
    body = _logical(injector.inject(BUSINESS))
    for line in _logical(BUSINESS):
        assert line in body


def test_the_business_lines_keep_their_order(injector):
    body = _logical(injector.inject(BUSINESS))
    positions = [body.index(line) for line in _logical(BUSINESS)]
    assert positions == sorted(positions)


def test_the_injection_is_reported(injector):
    injector.inject(BUSINESS)
    assert any("appended the commit test" in m for m in injector.messages)


def test_no_placeholder_survives(injector):
    text = "\n".join(injector.inject(BUSINESS))
    assert "{" not in text
    assert "}" not in text


# ---------------------------------------------------------------------
# Orphan scope terminators
# ---------------------------------------------------------------------

def test_an_orphan_end_if_is_removed(injector):
    body = _logical(injector.inject(BUSINESS + ["END-IF."]))
    assert body.count("END-IF.") == 1  # only the one the tail opened


def test_the_orphan_removal_is_reported(injector):
    injector.inject(BUSINESS + ["END-IF."])
    assert any("orphan END-IF" in m for m in injector.messages)


def test_a_matched_end_if_is_kept(injector):
    lines = [
        "IF DA-CCYYMMDD = ZERO",
        "   MOVE 00010101 TO DA-CCYYMMDD",
        "END-IF",
    ]
    body = _logical(injector.inject(lines))
    assert "IF DA-CCYYMMDD = ZERO" in body
    assert body.count("END-IF") >= 1


def test_a_one_line_if_is_balanced(injector):
    lines = ["IF A = B MOVE C TO D END-IF"]
    injector.inject(lines)
    assert not any("orphan" in m for m in injector.messages)


def test_an_orphan_end_evaluate_is_removed(injector):
    body = _logical(injector.inject(BUSINESS + ["END-EVALUATE."]))
    assert "END-EVALUATE." not in body


def test_a_matched_end_evaluate_is_kept(injector):
    lines = [
        "EVALUATE SQLCODE",
        "WHEN 0",
        "CONTINUE",
        "END-EVALUATE",
    ]
    body = _logical(injector.inject(lines))
    assert "END-EVALUATE" in body


def test_an_untracked_terminator_is_left_alone(injector):
    body = _logical(injector.inject(BUSINESS + ["END-READ."]))
    assert "END-READ." in body
    assert any("not tracked" in m for m in injector.messages)


# ---------------------------------------------------------------------
# Per-record COMMIT
# ---------------------------------------------------------------------

def test_the_split_commit_block_is_removed(injector):
    body = _logical(injector.inject(BUSINESS + COMMIT_BLOCK))
    assert "COMMIT" not in body
    assert "EXEC SQL" not in body


def test_the_one_line_commit_block_is_removed(injector):
    body = _logical(
        injector.inject(BUSINESS + ["EXEC SQL COMMIT END-EXEC."])
    )
    assert "EXEC SQL COMMIT END-EXEC." not in body


def test_the_commit_removal_is_reported(injector):
    injector.inject(BUSINESS + COMMIT_BLOCK)
    assert any("per-record COMMIT" in m for m in injector.messages)


def test_business_sql_is_never_removed(injector):
    lines = [
        "EXEC SQL",
        "UPDATE DZBFARTV",
        "SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR",
        "WHERE NR_IDFMAS_479BFAR = :DCLDZBFARTV.NR-IDFMAS-479BFAR",
        "END-EXEC",
    ]
    body = _logical(injector.inject(lines))
    for line in _logical(lines):
        assert line in body
    assert not any("per-record COMMIT" in m for m in injector.messages)


def test_an_unterminated_exec_block_is_left_alone(injector):
    lines = ["EXEC SQL", "COMMIT"]
    body = _logical(injector.inject(lines))
    assert "EXEC SQL" in body
    assert "COMMIT" in body


def test_two_commit_blocks_are_both_removed(injector):
    body = _logical(
        injector.inject(BUSINESS + COMMIT_BLOCK + COMMIT_BLOCK)
    )
    assert "COMMIT" not in body
    assert any("removed 2 per-record COMMIT" in m for m in injector.messages)


# ---------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------

def test_injecting_twice_appends_one_tail(injector):
    once = injector.inject(BUSINESS)
    twice = injector.inject(once)
    assert _logical(twice) == _logical(once)


def test_the_second_pass_reports_that_it_did_nothing(injector):
    once = injector.inject(BUSINESS)
    injector.inject(once)
    assert any("already present" in m for m in injector.messages)


def test_a_third_pass_is_still_stable(injector):
    once = injector.inject(BUSINESS)
    twice = injector.inject(once)
    thrice = injector.inject(twice)
    assert _logical(thrice) == _logical(once)


# ---------------------------------------------------------------------
# Combined repair - the shape actually generated
# ---------------------------------------------------------------------

def test_the_generated_shape_is_fully_repaired(config, injector):
    broken = BUSINESS + COMMIT_BLOCK + ["END-IF."]
    body = _logical(injector.inject(broken))

    assert "COMMIT" not in body
    assert body.count("END-IF.") == 1
    assert f"PERFORM {config.paragraph(std.ROLE_COMMIT)}" in body
    assert body[-1] == f"PERFORM {config.names.read_paragraph}."


def test_the_repair_reports_every_decision(injector):
    injector.inject(BUSINESS + COMMIT_BLOCK + ["END-IF."])
    joined = " ".join(injector.messages)
    assert "orphan END-IF" in joined
    assert "per-record COMMIT" in joined
    assert "appended the commit test" in joined


# ---------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------

def test_an_unusable_config_changes_nothing(role):
    injector = ProcessParagraphInjector(
        RestartConfig.build(role, RestartProgramNames())
    )
    assert injector.inject(BUSINESS) == BUSINESS
    assert injector.messages


def test_a_missing_counter_changes_nothing(role, complete_names):
    names = dataclasses.replace(complete_names, commit_counter="")
    injector = ProcessParagraphInjector(RestartConfig.build(role, names))
    assert injector.inject(BUSINESS) == BUSINESS
    assert any("commit_counter" in m for m in injector.messages)


def test_an_empty_paragraph_is_safe(injector):
    body = _logical(injector.inject([]))
    assert body
    assert body[-1].startswith("PERFORM ")


def test_none_is_safe(injector):
    assert injector.inject(None)


# ---------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------

def test_messages_are_reset_between_runs(injector):
    injector.inject(BUSINESS)
    first = len(injector.messages)
    injector.inject(BUSINESS)
    assert len(injector.messages) == first


def test_the_tail_is_stable(injector):
    assert injector.tail() == injector.tail()

def test_a_scope_emptied_by_the_commit_removal_is_removed(injector):
    lines = BUSINESS + ["IF CTR-REC > 99"] + COMMIT_BLOCK + ["END-IF."]
    body = _logical(injector.inject(lines))
    assert "IF CTR-REC > 99" not in body
    assert body.count("END-IF.") == 1          # only the appended tail's


def test_a_scope_with_a_body_is_never_touched(injector):
    lines = BUSINESS + ["IF CTR-REC > 99", "MOVE 1 TO X", "END-IF."]
    body = _logical(injector.inject(lines))
    assert "IF CTR-REC > 99" in body
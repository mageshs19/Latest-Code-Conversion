# LOCATION: tests/restart/test_m9a_legacy_cleanup.py
# ACTION: CREATE NEW FILE
"""M9a contract tests: removing the previous restart mechanism.

Two failure modes, opposite in direction:

    removing too little - a second run leaves two 700-RESTART-CONTROL
    paragraphs and COBOL performs the stale one

    removing too much - a legacy declaration the program still reads is
    deleted and the program no longer compiles
"""

from __future__ import annotations

import pytest

from converter.composers.restart.legacy_restart_cleanup import (
    LegacyRestartCleanup,
)
from rules import restart_standard_rules as std
from rules.restart_cleanup_rules import PARAGRAPH_SPAN_LIMIT


@pytest.fixture
def cleanup(config, line_utils):
    return LegacyRestartCleanup(config, line_utils)


def _logical(lines):
    return [" ".join(str(l).upper().split()) for l in lines if str(l).strip()]


def _program(data: list[str], procedure: list[str]) -> list[str]:
    return (
        ["DATA DIVISION.", "WORKING-STORAGE SECTION."]
        + data
        + ["PROCEDURE DIVISION."]
        + procedure
    )


# ---------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------

def test_legacy_tokens_are_detected(cleanup):
    assert cleanup.detect(["77 SW-RECAB PIC X VALUE 'Y'."]) is True
    assert any("SW-RECAB" in m for m in cleanup.messages)


def test_a_clean_program_reports_nothing_found(cleanup):
    assert cleanup.detect(["MOVE A TO B."]) is False
    assert any("no legacy restart token" in m for m in cleanup.messages)


def test_every_detection_token_is_recognised(cleanup):
    from rules.restart_cleanup_rules import (
        LEGACY_RESTART_DETECTION_TOKENS,
    )

    for token in LEGACY_RESTART_DETECTION_TOKENS:
        assert cleanup.detect([f"MOVE {token} TO X."]) is True


def test_a_comment_does_not_trigger_detection(cleanup):
    assert cleanup.detect(["      * SW-RECAB WAS USED HERE"]) is False


# ---------------------------------------------------------------------
# Paragraph removal
# ---------------------------------------------------------------------

def test_a_restart_paragraph_is_removed(config, cleanup):
    name = config.paragraph(std.ROLE_CONTROL)
    lines = [
        "PROCEDURE DIVISION.",
        "    STOP RUN.",
        f"{name}.",
        "    MOVE 0 TO WS-TELLER.",
        "VERWERKING.",
        "    CONTINUE.",
    ]
    body = _logical(cleanup.remove_paragraphs(lines))
    assert f"{name}." not in body
    assert "MOVE 0 TO WS-TELLER." not in body


def test_the_following_paragraph_survives(config, cleanup):
    name = config.paragraph(std.ROLE_CONTROL)
    lines = [
        "PROCEDURE DIVISION.",
        f"{name}.",
        "    MOVE 0 TO WS-TELLER.",
        "VERWERKING.",
        "    CONTINUE.",
    ]
    body = _logical(cleanup.remove_paragraphs(lines))
    assert "VERWERKING." in body
    assert "CONTINUE." in body


def test_every_restart_role_is_removed(config, cleanup):
    lines = ["PROCEDURE DIVISION."]
    for role in std.RESTART_PARAGRAPH_ROLES:
        lines += [f"{config.paragraph(role)}.", "    CONTINUE."]
    lines += ["VERWERKING.", "    CONTINUE."]

    body = _logical(cleanup.remove_paragraphs(lines))
    for role in std.RESTART_PARAGRAPH_ROLES:
        assert f"{config.paragraph(role)}." not in body
    assert "VERWERKING." in body


def test_a_business_paragraph_is_never_removed(cleanup):
    lines = ["PROCEDURE DIVISION.", "VERWERKING.", "    CONTINUE."]
    assert _logical(cleanup.remove_paragraphs(lines)) == _logical(lines)


def test_an_absent_paragraph_is_reported(config, cleanup):
    cleanup.remove_paragraphs(["PROCEDURE DIVISION.", "VERWERKING."])
    assert any("not present" in m for m in cleanup.messages)


def test_the_removal_is_reported_with_a_line_count(config, cleanup):
    name = config.paragraph(std.ROLE_COMMIT)
    cleanup.remove_paragraphs(
        ["PROCEDURE DIVISION.", f"{name}.", "    CONTINUE.", "X-PARA."]
    )
    assert any("removed paragraph" in m and name in m for m in cleanup.messages)


def test_a_paragraph_ending_at_a_section_is_bounded(config, cleanup):
    name = config.paragraph(std.ROLE_ABEND)
    lines = [
        "PROCEDURE DIVISION.",
        f"{name}.",
        "    CALL USERABEN.",
        "SOME SECTION.",
        "    CONTINUE.",
    ]
    body = _logical(cleanup.remove_paragraphs(lines))
    assert "SOME SECTION." in body
    assert "CALL USERABEN." not in body


def test_an_over_long_span_is_refused(config, cleanup):
    name = config.paragraph(std.ROLE_CONTROL)
    lines = (
        ["PROCEDURE DIVISION.", f"{name}."]
        + ["    CONTINUE."] * (PARAGRAPH_SPAN_LIMIT + 5)
    )
    body = _logical(cleanup.remove_paragraphs(lines))
    assert f"{name}." in body
    assert any("spans more than" in m for m in cleanup.messages)


# ---------------------------------------------------------------------
# Declaration removal
# ---------------------------------------------------------------------

def test_an_unreferenced_legacy_declaration_is_removed(cleanup):
    lines = _program(
        ["77 SW-RECAB PIC X(1) VALUE 'Y'."],
        ["    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert not any("SW-RECAB" in l for l in body)
    assert any("removed unreferenced" in m for m in cleanup.messages)


def test_a_referenced_legacy_declaration_survives(cleanup):
    lines = _program(
        ["77 CTR-REC PIC 9(9) VALUE 0."],
        ["    ADD 1 TO CTR-REC.", "    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert any("77 CTR-REC" in l for l in body)
    assert any("still referenced" in m for m in cleanup.messages)


def test_the_legacy_abend_marker_is_removed(cleanup):
    lines = _program(
        ["77 STOP01 PIC X(50) VALUE '##&&VM1BD567-STOP01 ACCES DB'."],
        ["    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert not any("STOP01" in l for l in body)
    assert any("abend marker" in m for m in cleanup.messages)


def test_a_wrapped_marker_is_removed_whole(cleanup):
    lines = _program(
        [
            "77 STOP01 PIC X(50)",
            "VALUE '##&&VM1BD567-STOP01 ACCES DB'.",
        ],
        ["    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert not any("STOP01" in l for l in body)
    assert not any("##&&" in l for l in body)


def test_a_referenced_marker_survives(cleanup):
    lines = _program(
        ["77 STOP01 PIC X(50) VALUE '##&&SOMETHING'."],
        ["    DISPLAY STOP01.", "    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert any("STOP01" in l for l in body)


def test_an_ordinary_declaration_is_never_removed(cleanup):
    lines = _program(
        ["77 USERABEN PIC X(8) VALUE 'USERABEN'."],
        ["    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert any("USERABEN" in l for l in body)


def test_a_program_without_a_procedure_division_is_untouched(cleanup):
    lines = ["DATA DIVISION.", "77 SW-RECAB PIC X(1) VALUE 'Y'."]
    assert cleanup.remove_declarations(lines) == lines
    assert any("no PROCEDURE DIVISION" in m for m in cleanup.messages)


def test_the_procedure_division_is_never_edited(cleanup):
    lines = _program(
        ["77 SW-RECAB PIC X(1) VALUE 'Y'."],
        ["    MOVE A TO B.", "    STOP RUN."],
    )
    body = _logical(cleanup.remove_declarations(lines))
    assert "MOVE A TO B." in body
    assert "STOP RUN." in body


# ---------------------------------------------------------------------
# Combined, and idempotent
# ---------------------------------------------------------------------

def test_clean_removes_paragraphs_and_declarations(config, cleanup):
    name = config.paragraph(std.ROLE_CONTROL)
    lines = _program(
        ["77 SW-RECAB PIC X(1) VALUE 'Y'."],
        ["    STOP RUN.", f"{name}.", "    CONTINUE.", "VERWERKING."],
    )
    body = _logical(cleanup.clean(lines))
    assert not any("SW-RECAB" in l for l in body)
    assert f"{name}." not in body
    assert "VERWERKING." in body


def test_cleaning_twice_is_stable(config, cleanup):
    name = config.paragraph(std.ROLE_CONTROL)
    lines = _program(
        ["77 SW-RECAB PIC X(1) VALUE 'Y'."],
        ["    STOP RUN.", f"{name}.", "    CONTINUE."],
    )
    once = cleanup.clean(lines)
    twice = cleanup.clean(once)
    assert _logical(twice) == _logical(once)


def test_cleaning_a_clean_program_changes_nothing(cleanup):
    lines = _program(
        ["77 USERABEN PIC X(8) VALUE 'USERABEN'."],
        ["    STOP RUN.", "VERWERKING.", "    CONTINUE."],
    )
    assert cleanup.clean(lines) == lines


def test_messages_are_reset_between_runs(cleanup):
    lines = _program(["77 SW-RECAB PIC X(1) VALUE 'Y'."], ["    STOP RUN."])
    cleanup.clean(lines)
    first = len(cleanup.messages)
    cleanup.clean(lines)
    assert len(cleanup.messages) == first


def test_empty_input_is_safe(cleanup):
    assert cleanup.clean([]) == []
    assert cleanup.clean(None) == []
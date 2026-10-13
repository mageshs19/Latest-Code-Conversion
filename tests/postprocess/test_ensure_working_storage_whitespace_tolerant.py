# LOCATION: tests/postprocess/test_ensure_working_storage_whitespace_tolerant.py
# ACTION: REPLACE ENTIRE FILE
"""Regression for NEW-2c: a group declared by a DIFFERENT generator,
with different internal spacing, must still be recognised as present.

CORRECTION: the class under test is StorageWsInjector - a mixin that
depends on its host class for self.line_utils / self.generator, not a
standalone UpdateStorageIncludeManager (that name does not exist in
this module). Constructed directly here with a minimal line_utils
stand-in, since the existence check being tested only needs
.lines() and .logical().
"""
from __future__ import annotations

from converter.postprocess.storage_include.storage_ws_injector import (
    StorageWsInjector,
)


class _LineUtils:
    """Minimal stand-in: fixed-format columns 8-72, stripped."""

    def lines(self, text: str) -> list[str]:
        return str(text or "").splitlines()

    def logical(self, line: str) -> str:
        text = str(line or "")
        if len(text) > 7 and text[:6].strip().isdigit():
            return text[7:72].rstrip()
        return text.strip()

    def logical_contains(self, cobol_text: str, expected: str) -> bool:
        target = str(expected or "").strip().upper()
        if not target:
            return False
        for line in self.lines(cobol_text):
            if target in self.logical(line).upper():
                return True
        return False


def _injector():
    injector = StorageWsInjector()
    injector.line_utils = _LineUtils()
    return injector


TWO_SPACE_SOURCE = "\n".join([
    "000100 DATA DIVISION.",
    "000200 WORKING-STORAGE SECTION.",
    "000300 01  WS-SWITCHES.",
    "000400     02  SW-VMDZ205I            PIC X     VALUE 'N'.",
    "000500 01  HELP-VARIABLE.",
    "000600     02  WS-RESTART-REC.",
    "000700 PROCEDURE DIVISION.",
    "000800     STOP RUN.",
])

ONE_SPACE_SOURCE = TWO_SPACE_SOURCE.replace(
    "01  WS-SWITCHES.", "01 WS-SWITCHES."
).replace("01  HELP-VARIABLE.", "01 HELP-VARIABLE.")


def test_a_two_space_aligned_group_is_recognised_as_declared():
    injector = _injector()
    assert injector._declares_group(TWO_SPACE_SOURCE, "WS-SWITCHES") is True
    assert injector._declares_group(TWO_SPACE_SOURCE, "HELP-VARIABLE") is True


def test_a_one_space_aligned_group_is_also_recognised():
    injector = _injector()
    assert injector._declares_group(ONE_SPACE_SOURCE, "WS-SWITCHES") is True


def test_a_genuinely_absent_group_is_not_recognised():
    injector = _injector()
    bare = "\n".join([
        "000100 DATA DIVISION.",
        "000200 WORKING-STORAGE SECTION.",
        "000300 77  USERABEN  PIC X(8).",
        "000400 PROCEDURE DIVISION.",
        "000500     STOP RUN.",
    ])
    assert injector._declares_group(bare, "WS-SWITCHES") is False


def test_ensure_working_storage_does_not_duplicate_a_two_space_group(monkeypatch):
    """The exact regression: the metadata-driven system's own spacing
    convention must be recognised, not just this generator's own."""
    injector = _injector()
    # generator/context are never reached when the group is already
    # found, so they can stay unset for this test.
    diagnostics: list[str] = []
    result = injector.ensure_working_storage(
        TWO_SPACE_SOURCE, context=None, diagnostics=diagnostics
    )
    assert result == TWO_SPACE_SOURCE
    assert not any("injected" in d.lower() for d in diagnostics)
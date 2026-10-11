# LOCATION: tests/pipeline/test_every_stage_has_a_call_site.py
# ACTION: CREATE NEW FILE
r"""A registered stage with no caller is dead code that reads as live.

registry.py warns:

    "A stage whose call site delegates to run_stage() MUST be enabled.
     Disabling it makes the pass silently stop running, and the
     row/column baseline will not notice."

Registering is only half the wiring. While call POSITION is owned by the
call sites, every stage name in PIPELINE must appear in at least one
run_stage("<name>", ...) or self._stage("<name>", ...) call somewhere in
converter/. This test is the missing half.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from converter.pipeline.registry import PIPELINE

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "converter"
ENCODING = "utf-8-sig"


def _all_source() -> str:
    parts = []
    for path in sorted(SOURCE_DIR.rglob("*.py")):
        if path.name == "registry.py":
            continue  # the declaration, not a call site
        parts.append(path.read_text(encoding=ENCODING, errors="replace"))
    return "\n".join(parts)


SOURCE = _all_source()


@pytest.mark.parametrize("stage", PIPELINE, ids=lambda s: s.name)
def test_every_stage_is_actually_invoked(stage):
    needle = f'"{stage.name}"'
    assert needle in SOURCE, (
        f"Stage '{stage.name}' is registered in PIPELINE but no call site "
        f"names it. It will never run, and no baseline will notice.\n"
        f"Add a delegating method that calls "
        f'run_stage("{stage.name}", Document(cobol=...)) and invoke it '
        f"from finish()."
    )
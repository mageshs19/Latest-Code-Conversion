# FILE: tools/lrf_populator_probe.py
# ACTION: CREATE NEW FILE
"""Runs the LRF populator directly against the newest generated .cbl.

Bypasses the pipeline entirely. If this prints diagnostics, the
populator works and the defect is in the WIRING. If it prints nothing,
the defect is in the populator.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from converter.generators.lrf_host_variable_populator import (
    LrfHostVariablePopulator,
)

OUTPUT_DIR = ROOT / "mainframe" / "workspace" / "Output"


def newest_cbl() -> Path:
    files = sorted(
        OUTPUT_DIR.glob("*.cbl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise SystemExit(f"No .cbl found in {OUTPUT_DIR}")
    return files[0]


def main() -> None:
    target = newest_cbl()
    print(f"File    : {target.name}")

    text = target.read_text(encoding="utf-8", errors="replace")
    marker_lines = [
        index + 1
        for index, line in enumerate(text.split("\n"))
        if "EXPANDED LRF" in line.upper()
    ]
    print(f"Markers : {len(marker_lines)} at lines {marker_lines}")

    populator = LrfHostVariablePopulator()
    result, messages = populator.augment_procedure_division(text)

    print(f"Changed : {result != text}")
    print(f"Messages: {len(messages)}")
    for message in messages:
        print(f"  - {message}")


if __name__ == "__main__":
    main()
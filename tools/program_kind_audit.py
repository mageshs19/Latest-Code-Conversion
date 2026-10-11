# LOCATION: tools/program_kind_audit.py
# ACTION: CREATE NEW FILE

"""Classify every program in the workspace and show the evidence.

Answers one question with data instead of opinion: does source-based
classification agree with what the team believes about each member?

Run from the project root:

    $env:PYTHONPATH = "."
    python tools\program_kind_audit.py

Exit code 0 when every program classified with evidence or was clearly
read-only. Exit code 1 when any program is LOW CONFIDENCE and wants a
human look.
"""

from __future__ import annotations

import sys
from pathlib import Path

from converter.resolvers.program_kind_resolver import ProgramKindResolver
from rules.program_kind_rules import KIND_UPDATE

SUPPORTED = (".cbl", ".cob", ".txt")

# A program the team may believe writes, whose source shows nothing.
# Not an error - a prompt to look.
LOW_CONFIDENCE_HINTS = ("FFRECAB", "CHECKPOINT", "RESTART")


def program_files(root: Path) -> list[Path]:
    """Every program file, flat layout or kind sub-folders."""
    if not root.is_dir():
        return []
    found = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED
    ]
    return sorted(found, key=lambda item: item.name.lower())


def classify(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    resolver = ProgramKindResolver()
    kind, messages = resolver.resolve(text, input_says_update=None)
    evidence = [m for m in messages if "evidence line" in m]
    return kind, evidence


def low_confidence(path: Path, kind: str) -> bool:
    """Read-only verdict on a program that smells like a restart job."""
    if kind == KIND_UPDATE:
        return False
    upper = path.read_text(encoding="utf-8", errors="replace").upper()
    return any(hint in upper for hint in LOW_CONFIDENCE_HINTS)


def main() -> int:
    from mainframe.zowe_workspace import program_dir

    root = program_dir()
    files = program_files(root)

    if not files:
        print(f"No program files under {root}")
        return 1

    print(f"Program folder : {root}")
    print(f"Members        : {len(files)}")
    print("-" * 78)

    suspect = 0
    for path in files:
        kind, evidence = classify(path)
        flag = ""
        if low_confidence(path, kind):
            flag = "  <-- LOW CONFIDENCE, review"
            suspect += 1

        print(f"{path.name:<24} {kind.upper():<10} "
              f"{len(evidence)} evidence line(s){flag}")
        for line in evidence[:3]:
            print(f"    {line.split('evidence ', 1)[-1]}")

    print("-" * 78)
    print(f"Low confidence : {suspect}")
    return 1 if suspect else 0


if __name__ == "__main__":
    sys.exit(main())
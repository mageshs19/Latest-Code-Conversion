"""Print the pipeline. Self-documenting: run it, read the conversion."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from converter.pipeline.registry import PIPELINE, describe  # noqa: E402

if __name__ == "__main__":
    print(f"\nCONVERSION PIPELINE - {len(PIPELINE)} stage(s)\n" + "-" * 60)
    for line in describe():
        print(line)
    print()
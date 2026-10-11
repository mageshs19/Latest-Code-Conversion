import sys
from pathlib import Path

from converter.services.working_storage_group_selector import (
    WorkingStorageGroupSelector,
)

folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/S/S-Input/Output/Retrieval")
files = sorted(folder.glob("*.cbl"), key=lambda p: p.stat().st_mtime)
if not files:
    raise SystemExit(f"no .cbl found in {folder}")

artifact = files[-1]
lines = artifact.read_text(encoding="utf-8", errors="replace").splitlines()
layout = WorkingStorageGroupSelector().analyze(lines)

print("artifact:", artifact.name)
print("")
print("ALL 01 GROUPS")
for g in layout.groups:
    kind = "RECORD" if g.is_record_layout else "work"
    print(f"  {g.name:<28} {kind:<7} child_level={g.child_level or '-':<3} header={g.header_index}")

safe = layout.safe_groups()
print("")
print("SAFE GROUPS:", [g.name for g in safe])
print("FIRST SAFE :", safe[0].name if safe else "(none)")
print("LAST  SAFE :", safe[-1].name if safe else "(none)")

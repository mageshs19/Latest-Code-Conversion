import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import rules.idms_transformer_messages as m

print("module file :", m.__file__)
print("has constant:", hasattr(m, "ERROR_STATUS_MOVE_OWNED_ELSEWHERE"))
print()
print("sys.path:")
for entry in sys.path:
    print("   ", entry)

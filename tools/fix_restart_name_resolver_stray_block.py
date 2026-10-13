# LOCATION: tools/fix_restart_name_resolver_stray_block.py
# ACTION: CREATE NEW FILE, RUN ONCE, THEN DELETE
"""
CORRECTION: removes a stray, half-merged header block from
converter/generators/restart/restart_name_resolver.py.

The block contained:
  - a SECOND `from __future__ import annotations` (illegal after other
    imports already executed - this is the confirmed SyntaxError),
  - a `NameDerivationResolver` import/wiring that does not belong in
    this module (record_name here is PROGRAM-owned: read from source,
    refused when absent - per the module's own docstring. Derivation
    belongs in RestartStorageBuilder, where it already lives and is
    covered by tests/restart/test_m5_storage_builder_derives_record.py),
  - a redundant `import re` (re is already imported at the top of the
    file; nothing here needs a second import).

Uses exact string matching against the verbatim text captured from the
live file, so this is a precise deletion, not a reconstruction.
"""
from __future__ import annotations

from pathlib import Path

TARGET = Path("converter/generators/restart/restart_name_resolver.py")

STRAY_BLOCK = '''from __future__ import annotations

from converter.services.name_derivation_resolver import NameDerivationResolver

# Reuse the same word-boundary substitution UpdateInputRecordRenamer
# relies on, so both passes derive names identically. If the renamer's
# pattern constant is importable, prefer it over re-declaring one here.
from converter.postprocess.update_input_record_renamer import (
    WORD_REFERENCE_PATTERN_TEMPLATE,
)
import re
'''

STRAY_INIT_LINE = "        self._name_resolver = name_derivation_resolver or NameDerivationResolver()\n"

def main() -> None:
    text = TARGET.read_text(encoding="utf-8")

    if STRAY_BLOCK not in text:
        raise SystemExit(
            "Stray header block not found verbatim - the file has changed "
            "since this patch was written. Stopping without modifying "
            "anything; re-diff before proceeding."
        )
    if STRAY_INIT_LINE not in text:
        raise SystemExit(
            "Stray __init__ line not found verbatim - the file has changed "
            "since this patch was written. Stopping without modifying "
            "anything; re-diff before proceeding."
        )

    fixed = text.replace(STRAY_BLOCK, "")
    fixed = fixed.replace(STRAY_INIT_LINE, "")

    TARGET.write_text(fixed, encoding="utf-8")
    print(f"Removed stray block and stray __init__ line from {TARGET}")

if __name__ == "__main__":
    main()
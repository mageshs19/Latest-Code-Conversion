# LOCATION: tools/probe_live_cursor_diagnostics.py
# ACTION: CREATE NEW FILE  (throwaway)
"""What is ACTUALLY loaded. No assumptions.

    $env:PYTHONPATH = "."
    python tools\probe_live_cursor_diagnostics.py
"""

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

LINE = "-" * 68


def show(label, value):
    print(f"  {label:<34}{value}")


# ---------------------------------------------------------------- 1
print(LINE)
print("1. DUPLICATE FILES ON DISK")
print(LINE)
for stem in (
    "cursor_key_diagnostics",
    "cursor_paragraph_body_builder",
    "join_key_label_resolver",
    "cursor_error_branch",
):
    hits = sorted(ROOT.rglob(f"{stem}.py"))
    flag = "  <-- DUPLICATE" if len(hits) > 1 else ""
    print(f"  {stem}: {len(hits)}{flag}")
    for h in hits:
        print(f"      {h.relative_to(ROOT)}")

caches = sorted(ROOT.rglob("__pycache__"))
print(f"\n  __pycache__ folders: {len(caches)}")

# ---------------------------------------------------------------- 2
print(LINE)
print("2. LIVE RULES VALUES")
print(LINE)
import rules.cursor_paragraph_rules as R   # noqa: E402

show("module file", R.__file__)
for name in (
    "KEY_DISPLAY_TEMPLATE",
    "KEY_LABEL_SOURCE",
    "KEY_LABEL_MIN_WIDTH",
    "ALIGN_KEY_QUALIFIER",
    "EMIT_KEY_DIAGNOSTICS",
):
    show(name, repr(getattr(R, name, "*** ABSENT ***")))

print()
for dead in (
    "FETCH_KEY_LABEL_WIDTH",
    "JOIN_KEY_LABEL_WIDTH",
    "IND_WHEN_BODY_CONT",
):
    if hasattr(R, dead):
        show(dead, f"{getattr(R, dead)!r}   <-- SHOULD BE DELETED")

# ---------------------------------------------------------------- 3
print(LINE)
print("3. LIVE CLASS FILES")
print(LINE)
from converter.generators.cursor_paragraph.cursor_key_diagnostics import (  # noqa: E402
    KeyDiagnosticsBuilder,
)
from converter.generators.cursor_paragraph.cursor_paragraph_body_builder import (  # noqa: E402
    CursorParagraphBodyBuilder,
)

show("KeyDiagnosticsBuilder", inspect.getfile(KeyDiagnosticsBuilder))
show("CursorParagraphBodyBuilder", inspect.getfile(CursorParagraphBodyBuilder))

# what the PACKAGE exports may differ from the MODULE
import converter.generators.cursor_paragraph as PKG   # noqa: E402

pkg_cls = getattr(PKG, "CursorParagraphBodyBuilder", None)
if pkg_cls is not None:
    same = pkg_cls is CursorParagraphBodyBuilder
    show("package export is same object", same)
    if not same:
        show("package export file", inspect.getfile(pkg_cls))
        print("      <-- __init__.py IS SHADOWING THE MODULE")

# ---------------------------------------------------------------- 4
print(LINE)
print("4. NEW CODE PRESENT?")
print(LINE)
src = inspect.getsource(KeyDiagnosticsBuilder)
checks = {
    "derived width (KEY_LABEL_MIN_WIDTH)": "KEY_LABEL_MIN_WIDTH" in src,
    "derived offset (len(display)-len(host))":
        "len(display) - len(host)" in src,
    "calls label_resolver.label_for": "label_for" in src,
    "STALE FETCH_KEY_LABEL_WIDTH": "FETCH_KEY_LABEL_WIDTH" in src,
}
for label, value in checks.items():
    show(label, value)

sig = inspect.signature(CursorParagraphBodyBuilder.__init__)
show("body builder accepts repository",
     "mapping_repository" in sig.parameters)

# ---------------------------------------------------------------- 5
print(LINE)
print("5. RENDER WITH NO REPOSITORY")
print(LINE)
b = KeyDiagnosticsBuilder()
for line in b.lines_for_hosts(
    ["CT-RKTPROD-479BEFF OF DCLDZBEFFTV",
     "NR-IDSTOCK-479BEFF OF DCLDZBEFFTV"]
):
    print(f"  |{line}|")
print()
show("fallback messages", len(b.messages))
for m in b.messages:
    print(f"      {m}")
print(LINE)
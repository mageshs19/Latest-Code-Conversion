"""Static arity guard for review Recorder call sites.

Reads the LIVE signature of every public Recorder method and compares it
against every `record.<method>(...)` call in review/checks. Catches the
exact defect that BLOCKED CHK-26 on all six programs:

    Recorder.pass_all() takes 3 positional arguments but 4 were given

Limits are DERIVED, never hardcoded, so the guard cannot drift when a
Recorder signature changes.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from review.engine.check_base import Recorder  # noqa: E402

CHECKS_DIR = ROOT / "review" / "checks"
RECORDER_VAR = "record"
UNBOUNDED = 10 ** 6


def max_positional() -> dict:
    limits = {}
    for name, member in inspect.getmembers(Recorder, inspect.isfunction):
        if name.startswith("_"):
            continue
        count = 0
        for param_name, param in inspect.signature(member).parameters.items():
            if param_name == "self":
                continue
            if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
                count += 1
            elif param.kind is param.VAR_POSITIONAL:
                count = UNBOUNDED
        limits[name] = count
    return limits


def call_sites(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if not isinstance(func.value, ast.Name):
            continue
        if func.value.id != RECORDER_VAR:
            continue
        yield node.lineno, func.attr, len(node.args)


def main() -> int:
    limits = max_positional()
    files = sorted(CHECKS_DIR.glob("*.py"))
    bad = []
    unknown = []
    total = 0

    for path in files:
        for line, name, count in call_sites(path):
            total += 1
            if name not in limits:
                unknown.append((path.name, line, name))
            elif count > limits[name]:
                bad.append((path.name, line, name, count, limits[name]))

    print("Recorder methods: " + ", ".join(
        f"{n}({c})" for n, c in sorted(limits.items())
    ))
    print(f"Scanned {len(files)} check file(s), {total} record.* call site(s).")

    for file_name, line, name in unknown:
        print(f"UNKNOWN {file_name}:{line}: record.{name} is not a Recorder method")
    for file_name, line, name, count, allowed in bad:
        print(
            f"ARITY   {file_name}:{line}: record.{name} got {count} "
            f"positional arg(s); max is {allowed}"
        )

    if bad or unknown:
        print(f"FAILED: {len(bad)} arity, {len(unknown)} unknown.")
        return 1

    print("OK: every record.* call matches its Recorder signature.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

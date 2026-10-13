"""No module may declare the same constant twice.

tests/test_rules_no_duplicate_constants.py enforces this for rules/ and
nothing enforced it for review/standards/, where

    RESTART_INSERT_QUERYNO = ""        line 274
    RESTART_INSERT_QUERYNO = "413"     line 371

coexisted. The second assignment wins silently; the first becomes dead
code that still reads as authoritative.

The cross-module guard cannot catch this: it stores one value per file,
so a within-file duplicate overwrites itself before the comparison.
"""

from __future__ import annotations

import ast
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCANNED = ("rules", "review/standards", "catalogs", "patterns")


def _duplicates(path: pathlib.Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return []

    seen: dict[str, list[int]] = defaultdict(list)
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            continue
        for name in _target_names(node):
            seen[name].append(node.lineno)

    return [
        f"{path.name}:{name} at lines {lines}"
        for name, lines in sorted(seen.items())
        if len(lines) > 1
    ]

def _target_names(node: ast.AST) -> list[str]:
    """Constant-like assignment targets, including dict entries.

    WIDENED - only ast.Name targets were checked, so

        MESSAGES["key"] = "..."     assigned twice

    was invisible. rules/cursor_close_guarantee_rules.py carries a
    comment saying exactly that about business_paragraph_unverified:
    someone found it, wrote it down, and the guard still could not see
    it.
    """
    targets = getattr(node, "targets", None) or [getattr(node, "target", None)]
    names: list[str] = []
    for target in targets:
        if isinstance(target, ast.Name) and target.id.isupper():
            names.append(target.id)
        elif (
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id.isupper()
        ):
            try:
                names.append(f"{target.value.id}[{ast.unparse(target.slice)}]")
            except Exception:  # noqa: BLE001
                continue
    return names

def test_no_module_declares_a_constant_twice():
    offenders: list[str] = []
    for folder in SCANNED:
        base = ROOT / folder
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            offenders.extend(_duplicates(path))

    assert not offenders, "Duplicate constant declarations:\n" + "\n".join(
        offenders
    )

# LOCATION: tests/test_no_site_names_in_rules_and_patterns.py
# ACTION: REPLACE ENTIRE FILE
"""No customer site name may appear in rules/ or patterns/.

Both directories declare, in their own module docstrings, that no
program, paragraph, record, table, DCLGEN, cursor or host variable name
is hardcoded. This test enforces that declaration.

Comments and docstrings are included on purpose: a worked example
carrying a real table name is one copy-paste away from becoming a
default. That is exactly how DCLDZ01RSTV reached
rules/restart_sql_templates.py.

TWO LISTS, TWO MEANINGS - do not confuse them
-----------------------------------------------
OWNED_VOCABULARY       the module's PURPOSE is a naming rule, and the
                       worked example IS the specification. Permanent.

KNOWN_SITE_NAME_DEBT   prose that has not been rewritten yet. TEMPORARY.
                       An entry records the tokens present on
                       14-10-2026. The set may SHRINK; a token that is
                       not recorded fails the build.

The debt list is a ratchet, not an exemption. A NEW module, or a NEW
token in an existing module, fails immediately. A module whose debt is
cleared must be REMOVED from the list - test_debt_list_is_not_stale
enforces that, so the list cannot outlive the work.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SITE_TOKENS = ("DCLDZ", "DZ01RST", "DZBFAR", "VMDZ", "NM_ID_RS")

ROOT = Path(__file__).resolve().parents[1]
SCANNED_DIRS = ("rules", "patterns")

# Permanent. module stem -> the naming rule that module owns.
OWNED_VOCABULARY: dict[str, str] = {
    "name_derivation_rules": (
        "Owns the VM<site>?BD<tail> -> VMDZ<site><tail> rule. "
        "The worked example IS the specification."
    ),
    "update_runner_rules": (
        "Rule statement quotes the derivation rule verbatim."
    ),
    "retrieval_runner_rules": (
        "Rule statement quotes the derivation rule verbatim."
    ),
}

# TEMPORARY. Prose debt measured 14-10-2026. Shrink only.
KNOWN_SITE_NAME_DEBT: dict[str, tuple[str, ...]] = {
    # ---- rules/
    "cobol_standard_initialization_rules": ("DCLDZ", "VMDZ"),
    "cursor_declaration_order_by": ("VMDZ",),
    "cursor_declaration_templates": ("VMDZ",),
    "cursor_order_cleanup_rules": ("VMDZ",),
    "cursor_paragraph_rules": ("DCLDZ", "VMDZ"),
    "db2_date_conversion_standards": ("DCLDZ", "VMDZ"),
    "db2_include_rules": ("DZBFAR",),
    "field_mapping_standards": ("DCLDZ",),
    "field_reference_rewriter_rules": ("DCLDZ",),
    "move_alignment_rules": ("DCLDZ",),
    "procedure_indent_rules": ("DCLDZ",),
    "restart_statement_templates": ("DCLDZ", "DZ01RST"),
    "sql_location_rules": ("VMDZ",),
    "structural_safety_rules": ("DCLDZ", "DZBFAR"),
    "update_program_postprocess_rules": ("DZ01RST",),
    "update_restart_rules": ("DZ01RST",),
    # ---- patterns/
    "cursor_close_guarantee_patterns": ("DCLDZ",),
    "db2_date_patterns": ("DCLDZ",),
    "db2_include_patterns": ("DZBFAR",),
    "dynamic_metadata_patterns": ("DCLDZ", "DZ01RST", "VMDZ"),
    "restart_patterns": ("DZ01RST",),
}


def _modules() -> list[Path]:
    found: list[Path] = []
    for directory in SCANNED_DIRS:
        found.extend(sorted((ROOT / directory).rglob("*.py")))
    return found


def _tokens_in(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8", errors="replace").upper()
    return [token for token in SITE_TOKENS if token in source]


@pytest.mark.parametrize(
    "path", _modules(), ids=lambda p: f"{p.parent.name}/{p.name}"
)
def test_module_carries_no_site_name(path: Path) -> None:
    """A module must be clean, owned, or within its recorded debt."""
    if path.stem in OWNED_VOCABULARY:
        pytest.skip(OWNED_VOCABULARY[path.stem])

    found = set(_tokens_in(path))
    allowed = set(KNOWN_SITE_NAME_DEBT.get(path.stem, ()))
    new = sorted(found - allowed)

    assert not new, (
        f"{path.relative_to(ROOT)} carries NEW site name(s): "
        f"{', '.join(new)}. Rewrite to placeholders. Do not extend "
        f"KNOWN_SITE_NAME_DEBT - it shrinks only."
    )


@pytest.mark.parametrize("stem", sorted(KNOWN_SITE_NAME_DEBT))
def test_debt_list_is_not_stale(stem: str) -> None:
    """A cleared module must be REMOVED from the debt list.

    Without this the list outlives the work and silently becomes a
    permanent exemption - the thing it exists to avoid.
    """
    matches = [p for p in _modules() if p.stem == stem]
    assert matches, (
        f"{stem} is listed as debt but no such module exists. "
        f"Remove the entry."
    )

    found = set(_tokens_in(matches[0]))
    recorded = set(KNOWN_SITE_NAME_DEBT[stem])
    cleared = sorted(recorded - found)

    assert not cleared, (
        f"{stem} no longer carries {', '.join(cleared)}. "
        f"Update or remove its KNOWN_SITE_NAME_DEBT entry."
    )


def test_the_two_lists_do_not_overlap() -> None:
    """A module is either owned or in debt. Never both."""
    overlap = set(OWNED_VOCABULARY) & set(KNOWN_SITE_NAME_DEBT)
    assert not overlap, sorted(overlap)
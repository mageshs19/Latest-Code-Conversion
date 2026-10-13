# LOCATION: tests/test_rules_single_source_of_truth.py
# ACTION: CREATE NEW FILE
"""A fact may have exactly one home.

REGRESSION - QUERYNO_BASE was 100 in one rules module and 254 in
another. cursor_declare_builder.py imported its SQL tokens from one and
QUERYNO from the other, so the generated DECLARE carried QUERYNO 119
while the manual reference carries QUERYNO 254.

DB2 EXPLAIN identifies a statement by QUERYNO. A divergent number cannot
be tied back to the documented access path.
"""

from __future__ import annotations

import rules.cursor_declaration_rules as cursor_rules
import rules.db2_infrastructure_rules as infra_rules

MANUAL_REFERENCE_QUERYNO_BASE = 254


def test_queryno_base_has_one_value():
    assert cursor_rules.QUERYNO_BASE == infra_rules.QUERYNO_BASE


def test_queryno_step_has_one_value():
    assert cursor_rules.QUERYNO_STEP == infra_rules.QUERYNO_STEP


def test_queryno_template_has_one_value():
    assert cursor_rules.QUERYNO_TEMPLATE == infra_rules.QUERYNO_TEMPLATE


def test_queryno_first_matches_the_manual_reference():
    assert cursor_rules.QUERYNO_FIRST == MANUAL_REFERENCE_QUERYNO_BASE


def test_the_template_placeholder_is_honoured():
    """A renamed placeholder raises KeyError at render time."""
    rendered = cursor_rules.QUERYNO_TEMPLATE.format(number=254)

    assert rendered == "QUERYNO 254"

def test_no_rules_module_declares_a_restart_queryno():
    """RestartConfig owns the restart QUERYNOs. A rules-module copy is
    dead the moment the config changes, and reads as authoritative."""
    import pathlib

    rules = pathlib.Path(__file__).resolve().parents[1] / "rules"
    offenders = [
        f"{path.name}:{n}"
        for path in rules.rglob("*.py")
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if line.strip().startswith("RESTART_") and "QUERYNO" in line and "=" in line
    ]
    assert not offenders, "Restart QUERYNO declared outside RestartConfig: " + ", ".join(offenders)
# LOCATION: tests/test_eoc_vocabulary_agrees_across_the_review_boundary.py
# ACTION: CREATE NEW FILE
"""The converter and the reviewer must know the same EOC vocabulary.

review/ must never import from the converter, so the two lists are
deliberately separate copies in different shapes:

    rules/cursor_eoc_rules.py          bare CONDITIONS  "DB-END-OF-SET"
    review/standards/cobol_standards   loop STATEMENTS  "UNTIL DB-END-OF-SET"

Nothing enforced agreement, and the review copy silently held only two
of the six spellings the converter rewrites. A loop left on any of the
other four passed CHK-14 while failing the standard it enforces.

tests/ may import both, so the invariant lives here.
"""

from __future__ import annotations

from review.standards import cobol_standards as std
from rules.cursor_eoc_rules import LEGACY_EOC_CONDITIONS


def test_every_converter_condition_has_a_reviewer_statement() -> None:
    missing = [
        condition
        for condition in LEGACY_EOC_CONDITIONS
        if f"UNTIL {condition}" not in std.LEGACY_EOC_LOOP_STATEMENTS
    ]
    assert not missing, (
        "The reviewer cannot detect these converter-known conditions: "
        + ", ".join(missing)
    )


def test_review_does_not_import_the_converter() -> None:
    """The one-way boundary, asserted rather than trusted."""
    import inspect

    source = inspect.getsource(std)
    assert "from rules" not in source
    assert "from converter" not in source
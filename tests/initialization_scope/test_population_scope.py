# LOCATION: tests/initialization_scope/test_population_scope.py
# ACTION: CREATE NEW FILE
"""The second anchor: a paragraph that populates a DCLGEN group.

REGRESSION CONTRACT

VMDZ1567 shipped with VERWERKING populating DCLDZBFARTV from its first
statement and no INITIALIZE anywhere in the program. The initializer
had one anchor - a cursor OPEN - and the program has no cursor, so the
whole pass stood down.

These tests are written against PopulationSiteScanner directly, with
fixed-format lines built here, so they do not depend on the package
conftest and cannot drift with it.
"""

from __future__ import annotations

import pytest

from converter.generators.initialization.population_site_scanner import (
    InitializationSite,
    PopulationSiteScanner,
)
from rules.initialization_placement_rules import SCOPE_ROW

GROUP = "DCLAAATV"
OTHER = "DCLBBBTV"


def _fixed(body: str, number: int) -> str:
    """One 80-column fixed-format record."""
    left = f"{number:06d}"
    text = f"{body}"[:65].ljust(65)
    right = f"{number * 10:08d}"
    return f"{left} {text}{right}"

def _comment(body: str, number: int) -> str:
    """One 80-column fixed-format COMMENT record.

    The indicator is column 7. _fixed() starts the body at column 8, so
    a '*' passed through it lands in Area A and the line is a STATEMENT
    beginning with '*', not a comment. That is why the first version of
    this test failed: the fixture was wrong, not the scanner.
    """
    left = f"{number:06d}"
    text = f"{body}"[:65].ljust(65)
    right = f"{number * 10:08d}"
    return f"{left}*{text}{right}"

def _program(bodies: list[str]) -> list[str]:
    return [_fixed(body, index + 1) for index, body in enumerate(bodies)]


@pytest.fixture
def scanner() -> PopulationSiteScanner:
    return PopulationSiteScanner()


# ---------------------------------------------------------------- #
# The defect this file exists for
# ---------------------------------------------------------------- #
def test_a_populating_paragraph_yields_a_site(scanner) -> None:
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE '1815' TO CT-A OF {GROUP}",
        f"    MOVE WS-B TO NR-B OF {GROUP}",
        "    STOP RUN.",
    ])
    sites = scanner.sites(lines)
    assert len(sites) == 1
    assert sites[0].group == GROUP


def test_the_site_anchors_on_the_first_write(scanner) -> None:
    """INITIALIZE must land above the first MOVE, not the second."""
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE '1815' TO CT-A OF {GROUP}",
        f"    MOVE WS-B TO NR-B OF {GROUP}",
    ])
    assert scanner.sites(lines)[0].index == 2


def test_the_site_is_row_scoped(scanner) -> None:
    """The paragraph is the per-record unit of work."""
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
    ])
    assert scanner.sites(lines)[0].scope == SCOPE_ROW


def test_the_site_names_its_owning_paragraph(scanner) -> None:
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
    ])
    assert scanner.sites(lines)[0].owner.upper() == "VERWERKING"


# ---------------------------------------------------------------- #
# Resolution rule - why this dataclass exists
# ---------------------------------------------------------------- #
def test_a_population_site_resolves_without_a_cursor() -> None:
    """CursorOpenSite.is_resolved needs a cursor; this one must not."""
    site = InitializationSite(index=0, group=GROUP, indent="", owner="P")
    assert site.cursor == ""
    assert site.is_resolved is True


def test_a_site_without_a_group_is_unresolved() -> None:
    site = InitializationSite(index=0, group="", indent="", owner="P")
    assert site.is_resolved is False


# ---------------------------------------------------------------- #
# No double initialisation
# ---------------------------------------------------------------- #
def test_a_group_owned_by_a_cursor_is_excluded(scanner) -> None:
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
        f"    MOVE WS-B TO CT-B OF {OTHER}",
    ])
    sites = scanner.sites(lines, exclude_groups={GROUP})
    assert [site.group for site in sites] == [OTHER]


def test_two_paragraphs_touching_one_group_each_get_a_site(scanner) -> None:
    """Each paragraph is its own unit of work."""
    lines = _program([
        "PROCEDURE DIVISION.",
        "PARA-ONE.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
        "PARA-TWO.",
        f"    MOVE WS-B TO CT-B OF {GROUP}",
    ])
    owners = [site.owner.upper() for site in scanner.sites(lines)]
    assert owners == ["PARA-ONE", "PARA-TWO"]


# ---------------------------------------------------------------- #
# Refusals
# ---------------------------------------------------------------- #
def test_a_program_with_no_dclgen_write_yields_nothing(scanner) -> None:
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        "    MOVE WS-A TO WS-B",
    ])
    assert scanner.sites(lines) == []


def test_a_comment_is_never_a_site(scanner) -> None:
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
    ])
    lines.append(_comment(f"   MOVE WS-A TO CT-A OF {GROUP}", 3))
    assert scanner.sites(lines) == []


def test_a_non_dclgen_qualifier_is_not_a_site(scanner) -> None:
    """OF VMBFAR is an IDMS record, not a DCLGEN group."""
    lines = _program([
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        "    MOVE WS-A TO CT-A OF VMBFAR",
    ])
    assert scanner.sites(lines) == []

# ---------------------------------------------------------------- #
# The report must describe the program it actually converted
# ---------------------------------------------------------------- #
def test_a_population_placement_is_not_reported_as_a_child_cursor() -> None:
    """placed_row_scope claims a parent row that does not exist here."""
    from converter.generators.initialization.scope_initializer import (
        CursorScopedInitializer,
    )

    source = "\n".join(_program([
        "WORKING-STORAGE SECTION.",
        "EXEC SQL INCLUDE AAATV END-EXEC.",
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
        "    STOP RUN.",
    ]))

    initializer = CursorScopedInitializer(source)
    output = initializer.process()
    messages = " ".join(initializer.messages)

    assert f"INITIALIZE {GROUP}" in output
    assert "parent row" not in messages
    assert "populates it" in messages


def test_the_summary_counts_the_population_site() -> None:
    """It reported '0 run-level and 0 row-level' after placing one."""
    from converter.generators.initialization.scope_initializer import (
        CursorScopedInitializer,
    )

    source = "\n".join(_program([
        "WORKING-STORAGE SECTION.",
        "EXEC SQL INCLUDE AAATV END-EXEC.",
        "PROCEDURE DIVISION.",
        "VERWERKING.",
        f"    MOVE WS-A TO CT-A OF {GROUP}",
        "    STOP RUN.",
    ]))

    initializer = CursorScopedInitializer(source)
    initializer.process()
    assert any(
        "0 run-level and 1 row-level" in message
        for message in initializer.messages
    )
# LOCATION: tests/cursor_where/test_declare_refusals.py
# ACTION: CREATE NEW FILE
"""Every way the declare builder REFUSES, and how it reports it.

    D-6  empty column list rendered SELECT *    -> CHK-12.04 reject
    D-7  WHERE ownership guard was dropped      -> SQLCODE -206
    D-10 spec-level refusals were SILENT        -> cursor vanished

GOVERNING RULE
--------------
The converter may REFUSE to generate SQL it cannot resolve. It must
never GUESS, and it must never refuse in silence. A refusal has two
halves and both are asserted here:

    the COBOL   a DB2 WARNING block, sized for the body window
    the report  a message on builder.messages naming the reason

cobol_standards.FORBIDDEN_MARKERS contains "DB2 WARNING" deliberately,
so a program still carrying one FAILS production validation rather than
shipping a cursor that cannot bind.
"""

from __future__ import annotations

from rules.cursor_declaration_rules import ENFORCE_WHERE_COLUMN_OWNERSHIP
from tests.cursor_where._fixtures import (
    CHILD_TABLE,
    CURSOR,
    EXPECTED_PREDICATE,
    KEY_COLUMN,
    UNOWNED_COLUMN,
    UNOWNED_PREDICATE,
    assert_refusal,
    bodies,
    has_clause,
    spec,
)


# =====================================================================
# D-6  SELECT * is refused
# =====================================================================
def test_an_empty_column_list_refuses_instead_of_select_star(declares):
    """CHK-12.04 forbids SELECT *, and an implicit list breaks the
    SELECT / FETCH INTO positional parity. Refusing is the only safe
    answer."""
    rendered = bodies(declares.build(spec(select_columns=[])))

    assert_refusal(rendered, CHILD_TABLE)
    assert "*" not in " ".join(rendered)


def test_the_empty_column_refusal_is_reported(declares):
    declares.build(spec(select_columns=[]))

    assert any("SELECT * refused" in m for m in declares.messages)


def test_select_star_never_appears_in_a_rendered_declare(declares):
    rendered = bodies(declares.build(spec()))
    select = _first_column_line(rendered)

    assert select >= 0
    assert rendered[select].strip() != "*"


def _first_column_line(rendered: list[str]) -> int:
    """Index of the line after SELECT. -1 when there is no SELECT."""
    for index, body in enumerate(rendered):
        if body.upper().startswith("SELECT"):
            return index + 1
    return -1


# =====================================================================
# D-7  WHERE column ownership guard
# =====================================================================
def test_ownership_guard_is_enabled_by_the_site_standard():
    assert ENFORCE_WHERE_COLUMN_OWNERSHIP is True


def test_a_parent_column_on_the_left_is_refused(guarded_declares):
    """A parent column on the left of a child predicate binds as
    SQLCODE -206, so the whole program fails to run."""
    rendered = bodies(
        guarded_declares.build(spec(where_conditions=[UNOWNED_PREDICATE]))
    )

    assert_refusal(rendered, UNOWNED_COLUMN, CHILD_TABLE)


def test_the_ownership_refusal_names_the_column_in_the_report(
    guarded_declares,
):
    """A refusal with no diagnostic is worse than no guard at all: the
    cursor disappears and the report does not say which column did it."""
    guarded_declares.build(spec(where_conditions=[UNOWNED_PREDICATE]))

    assert any(UNOWNED_COLUMN in m for m in guarded_declares.messages)


def test_an_owned_column_on_the_left_is_accepted(guarded_declares):
    rendered = bodies(
        guarded_declares.build(spec(where_conditions=[EXPECTED_PREDICATE]))
    )

    assert has_clause(rendered, "WHERE")
    assert any(EXPECTED_PREDICATE in body for body in rendered)


def test_a_keyword_operator_predicate_is_not_refused(guarded_declares):
    """IS / BETWEEN / IN / LIKE carry no '=' character.

    The parser cut the predicate at the first SYMBOL operator, so a
    keyword form came back whole as the 'column', failed the ownership
    test, and a valid cursor was refused with a DB2 WARNING.
    """
    rendered = bodies(
        guarded_declares.build(
            spec(where_conditions=[f"{KEY_COLUMN} IS NOT NULL"])
        )
    )

    assert has_clause(rendered, "WHERE")


def test_a_qualified_operand_is_not_refused(guarded_declares):
    """T.NR_ID and NR_ID are the same column.

    Only the bare name is compared; a table qualifier used to fail the
    ownership test outright.
    """
    rendered = bodies(
        guarded_declares.build(
            spec(where_conditions=[f"T.{KEY_COLUMN} = :G.KY-SIFORM"])
        )
    )

    assert has_clause(rendered, "WHERE")


def test_the_guard_stands_down_when_no_column_list_is_available(declares):
    """No resolver injected: validate nothing rather than refuse a
    cursor that may be perfectly correct."""
    rendered = bodies(
        declares.build(
            spec(where_conditions=["ANY_COLUMN = :SOMEGROUP.ANY-COLUMN"])
        )
    )

    assert has_clause(rendered, "WHERE")


def test_the_stand_down_is_reported(declares):
    """A guard that stands down in SILENCE is how an unguarded builder
    reached production and stayed invisible across several runs."""
    declares.build(spec(where_conditions=[EXPECTED_PREDICATE]))

    assert any("stood down" in m for m in declares.messages)


def test_the_stand_down_is_reported_once_per_table(declares):
    """The lookup is cached per table. Without the cache the same
    message was repeated per cursor and buried the signal."""
    declares.build(spec(order=1, where_conditions=[EXPECTED_PREDICATE]))
    declares.build(spec(order=2, where_conditions=[EXPECTED_PREDICATE]))

    stand_downs = [m for m in declares.messages if "stood down" in m]
    assert len(stand_downs) == 1, stand_downs


# =====================================================================
# D-10  spec-level refusals
# =====================================================================
def test_a_spec_without_a_table_produces_a_warning_not_sql(declares):
    """Refusing beats guessing: no fabricated FROM clause."""
    rendered = bodies(declares.build(spec(table_name="")))

    assert_refusal(rendered, CURSOR)


def test_a_spec_without_a_table_is_reported(declares):
    declares.build(spec(table_name=""))

    assert declares.messages, "the refusal must appear in the report"


def test_a_spec_without_a_cursor_name_produces_a_warning_not_sql(declares):
    rendered = bodies(declares.build(spec(cursor_name="")))

    assert_refusal(rendered)


def test_a_spec_without_a_cursor_name_is_reported(declares):
    """Both spec-level refusals emitted a warning and logged NOTHING, so
    a cursor vanished from the program and the conversion report did not
    say why."""
    declares.build(spec(cursor_name=""))

    assert declares.messages


# =====================================================================
# A refusal is never partial
# =====================================================================
def test_a_refusal_emits_no_fragment_of_a_declare(guarded_declares):
    """Half a DECLARE is worse than none: the composer would carry the
    fragment into WORKING-STORAGE and the compiler would reject it."""
    rendered = bodies(
        guarded_declares.build(spec(where_conditions=[UNOWNED_PREDICATE]))
    )

    joined = " ".join(rendered).upper()
    for token in ("DECLARE", "CURSOR", "END-EXEC", "FOR READ ONLY"):
        assert token not in joined, rendered


def test_reset_clears_refusal_messages_between_programs(guarded_declares):
    """One instance renders every cursor of every program in a folder
    run, so an uncleared report carries program 1 into program 2."""
    guarded_declares.build(spec(where_conditions=[UNOWNED_PREDICATE]))
    assert guarded_declares.messages

    guarded_declares.reset()
    assert guarded_declares.messages == []
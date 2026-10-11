from __future__ import annotations


def test_declaration_carries_a_queryno(declares, spec, bodies):
    lines = bodies(declares.build(spec(order=0)))
    assert any(body.startswith("QUERYNO ") for body in lines)


def test_queryno_is_the_last_clause_before_end_exec(declares, spec, bodies):
    lines = bodies(declares.build(spec(order=0)))

    assert lines[-1] == "END-EXEC."
    assert lines[-2].startswith("QUERYNO ")
    assert lines[-3] == "FOR READ ONLY"


def test_queryno_is_derived_from_the_cursor_order(
    declares, spec, bodies, names
):
    lines = bodies(declares.build(spec(order=2)))
    expected = names["queryno_base"] + (2 * names["queryno_step"])

    assert f"QUERYNO {expected}" in lines


def test_two_cursors_never_share_a_queryno(declares, spec, bodies):
    first = bodies(declares.build(spec(order=0)))
    second = bodies(declares.build(spec(order=1)))

    def queryno(items: list[str]) -> str:
        return next(b for b in items if b.startswith("QUERYNO "))

    assert queryno(first) != queryno(second)


def test_queryno_is_stable_across_runs(declares, spec):
    assert declares.build(spec(order=1)) == declares.build(spec(order=1))


def test_a_child_cursor_keeps_where_and_order_by(
    declares, spec, bodies, clause_index
):
    built = spec(
        order=0,
        where_conditions=["NR_CIOFMAS_479BFAS = :DCLPARENT.NR-CIOFMAS"],
        order_by_columns=["NR_ID_479BFAS ASC"],
    )
    lines = bodies(declares.build(built))

    where = clause_index(lines, "WHERE")
    order_by = clause_index(lines, "ORDER BY")
    read_only = clause_index(lines, "FOR READ ONLY")

    assert where >= 0
    assert order_by >= 0
    assert where < order_by < read_only
    assert lines[-2].startswith("QUERYNO ")


def test_a_root_cursor_keeps_its_order_by(
    declares, spec, bodies, has_clause
):
    lines = bodies(
        declares.build(spec(order=0, order_by_columns=["NR_ID_479BFAS ASC"]))
    )
    assert has_clause(lines, "ORDER BY")


def test_a_spec_without_a_table_produces_a_warning_not_sql(
    declares, spec, bodies
):
    lines = bodies(declares.build(spec(order=0, table_name="")))

    assert len(lines) == 1
    assert "DB2 WARNING" in lines[0]
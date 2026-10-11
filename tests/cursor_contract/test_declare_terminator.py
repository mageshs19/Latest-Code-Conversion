from __future__ import annotations

BARE = "END-EXEC"
CLOSING = "END-EXEC."


def test_the_default_closes_the_sentence(declares, spec, bodies):
    lines = bodies(declares.build(spec(order=0)))
    assert lines[-1] == CLOSING


def test_the_default_preserves_the_previous_bytes(declares, spec):
    assert declares.build(spec(order=0)) == declares.build(
        spec(order=0), is_last=True
    )


def test_an_explicit_last_closes_the_sentence(declares, spec, bodies):
    lines = bodies(declares.build(spec(order=0), is_last=True))
    assert lines[-1] == CLOSING


def test_a_non_last_declaration_closes_bare(declares, spec, bodies):
    lines = bodies(declares.build(spec(order=0), is_last=False))
    assert lines[-1] == BARE


def test_only_the_last_of_two_declarations_carries_the_period(
    declares, spec, bodies
):
    specs = [spec(order=0), spec(order=1)]
    total = len(specs)

    rendered = [
        bodies(declares.build(item, is_last=index == total - 1))
        for index, item in enumerate(specs)
    ]

    assert rendered[0][-1] == BARE
    assert rendered[1][-1] == CLOSING


def test_queryno_still_precedes_the_close_on_both(declares, spec, bodies):
    for flag in (True, False):
        lines = bodies(declares.build(spec(order=0), is_last=flag))
        assert lines[-2].startswith("QUERYNO ")
        assert lines[-3] == "FOR READ ONLY"


def test_a_refusal_is_unaffected_by_is_last(declares, spec, bodies):
    for flag in (True, False):
        lines = bodies(
            declares.build(spec(order=0, table_name=""), is_last=flag)
        )
        assert "DB2 WARNING" in lines[0]
        assert not any(body.startswith(BARE) for body in lines)
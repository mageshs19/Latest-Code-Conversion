from __future__ import annotations


def test_tier_one_reuses_the_preferred_work_group(
    program, resolve, with_work_group
):
    _updated, anchor, _messages = resolve(program(with_work_group))

    assert anchor.is_usable
    assert anchor.group == "WS-TE-WORK"
    assert anchor.level == "10"
    assert anchor.created is False


def test_tier_two_reuses_an_existing_generated_group(
    program, resolve, with_generated_group
):
    _updated, anchor, _messages = resolve(program(with_generated_group))

    assert anchor.is_usable
    assert anchor.group == "WS-DB2-COUNTERS"
    assert anchor.created is False


def test_tier_two_never_picks_a_business_group(
    program, resolve, with_generated_group
):
    _updated, anchor, _messages = resolve(program(with_generated_group))
    assert anchor.group != "WS-DATUMVELDEN"


def test_tier_three_creates_the_generated_group(
    program, resolve, bodies, without_any_known_group
):
    updated, anchor, _messages = resolve(program(without_any_known_group))

    assert anchor.created is True
    assert anchor.group == "WS-DB2-GENERATED"
    assert anchor.level == "10"
    assert "01  WS-DB2-GENERATED." in bodies(updated)


def test_the_created_group_carries_its_marker(
    program, resolve, bodies, without_any_known_group
):
    updated, _anchor, _messages = resolve(program(without_any_known_group))
    joined = " ".join(bodies(updated)).upper()
    assert "DB2 GENERATED WORKING STORAGE" in joined


def test_a_second_resolve_reuses_the_created_group(
    program, resolve, without_any_known_group
):
    updated, first, _messages = resolve(program(without_any_known_group))
    _again, second, _more = resolve(updated)

    assert first.created is True
    assert second.created is False
    assert second.group == "WS-DB2-GENERATED"


def test_the_anchor_sits_after_the_last_child(
    program, resolve, bodies, with_work_group
):
    updated, anchor, _messages = resolve(program(with_work_group))
    before = updated[anchor.insert_index - 1].strip().upper()

    assert before.startswith("10  WS-STATUS")
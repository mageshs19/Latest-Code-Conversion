from __future__ import annotations


def test_a_record_layout_is_never_chosen(
    program, resolve, with_record_layout
):
    _updated, anchor, _messages = resolve(program(with_record_layout))
    assert anchor.group != "REC-FORM"
    assert anchor.group != "OUTRECORD"


def test_a_childless_group_is_never_chosen(
    program, resolve, with_childless_group
):
    _updated, anchor, messages = resolve(program(with_childless_group))

    assert anchor.group != "W-NR-IS-FORM-AS"
    assert anchor.created is True
    assert any("cannot take a generated field" in m for m in messages)


def test_no_working_storage_refuses_rather_than_guesses(
    program, resolve, without_working_storage
):
    lines = program(without_working_storage)
    updated, anchor, messages = resolve(lines)

    assert anchor.is_usable is False
    assert updated == lines
    assert any("no WORKING-STORAGE SECTION" in m for m in messages)


def test_cs_program_lands_in_the_preferred_work_group(
    program, declare, bodies, with_work_group
):
    updated, messages = declare(program(with_work_group), "VMDZ4420")
    text = bodies(updated)

    assert any(
        b.startswith("10  CS-PROGRAM") and "VMDZ4420" in b for b in text
    )
    assert any("inside WS-TE-WORK" in m for m in messages)


def test_cs_program_never_lands_under_an_elementary_item(
    program, declare, bodies, with_childless_group
):
    updated, _messages = declare(program(with_childless_group), "VMDZTEST")
    text = bodies(updated)

    position = next(
        index for index, b in enumerate(text)
        if b.startswith("10  CS-PROGRAM")
    )
    assert text[position - 1].startswith("01  WS-DB2-GENERATED")


def test_cs_program_is_declared_only_once(
    program, declare, bodies, with_work_group
):
    once, _messages = declare(program(with_work_group), "VMDZ4420")
    twice, messages = declare(once, "VMDZ4420")

    assert len([b for b in bodies(twice) if "CS-PROGRAM" in b]) == 1
    assert any("already declared" in m for m in messages)


def test_cs_program_and_counters_would_share_one_group(
    program, resolve, declare, with_work_group
):
    updated, _messages = declare(program(with_work_group), "VMDZ4420")
    _again, anchor, _more = resolve(updated)

    assert anchor.group == "WS-TE-WORK"
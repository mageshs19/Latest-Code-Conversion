from __future__ import annotations


def test_fetch_paragraph_does_not_initialize_the_dclgen_group(fetch):
    assert not any(body.startswith("INITIALIZE") for body in fetch())


def test_fetch_paragraph_rearms_the_not_eoc_flag(fetch, names):
    assert f"SET {names['cursor']}-NOT-EOC TO TRUE" in fetch()


def test_fetch_paragraph_still_issues_the_fetch(fetch, names):
    assert f"FETCH {names['cursor']}" in fetch()


def test_host_group_is_read_from_the_of_form(fetch, names):
    lines = fetch(host_variables=[f"DA-CPTAFS-479BFAS OF {names['group']}"])
    assert f"SET {names['cursor']}-NOT-EOC TO TRUE" in lines


def test_no_empty_initialize_when_the_group_cannot_be_derived(fetch, names):
    lines = fetch(host_variables=["WS-UNQUALIFIED-FIELD"])
    assert not any(body.startswith("INITIALIZE") for body in lines)
    assert f"SET {names['cursor']}-NOT-EOC TO TRUE" in lines


def test_open_paragraph_gains_no_initialize(cursor_paragraph, names):
    lines = cursor_paragraph("open_paragraph", names["open_paragraph"])
    assert not any(body.startswith("INITIALIZE") for body in lines)


def test_close_paragraph_gains_no_initialize(cursor_paragraph, names):
    lines = cursor_paragraph("close_paragraph", names["close_paragraph"])
    assert not any(body.startswith("INITIALIZE") for body in lines)


def test_paragraph_is_one_sentence(fetch):
    lines = fetch()
    assert lines[-1] == "."
    assert lines.count(".") == 1


def test_the_fetch_builder_shares_the_facade_collaborators(paragraphs):
    assert paragraphs.fetch_builder.error_branch is paragraphs.error_branch
    assert paragraphs.fetch_builder.sql_location is paragraphs.sql_location
    assert paragraphs.fetch_builder.blocks is paragraphs.blocks
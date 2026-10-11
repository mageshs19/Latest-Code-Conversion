from __future__ import annotations


def test_a_parent_fetch_counts_rows(fetch, names):
    lines = fetch(table_name=names["table"], is_parent_cursor=True)
    assert any(body.startswith("ADD 1 TO WS-NB-") for body in lines)


def test_a_child_fetch_does_not_count_rows(fetch):
    lines = fetch(
        cursor_name="DZEVEFC1",
        paragraph_name="820-FETCH-DZEVEFC1",
        table_name="DZEVEFTV",
        is_parent_cursor=False,
    )
    assert not any(body.startswith("ADD 1 TO") for body in lines)


def test_no_counter_without_a_table(fetch):
    lines = fetch(table_name="", is_parent_cursor=True)
    assert not any(body.startswith("ADD 1 TO") for body in lines)


def test_label_fallback_is_reported_when_no_repository_is_wired(
    paragraphs, names
):
    paragraphs.fetch_paragraph(
        cursor_name="DZEVEFC1",
        paragraph_name="820-FETCH-DZEVEFC1",
        host_variables=names["hosts"],
        sql_error_paragraph=names["sql_error"],
        where_conditions=[
            f"CT_RKTPROD_479BEFF = :{names['group']}.CT-RKTPROD-479BEFF"
        ],
        is_parent_cursor=False,
    )

    assert paragraphs.messages
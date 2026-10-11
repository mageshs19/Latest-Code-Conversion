from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_spec import CursorSpec


def test_cursor_order_is_read_from_the_spec_dict(names):
    built = CursorSpec.read(
        {"cursor_name": names["cursor"], "cursor_order": 3}
    )
    assert built.cursor_order == 3


def test_missing_cursor_order_falls_back_to_list_position():
    specs = CursorSpec.read_all(
        [{"cursor_name": "C1"}, {"cursor_name": "C2"}]
    )
    assert [built.cursor_order for built in specs] == [0, 1]


def test_a_malformed_cursor_order_never_raises():
    assert CursorSpec.read(
        {"cursor_order": "not-a-number"}, 7
    ).cursor_order == 7
    assert CursorSpec.read({"cursor_order": -1}, 4).cursor_order == 4
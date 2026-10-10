from converter.generators.db2_infrastructure.spec_builder.cursor_spec_builder import (
    CursorSpecBuilder,
)


def test_builder_construction_does_not_require_line_utils(owner_without_line_utils):
    builder = CursorSpecBuilder(owner_without_line_utils)

    assert builder.messages == []


def test_reporter_is_created_only_when_include_names_is_called(
    owner_with_line_utils,
):
    builder = CursorSpecBuilder(owner_with_line_utils)

    assert builder._reporter is None

    builder.include_names([])

    assert builder._reporter is not None
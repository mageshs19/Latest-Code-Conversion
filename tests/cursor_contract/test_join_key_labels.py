from __future__ import annotations

import pytest

from converter.generators.cursor_paragraph.join_key_label_resolver import (
    JoinKeyLabelResolver,
)

GROUP = "DCLDZBEFFTV"
COLUMN = "CT_RKTPROD_479BEFF"
HOST = "CT-RKTPROD-479BEFF"
MAPPED_NAME = "CT-RK-TPROD"


class FakeRepository:
    def __init__(self, rows: dict) -> None:
        self.rows = {
            (table.upper(), column.upper()): value
            for (table, column), value in rows.items()
        }

    def cobol_field_for_column(self, table_name: str, column_name: str):
        return self.rows.get(
            (str(table_name).upper(), str(column_name).upper()), ""
        )


@pytest.fixture
def mapped() -> JoinKeyLabelResolver:
    return JoinKeyLabelResolver(
        FakeRepository({("DZBEFFTB", COLUMN): "  04  CT-RK-TPROD       "})
    )


def test_the_dclgen_group_resolves_to_the_mapping_table(mapped):
    assert "DZBEFFTB" in mapped.candidate_tables("DZBEFFTV")


def test_the_label_comes_from_sheet_mapping(mapped):
    label = mapped.label_for(
        table=mapped.table_of(GROUP), column=COLUMN, host=HOST
    )
    assert label == MAPPED_NAME


def test_the_level_prefix_is_stripped(mapped):
    label = mapped.label_for(
        table=mapped.table_of(GROUP), column=COLUMN, host=HOST
    )
    assert not label.startswith("04")


def test_a_successful_lookup_reports_nothing(mapped):
    mapped.label_for(table=mapped.table_of(GROUP), column=COLUMN, host=HOST)
    assert mapped.messages == []


def test_a_missing_row_falls_back_and_reports():
    resolver = JoinKeyLabelResolver(FakeRepository({}))
    label = resolver.label_for(
        table=resolver.table_of(GROUP), column=COLUMN, host=HOST
    )

    assert label == HOST
    assert resolver.messages


def test_no_repository_falls_back_and_reports():
    resolver = JoinKeyLabelResolver()
    label = resolver.label_for(
        table=resolver.table_of(GROUP), column=COLUMN, host=HOST
    )

    assert label == HOST
    assert resolver.messages


def test_an_empty_cobol_zone_is_not_a_label():
    resolver = JoinKeyLabelResolver(
        FakeRepository({("DZEVEFTB", COLUMN): "   "})
    )
    label = resolver.label_for(
        table=resolver.table_of("DCLDZEVEFTV"), column=COLUMN, host=HOST
    )

    assert label == HOST
    assert resolver.messages

def test_the_repository_lookup_does_not_raise(mapped):
    """Regression: cobol_field_for_column delegated to a non-existent
    attribute, so every lookup raised AttributeError, was caught, and
    fell back to the DCLGEN host name. A converter defect that looked
    exactly like a missing workbook cell.
    """
    label = mapped.label_for(
        table=mapped.table_of(GROUP), column=COLUMN, host=HOST
    )
    assert label == MAPPED_NAME
    assert mapped.messages == []


def test_a_builder_without_a_resolver_is_refused():
    """Regression: KeyDiagnosticsBuilder() was legal and substituted an
    empty resolver, degrading every label silently.
    """
    import pytest
    from converter.generators.cursor_paragraph.cursor_key_diagnostics import (
        KeyDiagnosticsBuilder,
    )

    with pytest.raises(ValueError):
        KeyDiagnosticsBuilder()
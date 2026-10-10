from converter.generators.db2_infrastructure.spec_builder.spec_parent_classifier import (
    SpecParentClassifier,
)


def test_cursor_without_where_is_parent_even_at_910():
    classifier = SpecParentClassifier()

    assert classifier.is_parent([], "910-FETCH-DZBFASC1") is True


def test_cursor_with_where_is_child_even_at_710():
    classifier = SpecParentClassifier()

    assert classifier.is_parent(
        ["NR_CIO_479BFAS = : DCLPARENT.NR-CIO"],
        "710-FETCH-DZBFASC1",
    ) is False
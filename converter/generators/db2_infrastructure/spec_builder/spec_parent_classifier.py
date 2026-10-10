"""Classifies a cursor as parent or child."""

from __future__ import annotations

from rules.cursor_spec import (
    CLASSIFY_PARENT_BY_ABSENT_WHERE,
    PARAGRAPH_NUMBER_SEPARATOR,
    PARENT_CURSOR_OPEN_NUMBER,
)

PARENT_SERIES_DIGIT = str(PARENT_CURSOR_OPEN_NUMBER)[0]


class SpecParentClassifier:
    """A cursor without predicates is the driving parent cursor."""

    def is_parent(
        self,
        where_conditions: list[str],
        fetch_paragraph: str,
    ) -> bool:
        if CLASSIFY_PARENT_BY_ABSENT_WHERE:
            return not where_conditions

        return self._legacy_series_result(fetch_paragraph)

    @staticmethod
    def _legacy_series_result(fetch_paragraph: str) -> bool:
        """Compatibility-only fallback for historical output comparison."""
        number = str(fetch_paragraph or "").split(
            PARAGRAPH_NUMBER_SEPARATOR,
            1,
        )[0]
        return bool(number) and number[:1] == PARENT_SERIES_DIGIT


__all__ = ["SpecParentClassifier"]
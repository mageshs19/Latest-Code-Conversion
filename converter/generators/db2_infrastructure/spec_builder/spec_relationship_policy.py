"""Creates safe relationship predicates for child cursor specifications."""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import SPEC_MESSAGES


class SpecRelationshipPolicy:
    """Build predicates once and refuse joins with unpopulated parent hosts."""

    def __init__(self, relationship_resolver, where_builder) -> None:
        self.relationship_resolver = relationship_resolver
        self.where_builder = where_builder
        self.messages: list[str] = []

    def where_conditions(
        self,
        record: str,
        navigated_records: set[str],
        lrf_cursors: dict,
    ) -> list[str]:
        """Return one de-duplicated predicate list for a child record."""
        relationship = self.relationship_resolver.resolve_for_child_record(
            record
        )
        conditions = list(getattr(relationship, "conditions", []) or [])
        if not conditions:
            return []

        parent = NameNormalizer.normalize(
            getattr(relationship, "parent_record", "")
        )
        if parent and parent not in navigated_records:
            self._log(
                "parent_not_navigated",
                record=record,
                parent=parent,
            )
            return []

        predicates = self.where_builder.predicates(conditions)

        if record in lrf_cursors and predicates:
            self._log(
                "lrf_where_already_present",
                record=record,
                count=len(predicates),
            )

        return predicates

    def _log(self, key: str, **fields) -> None:
        template = SPEC_MESSAGES.get(key, "")
        if not template:
            return

        try:
            self.messages.append(template.format(**fields))
        except (KeyError, IndexError):
            return


__all__ = ["SpecRelationshipPolicy"]
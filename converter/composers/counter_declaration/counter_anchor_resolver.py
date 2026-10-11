from __future__ import annotations

from converter.composers.counter_declaration.counter_anchor import (
    CounterAnchor,
    CounterAnchorFinder,
)
from converter.composers.counter_declaration.counter_line_factory import (
    CounterLineFactory,
)
from converter.services.generated_field_anchor import (
    GeneratedFieldAnchorResolver,
)
from converter.services.working_storage_group_selector import (
    WorkingStorageGroupSelector,
)
from rules.structural_safety_rules import (
    ENFORCE_SAFE_COUNTER_GROUP,
    STRUCTURAL_SAFETY_MESSAGES,
)


class CounterAnchorResolver:

    def __init__(
        self,
        line_factory: CounterLineFactory | None = None,
        selector: WorkingStorageGroupSelector | None = None,
        finder: CounterAnchorFinder | None = None,
        field_anchor: GeneratedFieldAnchorResolver | None = None,
    ) -> None:
        self.lines = line_factory or CounterLineFactory()
        self.selector = selector or WorkingStorageGroupSelector(
            fixed_format=self.lines.fixed_format,
        )
        self.finder = finder or CounterAnchorFinder(self.lines)
        self.field_anchor = field_anchor or GeneratedFieldAnchorResolver(
            line_factory=self.lines,
            selector=self.selector,
        )
        self.messages: list[str] = []

    def resolve(
        self,
        lines: list[str],
    ) -> tuple[list[str], CounterAnchor | None]:
        self.messages = []

        if not ENFORCE_SAFE_COUNTER_GROUP:
            layout = self.selector.analyze(lines)
            group = layout.groups[0] if layout.groups else None
            if group is None:
                return lines, None
            return lines, self.finder.anchor_for(
                lines, group.header_index, group.name
            )

        updated, anchor = self.field_anchor.resolve(lines)
        self.messages.extend(self.field_anchor.messages)

        if not anchor.is_usable:
            return list(lines), None

        return updated, CounterAnchor(
            insert_index=anchor.insert_index,
            template_line=anchor.template_line,
            level=anchor.level,
            indent=anchor.indent,
            group=anchor.group,
        )

    def _log(self, key: str, **values) -> None:
        template = STRUCTURAL_SAFETY_MESSAGES.get(str(key or ""), "")
        if template:
            self.messages.append(template.format(**values))


__all__ = ["CounterAnchorResolver"]
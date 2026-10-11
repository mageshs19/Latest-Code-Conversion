from __future__ import annotations

from dataclasses import dataclass

from converter.services.working_storage_group_selector import (
    WorkingStorageGroupSelector,
)
from rules.structural_safety_rules import (
    GENERATED_FIELD_CHILD_INDENT,
    GENERATED_FIELD_CHILD_LEVEL,
    GENERATED_FIELD_GROUP_ALIASES,
    GENERATED_FIELD_GROUP_MARKER,
    GENERATED_FIELD_GROUP_NAME,
    GENERATED_FIELD_GROUP_TEMPLATE,
    PREFERRED_WORK_GROUP_NAMES,
    STRUCTURAL_SAFETY_MESSAGES,
    UNIFY_GENERATED_FIELD_GROUP,
)

CREATED_GROUP_OFFSET = 3


@dataclass(frozen=True)
class FieldAnchor:
    insert_index: int = -1
    template_line: str = ""
    level: str = ""
    indent: str = ""
    group: str = ""
    created: bool = False

    @property
    def is_usable(self) -> bool:
        return self.insert_index >= 0 and bool(self.level)


class GeneratedFieldAnchorResolver:

    def __init__(
        self,
        line_factory=None,
        selector: WorkingStorageGroupSelector | None = None,
    ) -> None:
        if line_factory is None:
            from converter.composers.counter_declaration.counter_line_factory import (
                CounterLineFactory,
            )

            line_factory = CounterLineFactory()
        self.lines = line_factory
        self.selector = selector or WorkingStorageGroupSelector(
            fixed_format=getattr(self.lines, "fixed_format", None),
        )
        self.messages: list[str] = []

    def resolve(self, lines: list[str]) -> tuple[list[str], FieldAnchor]:
        self.messages = []

        if not UNIFY_GENERATED_FIELD_GROUP:
            return list(lines), FieldAnchor()

        layout = self.selector.analyze(lines)

        anchor = self._from_names(lines, layout, PREFERRED_WORK_GROUP_NAMES)
        if anchor is not None:
            self._log("field_group_reused", group=anchor.group)
            return list(lines), anchor

        anchor = self._from_names(lines, layout, GENERATED_FIELD_GROUP_ALIASES)
        if anchor is not None:
            self._log("field_group_reused", group=anchor.group)
            return list(lines), anchor

        self._report_refusals(layout)

        if layout.working_storage_index < 0:
            self._log("field_group_no_section")
            return list(lines), FieldAnchor()

        return self._create_group(lines, layout.boundary_index)

    def _from_names(self, lines, layout, names) -> FieldAnchor | None:
        group = layout.named(names)
        if group is None:
            return None
        return self._anchor_for(lines, group)

    def _anchor_for(self, lines, group) -> FieldAnchor | None:
        if not group.can_take_child:
            return None

        index = group.insert_index
        if index < 0 or index > len(lines):
            return None

        if group.has_children:
            template = lines[group.first_child_index]
            return FieldAnchor(
                insert_index=index,
                template_line=template,
                level=group.child_level,
                indent=self.lines.body_indent(template),
                group=group.name,
            )

        return FieldAnchor(
            insert_index=index,
            template_line=lines[group.header_index],
            level=GENERATED_FIELD_CHILD_LEVEL,
            indent=GENERATED_FIELD_CHILD_INDENT,
            group=group.name,
        )
    
    def _create_group(
        self,
        lines: list[str],
        boundary_index: int,
    ) -> tuple[list[str], FieldAnchor]:
        insert_at = boundary_index
        if insert_at < 0 or insert_at > len(lines):
            insert_at = len(lines)

        reference = lines[max(0, insert_at - 1)] if lines else ""
        marker = self.lines.comment(reference, GENERATED_FIELD_GROUP_MARKER)
        header = self.lines.statement(
            reference,
            GENERATED_FIELD_GROUP_TEMPLATE.format(
                name=GENERATED_FIELD_GROUP_NAME,
            ),
        )

        updated = lines[:insert_at] + ["", marker, header] + lines[insert_at:]
        self._log("field_group_created", group=GENERATED_FIELD_GROUP_NAME)

        return updated, FieldAnchor(
            insert_index=insert_at + CREATED_GROUP_OFFSET,
            template_line=header,
            level=GENERATED_FIELD_CHILD_LEVEL,
            indent=GENERATED_FIELD_CHILD_INDENT,
            group=GENERATED_FIELD_GROUP_NAME,
            created=True,
        )

    def _report_refusals(self, layout) -> None:
        for group in layout.groups:
            if group.is_record_layout:
                self._log("counter_group_rejected", group=group.name)
        for group in layout.childless_safe():
            self._log("field_group_childless", group=group.name)

    def _log(self, key: str, **values) -> None:
        template = STRUCTURAL_SAFETY_MESSAGES.get(str(key or ""), "")
        if not template:
            return
        try:
            self.messages.append(template.format(**values))
        except (IndexError, KeyError):
            self.messages.append(f"{template} [{key}: {values}]")


__all__ = ["FieldAnchor", "GeneratedFieldAnchorResolver"]
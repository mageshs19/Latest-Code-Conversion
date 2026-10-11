from __future__ import annotations

from dataclasses import dataclass, field

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.structural_safety_patterns import (
    FD_PATTERN,
    FILE_SECTION_PATTERN,
    LEVEL_01_PATTERN,
    LINKAGE_SECTION_PATTERN,
    MOVE_WHOLE_GROUP_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
    READ_INTO_PATTERN,
    RECORD_VERB_PATTERN,
    SUBORDINATE_LEVEL_PATTERN,
    WORKING_STORAGE_PATTERN,
    WRITE_FROM_PATTERN,
)

COMMENT_PREFIXES = ("*", "/")
PICTURE_TOKENS = (" PIC ", " PIC(", " PICTURE ", " PICTURE(")


@dataclass
class WorkingStorageGroup:
    name: str = ""
    header_index: int = -1
    first_child_index: int = -1
    last_child_index: int = -1
    child_level: str = ""
    is_record_layout: bool = False
    is_elementary: bool = False

    @property
    def has_children(self) -> bool:
        return self.first_child_index >= 0 and bool(self.child_level)

    @property
    def is_safe(self) -> bool:
        return bool(self.name) and not self.is_record_layout

    @property
    def can_take_child(self) -> bool:
        return self.is_safe and not self.is_elementary

    @property
    def insert_index(self) -> int:
        if self.last_child_index >= 0:
            return self.last_child_index + 1
        return self.header_index + 1


@dataclass
class WorkingStorageLayout:
    groups: list[WorkingStorageGroup] = field(default_factory=list)
    working_storage_index: int = -1
    boundary_index: int = -1

    def safe_groups(self) -> list[WorkingStorageGroup]:
        return [group for group in self.groups if group.is_safe]

    def usable_groups(self) -> list[WorkingStorageGroup]:
        return [group for group in self.groups if group.can_take_child]

    def named(self, names) -> WorkingStorageGroup | None:
        wanted = [str(name or "").upper() for name in (names or ())]
        for name in wanted:
            for group in self.groups:
                if group.name.upper() == name and group.can_take_child:
                    return group
        return None

    def childless_safe(self) -> list[WorkingStorageGroup]:
        return [
            group for group in self.groups
            if group.is_safe and not group.can_take_child
        ]


class WorkingStorageGroupSelector:

    def __init__(
        self,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.fixed_format = fixed_format or FixedFormatLineService()

    def analyze(self, lines: list[str]) -> WorkingStorageLayout:
        layout = WorkingStorageLayout()
        record_names = self._record_layout_names(lines)

        in_working_storage = False
        in_file_section = False
        current: WorkingStorageGroup | None = None

        for index, line in enumerate(lines):
            body = self._logical(line)
            if not body or self._is_comment(body):
                continue

            if FILE_SECTION_PATTERN.match(body):
                in_file_section = True
                in_working_storage = False
                continue

            if WORKING_STORAGE_PATTERN.match(body):
                in_file_section = False
                in_working_storage = True
                layout.working_storage_index = index
                continue

            if LINKAGE_SECTION_PATTERN.match(body) or (
                PROCEDURE_DIVISION_PATTERN.match(body)
            ):
                layout.boundary_index = index
                break

            if in_file_section or FD_PATTERN.match(body):
                continue

            if not in_working_storage:
                continue

            match = LEVEL_01_PATTERN.match(body)
            if match:
                name = match.group("name").upper()
                current = WorkingStorageGroup(
                    name=name,
                    header_index=index,
                    is_record_layout=name in record_names,
                    is_elementary=self._has_picture(body),
                )
                layout.groups.append(current)
                continue

            child = SUBORDINATE_LEVEL_PATTERN.match(body)
            if child and current is not None:
                current.last_child_index = index
                if current.first_child_index < 0:
                    current.first_child_index = index
                if not current.child_level:
                    current.child_level = child.group("level")

        if layout.boundary_index < 0:
            layout.boundary_index = len(lines)

        return layout

    def select(self, lines: list[str]) -> WorkingStorageGroup | None:
        usable = self.analyze(lines).usable_groups()
        return usable[-1] if usable else None

    def select_named(
        self,
        lines: list[str],
        names,
    ) -> WorkingStorageGroup | None:
        return self.analyze(lines).named(names)

    def _record_layout_names(self, lines: list[str]) -> set[str]:
        names: set[str] = set()
        in_file_section = False

        for line in lines:
            body = self._logical(line)
            if not body or self._is_comment(body):
                continue

            if FILE_SECTION_PATTERN.match(body):
                in_file_section = True
            elif WORKING_STORAGE_PATTERN.match(body):
                in_file_section = False

            if in_file_section:
                match = LEVEL_01_PATTERN.match(body)
                if match:
                    names.add(match.group("name").upper())

            match = RECORD_VERB_PATTERN.match(body)
            if match:
                names.add(match.group("name").upper())

            for pattern in (
                WRITE_FROM_PATTERN,
                READ_INTO_PATTERN,
                MOVE_WHOLE_GROUP_PATTERN,
            ):
                found = pattern.search(body)
                if found:
                    names.add(found.group("name").upper())

        return names

    def _logical(self, line: str) -> str:
        try:
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:  # noqa: BLE001
            return str(line or "").strip()

    @staticmethod
    def _has_picture(body: str) -> bool:
        text = f" {str(body or '').upper()} "
        return any(token in text for token in PICTURE_TOKENS)

    @staticmethod
    def _is_comment(body: str) -> bool:
        return body.startswith(COMMENT_PREFIXES)


__all__ = [
    "WorkingStorageGroup",
    "WorkingStorageLayout",
    "WorkingStorageGroupSelector",
]
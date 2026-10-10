# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_reporter.py
# ACTION: REPLACE ENTIRE FILE
"""Include names and spec-quality diagnostics."""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import (
    SPEC_CURSOR_NAME,
    SPEC_HOST_VARIABLES,
    SPEC_MESSAGES,
    SPEC_RECORD_NAME,
    SPEC_SELECT_COLUMNS,
    SPEC_TABLE_NAME,
)


class SpecReporter:
    """Reads finished specs. Changes nothing."""

    def __init__(self, line_utils) -> None:
        self.line_utils = line_utils

    def include_names(self, specs: list[dict[str, object]]) -> list[str]:
        output: list[str] = []
        seen: set[str] = set()

        for spec in specs or []:
            table = NameNormalizer.normalize(
                str(spec.get(SPEC_TABLE_NAME, ""))
            )
            if not table:
                continue

            include = self.line_utils.normalize_include_name(table)
            if not include or include in seen:
                continue

            seen.add(include)
            output.append(include)

        return output

    @staticmethod
    def messages(specs: list[dict[str, object]]) -> list[str]:
        output: list[str] = []

        for spec in specs or []:
            cursor = str(spec.get(SPEC_CURSOR_NAME, ""))
            record = str(spec.get(SPEC_RECORD_NAME, ""))

            checks = (
                ("no_table", spec.get(SPEC_TABLE_NAME, "")),
                ("no_select_columns", spec.get(SPEC_SELECT_COLUMNS, [])),
                ("no_host_variables", spec.get(SPEC_HOST_VARIABLES, [])),
            )

            for key, value in checks:
                if value:
                    continue
                template = SPEC_MESSAGES.get(key, "")
                if template:
                    output.append(
                        template.format(cursor=cursor, record=record)
                    )

        return output


__all__ = ["SpecReporter"]
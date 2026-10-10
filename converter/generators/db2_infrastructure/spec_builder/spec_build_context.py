"""Immutable input collected once for one cursor-spec build run."""

from __future__ import annotations

from dataclasses import dataclass

from converter.domain.models import IdmsOperation


@dataclass(frozen=True)
class SpecBuildContext:
    """Inputs shared by all cursor specifications in one program."""

    operations: list[IdmsOperation]
    field_usage_analysis: object
    navigated_records: set[str]
    materialised_records: set[str]
    lrf_cursors: dict

    @classmethod
    def create(
        cls,
        operations: list[IdmsOperation] | None,
        cobol_text: str,
        field_usage_analysis,
        navigation,
        lrf,
    ) -> "SpecBuildContext":
        return cls(
            operations=list(operations or []),
            field_usage_analysis=field_usage_analysis,
            navigated_records=navigation.navigated_records(operations or []),
            materialised_records=navigation.materialised_records(cobol_text),
            lrf_cursors=lrf.cursors(cobol_text),
        )


__all__ = ["SpecBuildContext"]
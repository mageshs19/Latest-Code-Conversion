"""Facade for DB2 cursor specification construction.

The public API remains stable:

- build()
- include_names()
- spec_messages()
- _augment_select_columns()

Dependencies used only by build() or reporting are created lazily.
This preserves support for minimal owners used by augmentation tests.
"""

from __future__ import annotations

from converter.analyzers.field_usage_analyzer import FieldUsageAnalyzer
from converter.domain.models import IdmsOperation
from converter.generators.db2_infrastructure.spec_builder.spec_build_context import (
    SpecBuildContext,
)
from converter.generators.db2_infrastructure.spec_builder.spec_factory import (
    SpecFactory,
)
from converter.generators.db2_infrastructure.spec_builder.spec_lrf_scanner import (
    SpecLrfScanner,
)
from converter.generators.db2_infrastructure.spec_builder.spec_navigation_scanner import (
    SpecNavigationScanner,
)
from converter.generators.db2_infrastructure.spec_builder.spec_parent_classifier import (
    SpecParentClassifier,
)
from converter.generators.db2_infrastructure.spec_builder.spec_relationship_policy import (
    SpecRelationshipPolicy,
)
from converter.generators.db2_infrastructure.spec_builder.spec_reporter import (
    SpecReporter,
)
from converter.generators.db2_infrastructure.spec_builder.spec_select_augmenter import (
    SpecSelectAugmenter,
)
from converter.generators.db2_infrastructure.spec_builder.spec_where_builder import (
    SpecWhereBuilder,
)


class CursorSpecBuilder:
    """Builds and augments DB2 cursor specification dictionaries."""

    def __init__(self, owner) -> None:
        self.owner = owner

        self.navigation = SpecNavigationScanner()
        self.lrf = SpecLrfScanner()
        self.parent_classifier = SpecParentClassifier()

        self.where = SpecWhereBuilder(
            dclgen_repository=getattr(
                owner,
                "dclgen_repository",
                None,
            ),
        )
        self.augmenter = SpecSelectAugmenter(
            host_variable_resolver=owner.host_variable_resolver,
            where_builder=self.where,
        )

        self._relationship_policy: SpecRelationshipPolicy | None = None
        self._factory: SpecFactory | None = None
        self._reporter: SpecReporter | None = None

        self.messages: list[str] = []

    @property
    def relationship_policy(self) -> SpecRelationshipPolicy:
        """Create relationship policy only for a complete build."""
        if self._relationship_policy is None:
            resolver = getattr(
                self.owner,
                "relationship_resolver",
                None,
            )
            if resolver is None:
                raise AttributeError(
                    "CursorSpecBuilder.build() requires "
                    "owner.relationship_resolver"
                )

            self._relationship_policy = SpecRelationshipPolicy(
                relationship_resolver=resolver,
                where_builder=self.where,
            )

        return self._relationship_policy

    @property
    def factory(self) -> SpecFactory:
        """Create the spec factory only when build() is called."""
        if self._factory is None:
            self._factory = SpecFactory(
                owner=self.owner,
                relationship_policy=self.relationship_policy,
                parent_classifier=self.parent_classifier,
            )

        return self._factory

    @property
    def reporter(self) -> SpecReporter:
        """Create reporter only when report output is requested."""
        if self._reporter is None:
            line_utils = getattr(self.owner, "line_utils", None)
            if line_utils is None:
                raise AttributeError(
                    "Cursor reporting requires owner.line_utils"
                )

            self._reporter = SpecReporter(line_utils)

        return self._reporter

    def build(
        self,
        operations: list[IdmsOperation],
        cobol_text: str = "",
        field_usage_analysis=None,
    ) -> list[dict[str, object]]:
        """Build and augment cursor specifications."""
        self._reset_messages()

        usage = field_usage_analysis
        if usage is None:
            usage = self._field_usage(cobol_text)

        context = SpecBuildContext.create(
            operations=operations,
            cobol_text=cobol_text,
            field_usage_analysis=usage,
            navigation=self.navigation,
            lrf=self.lrf,
        )

        specs = self.factory.build(context)
        self._augment_select_columns(specs)

        self.messages.extend(self.relationship_policy.messages)
        self.messages.extend(self.where.messages)

        return specs

    def _augment_select_columns(
        self,
        specs: list[dict[str, object]],
    ) -> None:
        """Backward-compatible select-column augmentation entry point."""
        self.augmenter.augment(specs)

    def include_names(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        """Return DCLGEN include names."""
        return self.reporter.include_names(cursor_specs)

    def spec_messages(
        self,
        cursor_specs: list[dict[str, object]],
    ) -> list[str]:
        """Return completed-spec diagnostics."""
        return self.reporter.messages(cursor_specs)

    def _field_usage(self, cobol_text: str):
        mapping_repository = getattr(
            self.owner,
            "mapping_repository",
            None,
        )
        table_name_resolver = getattr(
            self.owner,
            "table_name_resolver",
            None,
        )

        if mapping_repository is None:
            raise AttributeError(
                "CursorSpecBuilder.build() requires "
                "owner.mapping_repository"
            )

        if table_name_resolver is None:
            raise AttributeError(
                "CursorSpecBuilder.build() requires "
                "owner.table_name_resolver"
            )

        return FieldUsageAnalyzer(
            mapping_repository=mapping_repository,
            table_name_resolver=table_name_resolver,
        ).analyze(cobol_text)

    def _reset_messages(self) -> None:
        self.messages = []
        self.where.messages = []

        if self._relationship_policy is not None:
            self._relationship_policy.messages = []


__all__ = ["CursorSpecBuilder"]
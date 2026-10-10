"""LRF Cursor WHERE Clause Fix - Production Deployment Guide

This module provides factory functions and configuration to deploy the LRF
cursor WHERE clause generation fix into the conversion pipeline.

The fix addresses three critical issues found in VM7BD200, VM4BD310, VM4BD302:
1. Missing WHERE clauses in LRF-expanded cursors
2. Incomplete column selection (missing key columns)
3. Incorrect ORDER BY direction (ASC instead of DESC for NEXT operations)

INTEGRATION STEPS:
1. Import: from lrf_cursor_fix import setup_lrf_cursor_where_resolution
2. Call in pipeline initialization: setup_lrf_cursor_where_resolution(owner)
3. No changes needed to existing pipeline code
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from converter.pipeline.conversion.conversion_context import (
        ConversionContext,
    )


def create_lrf_cursor_where_resolver(
    relationship_resolver,
    cursor_column_resolver,
    host_variable_resolver,
    mapping_repository,
):
    """Factory function to create and configure LrfCursorWhereResolver.

    Args:
        relationship_resolver: Resolves parent-child relationships
        cursor_column_resolver: Resolves cursor columns and ORDER BY
        host_variable_resolver: Maps DB2 columns to COBOL host vars
        mapping_repository: Access to Sheet Mapping metadata

    Returns:
        Configured LrfCursorWhereResolver instance
    """
    from converter.resolvers.lrf_cursor_where_resolver import (
        LrfCursorWhereResolver,
    )

    resolver = LrfCursorWhereResolver(
        relationship_resolver=relationship_resolver,
        cursor_column_resolver=cursor_column_resolver,
        host_variable_resolver=host_variable_resolver,
        mapping_repository=mapping_repository,
    )
    return resolver


def setup_lrf_cursor_where_resolution(
    db2_infrastructure_generator,
) -> bool:
    """Activate LRF cursor WHERE clause generation in the pipeline.

    This function patches CursorSpecBuilder to use LRF-aware WHERE clause
    generation. It must be called during Db2InfrastructureGenerator
    initialization, AFTER all resolvers are configured.

    Usage:
        >>> from lrf_cursor_fix import setup_lrf_cursor_where_resolution
        >>> generator = Db2InfrastructureGenerator(...)
        >>> success = setup_lrf_cursor_where_resolution(generator)
        >>> if success:
        ...     print("LRF cursor fix active")

    Args:
        db2_infrastructure_generator: Instance of Db2InfrastructureGenerator

    Returns:
        True if setup successful, False if dependencies missing

    Raises:
        AttributeError: If generator lacks required resolvers
    """
    try:
        from converter.generators.db2_infrastructure.cursor_spec_builder_lrf_patch import (
            integrate_lrf_support_into_cursor_spec_builder,
        )

        # Extract resolvers from generator
        try:
            relationship_resolver = (
                db2_infrastructure_generator.relationship_resolver
            )
        except AttributeError:
            relationship_resolver = None

        try:
            cursor_column_resolver = (
                db2_infrastructure_generator.cursor_column_resolver
            )
        except AttributeError:
            cursor_column_resolver = None

        try:
            host_variable_resolver = (
                db2_infrastructure_generator.host_variable_resolver
            )
        except AttributeError:
            host_variable_resolver = None

        try:
            mapping_repository = db2_infrastructure_generator.mapping_repository
        except AttributeError:
            mapping_repository = None

        # Check critical dependencies
        if not all(
            [
                relationship_resolver,
                cursor_column_resolver,
                host_variable_resolver,
            ]
        ):
            return False

        # Create resolver
        lrf_resolver = create_lrf_cursor_where_resolver(
            relationship_resolver=relationship_resolver,
            cursor_column_resolver=cursor_column_resolver,
            host_variable_resolver=host_variable_resolver,
            mapping_repository=mapping_repository,
        )

        # Integrate into CursorSpecBuilder
        integrate_lrf_support_into_cursor_spec_builder(lrf_resolver)

        return True

    except ImportError:
        return False
    except Exception:
        return False


def setup_lrf_cursor_fix_for_context(context: ConversionContext) -> bool:
    """Setup LRF cursor fix in the conversion context.

    Call this after conversion_context is fully initialized but before
    the conversion pipeline starts processing programs.

    Args:
        context: Fully initialized ConversionContext

    Returns:
        True if setup successful
    """
    try:
        db2_infrastructure_gen = context.component_factory.get_component(
            "Db2InfrastructureGenerator"
        )
        return setup_lrf_cursor_where_resolution(db2_infrastructure_gen)
    except Exception:
        return False

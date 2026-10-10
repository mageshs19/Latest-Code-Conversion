# LOCATION: converter/pipeline/lrf_host_variable_population.py
# ACTION: CREATE NEW FILE
"""Orchestrates LRF host variable population integration into the pipeline.

INTEGRATION POINTS
------------------
This module is called AFTER the main DB2 conversion pipeline:

    # In conversion_pipeline.py or factory:
    from converter.pipeline.lrf_host_variable_population import (
        setup_lrf_host_variable_population,
    )
    
    # After Db2InfrastructureGenerator and CursorParagraphGenerator
    setup_lrf_host_variable_population(
        cursor_paragraph_generator=generator,
        host_variable_resolver=host_var_resolver,
        table_name_resolver=table_resolver,
        cursor_name_resolver=cursor_resolver,
    )
    
    # Then when processing COBOL:
    cobol_with_init, messages = generator.augment_lrf_procedure_division(
        cobol_text=converted_cobol,
    )

RESPONSIBILITY
--------------
This module only coordinates component initialization and integration.
The actual code generation lives in LrfHostVariablePopulator.
"""

from __future__ import annotations

from typing import Optional

from converter.generators.lrf_host_variable_populator import (
    LrfHostVariablePopulator,
)


def setup_lrf_host_variable_population(
    cursor_paragraph_generator,
    host_variable_resolver=None,
    table_name_resolver=None,
    cursor_name_resolver=None,
    relationship_resolver=None,
    name_normalizer=None,
) -> bool:
    """Configure LRF host variable population in the cursor generator.

    Attaches the LrfHostVariablePopulator to the cursor generator so it
    can augment generated PROCEDURE DIVISION with host variable initialization.

    Returns True if successful, False if dependencies missing.
    """
    if not cursor_paragraph_generator:
        return False

    try:
        populator = LrfHostVariablePopulator(
            host_variable_resolver=host_variable_resolver,
            relationship_resolver=relationship_resolver,
            name_normalizer=name_normalizer,
        )

        # Inject into the generator for later use
        cursor_paragraph_generator._lrf_host_variable_populator = populator
        cursor_paragraph_generator._table_name_resolver = table_name_resolver
        cursor_paragraph_generator._cursor_name_resolver = cursor_name_resolver

        return True

    except Exception as e:  # noqa: BLE001
        # Silently fail if setup has issues; the converter continues
        # without LRF support
        return False


def augment_with_lrf_population(
    cursor_paragraph_generator,
    cobol_text: str,
) -> tuple[str, list[str]]:
    """Apply LRF host variable population to generated COBOL.

    Call this AFTER cursor_paragraph_generator.apply() has completed
    and injected all cursor paragraphs.

    Returns (modified_cobol, messages).
    """
    if not cursor_paragraph_generator:
        return cobol_text, []

    populator = getattr(
        cursor_paragraph_generator,
        "_lrf_host_variable_populator",
        None,
    )
    if not populator:
        # LRF support not configured
        return cobol_text, []

    try:
        # Inject host variable population code before cursor OPENs
        augmented_cobol, messages = populator.augment_procedure_division(
            cobol_text
        )
        return augmented_cobol, messages

    except Exception as e:  # noqa: BLE001
        # If augmentation fails, return original and note the error
        error_msg = f"[LRF-POPULATION] augmentation failed: {e}"
        return cobol_text, [error_msg]


class LrfHostVariablePopulationMixin:
    """Mixin to add LRF host variable population to CursorParagraphGenerator.

    Attach this to the cursor generator to add augmentation capability:

        generator._lrf_host_variable_populator = populator
        generator.augment_lrf_procedure_division(cobol_text)
    """

    _lrf_host_variable_populator: Optional[LrfHostVariablePopulator] = None
    _table_name_resolver = None
    _cursor_name_resolver = None

    def augment_lrf_procedure_division(
        self,
        cobol_text: str,
    ) -> tuple[str, list[str]]:
        """Apply LRF host variable population after main generation.

        Call AFTER apply() has completed:

            cobol, messages = generator.apply(...)
            cobol, aug_messages = generator.augment_lrf_procedure_division(cobol)
        """
        if not self._lrf_host_variable_populator:
            return cobol_text, []

        return self._lrf_host_variable_populator.augment_procedure_division(
            cobol_text
        )

"""Every entry point must import.

The full suite passed 500+ tests while

    ImportError: cannot import name 'RESTART_INSERT_QUERYNO'
                 from 'rules.update_restart_rules'

made the entire update conversion path unrunnable. No test imported the
runner, so deleting a constant that one module still read broke
production and nothing went red.

A unit test proves a unit works. Only an import proves the program can
start.
"""

from __future__ import annotations

import importlib

import pytest

ENTRY_POINTS = [
    "runners.run_update",
    "runners.update.update_postprocess_pipeline",
    "runners.update.update_program_converter",
    "runners.update.update_input_loader",
    "runners.batch.update_postprocess_pipeline",
    "runners.batch.program_converter",
    "converter.ui.conversion_actions",
    "converter.pipeline.conversion.conversion_pipeline",
    "converter.postprocess.update_program_enhancer",
    "converter.postprocess.cobol_update_standard_generator",
]


@pytest.mark.parametrize("module_name", ENTRY_POINTS)
def test_entry_point_imports(module_name: str) -> None:
    try:
        importlib.import_module(module_name)
    except ImportError as error:
        pytest.fail(f"{module_name} cannot be imported: {error}")
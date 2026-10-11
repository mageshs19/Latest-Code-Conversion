from __future__ import annotations

import logging

from converter.generators.enhancement.enhancement_pipeline import (
    ConverterEnhancementPipeline,
    enhance_converter_output,
    setup_pipeline_logging,
)
from converter.generators.enhancement.output_validator import (
    OutputValidator,
    validate_output,
)
from converter.generators.initialization.line_geometry import LineGeometry
from patterns.initialization_scope_patterns import (
    FETCH_PARAGRAPH_HEADER_PATTERN as FETCH_PARAGRAPH_PATTERN,
)

logger = logging.getLogger(__name__)

BODY_START = 7
BODY_END = 72


def _body(line: str) -> str:
    return LineGeometry.body(line)


def _is_comment(line: str) -> bool:
    return LineGeometry.is_comment(line)


__all__ = [
    "BODY_END",
    "BODY_START",
    "ConverterEnhancementPipeline",
    "FETCH_PARAGRAPH_PATTERN",
    "OutputValidator",
    "enhance_converter_output",
    "setup_pipeline_logging",
    "validate_output",
]
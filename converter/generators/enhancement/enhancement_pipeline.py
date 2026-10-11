from __future__ import annotations

import logging
from typing import Dict

from converter.generators.enhancement.output_validator import (
    OutputValidator,
)
from converter.generators.initialization.scope_initializer import (
    CursorScopedInitializer,
)
from converter.pipeline.conversion.conversion_layout_steps import (
    FinalSequenceResequencerService,
)

logger = logging.getLogger(__name__)

STEP_START = "[{program}] Starting converter enhancement pipeline"
STEP_DONE = "[{program}] Converter enhancement pipeline complete"
STEP_SCOPE = "[{program}] Step 1: Cursor scoped initialization"
STEP_MESSAGE = "[{program}] {message}"
STEP_GROUPS = "[{program}] Found {count} DCLGEN group(s)"
STEP_NO_CHANGE = "[{program}] Cursor scoped initialization made no change"
STEP_FAILED = "[{program}] Failed to scope initialization: {error}"
PIPELINE_FAILED = "[{program}] Error in converter enhancement pipeline: {error}"


class ConverterEnhancementPipeline:

    def __init__(self, program_text: str, program_id: str = "UNKNOWN") -> None:
        self.program_text = program_text
        self.program_id = program_id
        self.logger = logging.getLogger(__name__)

    def execute(self) -> str:
        result = self.program_text
        try:
            self.logger.info(STEP_START.format(program=self.program_id))
            result = self._step_scope_initialization(result)
            result = FinalSequenceResequencerService().resequence(result)
            self.logger.info(STEP_DONE.format(program=self.program_id))
            return result
        except Exception as error:
            self.logger.error(
                PIPELINE_FAILED.format(
                    program=self.program_id,
                    error=error,
                ),
                exc_info=True,
            )
            return self.program_text

    def _step_scope_initialization(self, program_text: str) -> str:
        self.logger.info(STEP_SCOPE.format(program=self.program_id))
        try:
            initializer = CursorScopedInitializer(program_text)
            result = initializer.process()

            for message in initializer.messages:
                self.logger.info(
                    STEP_MESSAGE.format(
                        program=self.program_id,
                        message=message,
                    )
                )

            self.logger.debug(
                STEP_GROUPS.format(
                    program=self.program_id,
                    count=len(initializer.dclgen_groups),
                )
            )

            if result == program_text and initializer.messages:
                self.logger.warning(
                    STEP_NO_CHANGE.format(program=self.program_id)
                )
            return result
        except Exception as error:
            self.logger.warning(
                STEP_FAILED.format(
                    program=self.program_id,
                    error=error,
                )
            )
            return program_text

    @staticmethod
    def validate_output(program_text: str) -> Dict[str, object]:
        return OutputValidator().validate(program_text)


def enhance_converter_output(
    program_text: str,
    program_id: str = "UNKNOWN",
) -> str:
    return ConverterEnhancementPipeline(program_text, program_id).execute()


def setup_pipeline_logging(log_level: int = logging.INFO) -> None:
    pipeline_logger = logging.getLogger(__name__)
    pipeline_logger.setLevel(log_level)
    if pipeline_logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
    )
    pipeline_logger.addHandler(handler)


__all__ = [
    "ConverterEnhancementPipeline",
    "enhance_converter_output",
    "setup_pipeline_logging",
]
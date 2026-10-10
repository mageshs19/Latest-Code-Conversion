"""
CONVERTER PIPELINE INTEGRATION

Post-processing orchestrator that applies production COBOL standards to
converter output.

Integration point - conversion_layout_pipeline.py, as the final step:

    pipeline = ConverterEnhancementPipeline(text, program_id)
    production_ready = pipeline.execute()
"""

from __future__ import annotations

import logging
import re

from .initialization_centralizer import InitializationCentralizer
from .working_storage_organizer import WorkingStorageOrganizer
from .procedure_division_organizer import ProcedureDivisionOrganizer
from converter.pipeline.conversion.conversion_layout_steps import (
    FinalSequenceResequencerService,
)


logger = logging.getLogger(__name__)

FETCH_PARAGRAPH_PATTERN = re.compile(
    r"^\d{3,6}-\w*FETCH\w*\s*\.$",
    re.IGNORECASE,
)

BODY_START = 7
BODY_END = 72


def _body(line: str) -> str:
    """Columns 8-72 of a fixed-format record, else the stripped line."""
    text = str(line or "").rstrip("\r\n")
    if not text:
        return ""
    if len(text) > BODY_START and text[:6].isdigit():
        return text[BODY_START:BODY_END].strip()
    return text.strip()


def _is_comment(line: str) -> bool:
    text = str(line or "")
    if len(text) > 6 and text[:6].isdigit():
        return text[6:7] in ("*", "/")
    return text.lstrip()[:1] in ("*", "/")


class ConverterEnhancementPipeline:
    """Enhances converter output for production."""

    def __init__(self, program_text: str, program_id: str = "UNKNOWN"):
        self.program_text = program_text
        self.program_id = program_id
        self.logger = logging.getLogger(__name__)

    def execute(self) -> str:
        """Run every enabled enhancement step, then resequence."""
        result = self.program_text

        try:
            self.logger.info(
                f"[{self.program_id}] Starting converter enhancement pipeline"
            )

            result = self._step_1_centralize_initialization(result)

            # Step 2 DISABLED - WorkingStorageOrganizer drops counter fields.
            # Step 3 DISABLED - ProcedureDivisionOrganizer rebuilds the whole
            # PROCEDURE DIVISION and re-breaks paragraph boundaries.

            result = FinalSequenceResequencerService().resequence(result)

            self.logger.info(
                f"[{self.program_id}] Converter enhancement pipeline complete"
            )
            return result

        except Exception as e:
            self.logger.error(
                f"[{self.program_id}] Error in converter enhancement "
                f"pipeline: {e}",
                exc_info=True,
            )
            return self.program_text

    def _step_1_centralize_initialization(self, program_text: str) -> str:
        """Consolidate DCLGEN INITIALIZE statements into 100-INITIALIZE.

        A REFUSAL returns the input unchanged and explains itself in
        .messages. Without surfacing those, a skipped or rolled-back pass
        is indistinguishable from a successful one.
        """
        self.logger.info(
            f"[{self.program_id}] Step 1: Centralizing initialization"
        )

        try:
            centralizer = InitializationCentralizer(program_text)
            result = centralizer.process()

            for message in centralizer.messages:
                self.logger.info(f"[{self.program_id}] {message}")

            self.logger.debug(
                f"[{self.program_id}] Found "
                f"{len(centralizer.dclgen_groups)} DCLGEN group(s)"
            )

            if result == program_text and centralizer.messages:
                self.logger.warning(
                    f"[{self.program_id}] Initialization centralization "
                    f"made no change"
                )

            return result

        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to centralize "
                f"initialization: {e}"
            )
            return program_text

    def _step_2_organize_working_storage(self, program_text: str) -> str:
        """Organize WORKING-STORAGE into standard sections. DISABLED."""
        self.logger.info(
            f"[{self.program_id}] Step 2: Organizing WORKING-STORAGE"
        )

        try:
            organizer = WorkingStorageOrganizer(program_text)
            result = organizer.reorganize()
            self.logger.debug(
                f"[{self.program_id}] WORKING-STORAGE sections: "
                + str({
                    section: len(organizer.sections[section])
                    for section in organizer.sections
                })
            )
            return result
        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to organize "
                f"WORKING-STORAGE: {e}"
            )
            return program_text

    def _step_3_organize_procedure_division(self, program_text: str) -> str:
        """Structure PROCEDURE DIVISION with standard flow. DISABLED."""
        self.logger.info(
            f"[{self.program_id}] Step 3: Organizing PROCEDURE DIVISION"
        )

        try:
            organizer = ProcedureDivisionOrganizer(program_text)
            result = organizer.organize()
            self.logger.debug(
                f"[{self.program_id}] Found "
                f"{len(organizer.paragraphs)} paragraphs"
            )
            return result
        except Exception as e:
            self.logger.warning(
                f"[{self.program_id}] Failed to organize PROCEDURE "
                f"DIVISION: {e}"
            )
            return program_text

    @staticmethod
    def validate_output(program_text: str) -> dict:
        """Validate that output meets production standards."""
        validation = {"is_valid": True, "issues": [], "warnings": []}

        lines = (
            str(program_text or "")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )
        bodies = [
            _body(line) for line in lines
            if not _is_comment(line) and _body(line)
        ]
        joined = "\n".join(bodies).upper()

        if "100-INITIALIZE." not in joined:
            validation["issues"].append("Missing 100-INITIALIZE paragraph")
            validation["is_valid"] = False

        if not any(
            body.upper().startswith("INITIALIZE DCL") for body in bodies
        ):
            validation["issues"].append(
                "No DCLGEN group is initialized anywhere in the program"
            )
            validation["is_valid"] = False

        if "PERFORM 100-INITIALIZE" not in joined:
            validation["issues"].append(
                "100-INITIALIZE is declared but never performed"
            )
            validation["is_valid"] = False

        for index, body in enumerate(bodies):
            if not FETCH_PARAGRAPH_PATTERN.match(body):
                continue
            window = bodies[index + 1:index + 6]
            offenders = [
                item for item in window
                if item.upper().startswith("INITIALIZE DCL")
            ]
            if offenders:
                validation["warnings"].append(
                    f"INITIALIZE found in fetch paragraph: {body}"
                )

        if "600-GET-TIMESTAMP." not in joined:
            validation["warnings"].append(
                "Missing 600-GET-TIMESTAMP paragraph"
            )

        if "500-DISPLAY-TOTALS." not in joined:
            validation["warnings"].append(
                "Missing 500-DISPLAY-TOTALS paragraph"
            )

        return validation


def enhance_converter_output(
    program_text: str,
    program_id: str = "UNKNOWN",
) -> str:
    """Enhance converter output for production."""
    pipeline = ConverterEnhancementPipeline(program_text, program_id)
    return pipeline.execute()


def setup_pipeline_logging(log_level=logging.INFO) -> None:
    """Attach a console handler to the pipeline logger."""
    pipeline_logger = logging.getLogger(__name__)
    pipeline_logger.setLevel(log_level)

    if not pipeline_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        )
        pipeline_logger.addHandler(handler)
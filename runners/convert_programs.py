# LOCATION: runners/convert_programs.py
# ACTION: REPLACE ENTIRE FILE
"""Converts every program in the configured folder, routed by PROGRAM KIND.

CORRECTION - every program was sent to the RETRIEVAL converter

run_conversion() imported convert_one_program from
runners.retrieval.retrieval_program_converter and called it for every
file, with no kind check anywhere in the chain. This module is what
mainframe/zowe_rules_pipeline.py drives:

    CONVERT_RUNNER = "runners/convert_programs.py"

so the production command

    python -m mainframe.zowe_pipeline all --from convert --to review

routed UPDATE programs through the retrieval path. Two consequences,
both observed on disk:

  1. The retrieval converter never calls enhance_update_program, so the
     update postprocess never ran. VMDZ1567 shipped with

         SET TS_UPDATE_479BFAR = :DCLDZBFARTV.TS-UPDATE-479BFAR
         SET ID_USERID_479BFAR = :DCLDZBFARTV.ID-USERID-479BFAR

     while NOTHING assigned either host variable, so DB2 received
     whatever the DCLGEN group happened to hold - silent data
     corruption on every updated row. The same pass also quotes a
     numeric literal moved to a CHAR host, so MOVE '1815' arrived as
     MOVE 1815.

  2. Only the retrieval converter substitutes the derived PROGRAM-ID
     for the file stem, which is why update programs appeared as
     VMDZ1567_*.cbl from this runner and VM1BD567_*.cbl from the batch
     runner - two files for one program, with different content.

The retrieval converter's docstring already says "Converts one
retrieval program". Nothing enforced it. This is the mirror of
UpdateProgramEnhancer CORRECTION 1, where "deliberately not used by
retrieval" was prose rather than code.

THE KIND IS MEASURED, NEVER ASSUMED

ProgramKindResolver().is_update() is the same resolver
UpdateProgramEnhancer uses for this exact decision. It reads the SOURCE,
before statement transformation, because the converted text no longer
carries the IDMS write verbs that prove the kind.

OUTPUT FOLDER IS DELIBERATELY SHARED

Both paths are given the SAME output_dir, so the Zowe review stage
continues to find every artefact in one place. Routing changes which
converter runs, not where its result lands.

THE ROUTE IS REPORTED

A silent dispatch is indistinguishable from the defect it replaces, so
every program prints the kind measured and the converter chosen.
"""

from __future__ import annotations

from pathlib import Path

from runners.retrieval.retrieval_environment import (
    bootstrap_sys_path,
)

SRC_DIR, PROJECT_ROOT = bootstrap_sys_path(Path(__file__))

from config.path_settings import (  # noqa: E402
    DEFAULT_RETRIEVAL_OUTPUT_DIR,
    DEFAULT_RETRIEVAL_PROGRAM_DIR,
    LOGS_DIR,
)
from converter.infrastructure.logger_factory import (  # noqa: E402
    LoggerFactory,
)
from converter.resolvers.program_kind_resolver import (  # noqa: E402
    ProgramKindResolver,
)
from runners.retrieval.retrieval_input_loader import (  # noqa: E402
    load_shared_inputs,
)
from runners.retrieval.retrieval_input_selector import (  # noqa: E402
    selected_program_paths,
    validate_inputs,
)
from runners.retrieval.retrieval_program_converter import (  # noqa: E402
    convert_one_program,
    resolve_target_program_id,
)
from runners.update.update_program_converter import (  # noqa: E402
    convert_one_program as convert_one_update_program,
)
from rules.retrieval_runner_messages import (  # noqa: E402
    BATCH_OUTPUT_FOLDER_TEMPLATE,
    BATCH_PROGRAM_COUNT_TEMPLATE,
    BATCH_PROGRAM_FOLDER_TEMPLATE,
    HEADER_RETRIEVAL_BATCH_SUMMARY,
    RULE_RETRIEVAL_BATCH_SUMMARY,
)
from rules.retrieval_runner_rules import RETRIEVAL_LOGGER_NAME  # noqa: E402

OUTPUT_DIR = DEFAULT_RETRIEVAL_OUTPUT_DIR

# Runner presentation only. No program, record, table or host variable
# name appears here.
ROUTE_TEMPLATE = "Routing {name}: measured {kind}; using the {kind} converter."
ROUTE_FAILED_TEMPLATE = (
    "Routing {name}: the source could not be read to measure its kind "
    "({reason}); using the retrieval converter. If this is an update "
    "program its audit host variables will NOT be populated."
)

KIND_UPDATE = "update"
KIND_RETRIEVAL = "retrieval"

__all__ = [
    "resolve_target_program_id",
    "validate_inputs",
    "load_shared_inputs",
    "convert_one_program",
    "measure_program_kind",
    "run_conversion",
]


def measure_program_kind(program_path: Path) -> str:
    """KIND_UPDATE or KIND_RETRIEVAL, measured from the SOURCE text.

    Reading fails open to retrieval - the previous behaviour - but says
    so, because a silent fallback is what this correction exists to
    remove.
    """
    try:
        source_text = Path(program_path).read_text(
            encoding="utf-8", errors="ignore"
        )
    except OSError as exc:  # noqa: BLE001 - reported, never silent
        print(
            ROUTE_FAILED_TEMPLATE.format(
                name=Path(program_path).name, reason=exc
            )
        )
        return KIND_RETRIEVAL

    measured, _messages = ProgramKindResolver().is_update(source_text)
    return KIND_UPDATE if measured else KIND_RETRIEVAL


def run_conversion() -> None:
    validate_inputs()

    logger = LoggerFactory.create_logger(
        name=RETRIEVAL_LOGGER_NAME,
        logs_dir=LOGS_DIR,
    )

    sheet_rows, dclgen_columns, copybook_fields, diagnostics = load_shared_inputs(
        logger
    )

    program_files = selected_program_paths()

    print("")
    print(HEADER_RETRIEVAL_BATCH_SUMMARY)
    print(RULE_RETRIEVAL_BATCH_SUMMARY)
    print(BATCH_PROGRAM_FOLDER_TEMPLATE.format(value=DEFAULT_RETRIEVAL_PROGRAM_DIR))
    print(BATCH_PROGRAM_COUNT_TEMPLATE.format(value=len(program_files)))
    print(BATCH_OUTPUT_FOLDER_TEMPLATE.format(value=OUTPUT_DIR))

    for program_path in program_files:
        kind = measure_program_kind(program_path)

        print(ROUTE_TEMPLATE.format(name=Path(program_path).name, kind=kind))
        logger.info(
            ROUTE_TEMPLATE.format(name=Path(program_path).name, kind=kind)
        )

        converter = (
            convert_one_update_program
            if kind == KIND_UPDATE
            else convert_one_program
        )

        converter(
            program_path=program_path,
            sheet_rows=sheet_rows,
            dclgen_columns=dclgen_columns,
            copybook_fields=copybook_fields,
            shared_diagnostics=diagnostics,
            output_dir=OUTPUT_DIR,
            project_root=PROJECT_ROOT,
            src_dir=SRC_DIR,
            logger=logger,
        )


if __name__ == "__main__":
    run_conversion()
# LOCATION: runners/batch/batch_program_runner.py
# ACTION: REPLACE ENTIRE FILE
"""
CORRECTION (NEW-4): target_program_id was resolved ONCE, before the
loop, from env_target_program_id() falling back to
mode.default_target_program_id - the SAME name for every program in
the batch. VMDZ7200/4310/4420 all received whichever single name that
produced.

Derived per-program now, inside the loop, from each program's own
source text via CobolParser().program_id() + NameDerivationResolver(),
the same mechanism runners/update/update_program_converter.py already
uses for a single program. env_target_program_id() still wins when
explicitly set (manual override for a single-program run); it no
longer silently becomes the name for an entire batch.
"""
from __future__ import annotations

from pathlib import Path

from runners.batch.batch_environment import (
    bootstrap_sys_path,
    env_target_program_id,
)

SRC_DIR, PROJECT_ROOT = bootstrap_sys_path(Path(__file__))

from config.path_settings import DEFAULT_MAPPING_SHEET_DIR, LOGS_DIR  # noqa: E402
from converter.infrastructure.logger_factory import (  # noqa: E402
    LoggerFactory,
)
from converter.parsers.cobol_parser import CobolParser  # noqa: E402
from converter.services.name_derivation_resolver import (  # noqa: E402
    NameDerivationResolver,
)
from runners.batch.batch_models import (  # noqa: E402
    BatchMode,
    SharedInputs,
)
from runners.batch.batch_reporter import (  # noqa: E402
    print_batch_summary,
)
from runners.batch.batch_validator import (  # noqa: E402
    program_paths_for_mode,
    validate_common_input_folders,
    validate_mode,
)
from runners.batch.program_converter import (  # noqa: E402
    convert_one_program,
)
from runners.batch.shared_input_loader import (  # noqa: E402
    load_shared_inputs,
)


__all__ = [
    "BatchMode",
    "SharedInputs",
    "env_target_program_id",
    "program_paths_for_mode",
    "load_shared_inputs",
    "convert_one_program",
    "resolve_target_program_id_for",
    "run_batch",
]


def resolve_target_program_id_for(program_path: Path) -> str:
    """Derive the target PROGRAM-ID from ONE program's own source text
    (VM...BD... -> VMDZ...). Returns "" when the source carries no
    PROGRAM-ID or the name does not match the derivable shape - the
    caller falls back to the mode default in that case, same as before.
    """
    try:
        source_text = program_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""
    source_id = CobolParser().program_id(source_text)
    if not source_id:
        return ""
    return NameDerivationResolver().derive(source_id)


def run_batch(mode: BatchMode) -> None:
    validate_common_input_folders()
    validate_mode(mode)

    logger = LoggerFactory.create_logger(
        name=f"idms_db2_{mode.name.lower()}_conversion",
        logs_dir=LOGS_DIR,
    )

    shared_inputs = load_shared_inputs(logger)
    programs = program_paths_for_mode(mode.name)

    # CORRECTION (NEW-4): no single target_program_id for the whole
    # batch any more - this is reported for visibility only, each
    # program resolves its own below.
    env_override = env_target_program_id()
    summary_target_label = (
        env_override or "(derived per program)"
    )

    print_batch_summary(
        project_root=PROJECT_ROOT,
        src_dir=SRC_DIR,
        mode=mode,
        mapping_folder=DEFAULT_MAPPING_SHEET_DIR,
        program_count=len(programs),
        target_program_id=summary_target_label,
    )

    for program_path in programs:
        target_program_id = (
            env_override
            or resolve_target_program_id_for(program_path)
            or mode.default_target_program_id
        )
        convert_one_program(
            mode=mode,
            program_path=program_path,
            shared_inputs=shared_inputs,
            target_program_id=target_program_id,
            logger=logger,
        )

# LOCATION: runners/batch/batch_program_runner.py
# ACTION: ADD at the very end of the file
if __name__ == "__main__":
    from config.path_settings import (
        DEFAULT_UPDATE_OUTPUT_DIR,
        DEFAULT_UPDATE_PROGRAM_DIR,
    )

    run_batch(
        BatchMode(
            name="UPDATE",
            program_dir=DEFAULT_UPDATE_PROGRAM_DIR,
            output_dir=DEFAULT_UPDATE_OUTPUT_DIR,
            apply_update_postprocess=True,
        )
    )
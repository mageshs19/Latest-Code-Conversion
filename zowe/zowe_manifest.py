# LOCATION: zowe/zowe_manifest.py
# ACTION: CREATE NEW FILE
"""Per-execution program manifest for monitoring.

For every IDMS program in the workspace Program folder this writes ONE
timestamped monitoring file into the Review folder, mapping the program
to the copybooks, DCLGENs and subschema it references, plus the derived
DB2 PROGRAM-ID:

    IDMS Program - Copybook - DCLGen - Sub Schema - DB2 Program
    VM4BD420 - ESDATMAS - DZBEFFTV, DZEVEFTV - VMBTS07 - VMDZ4420

Dependencies are resolved from each program's own source (the same
resolver the fetch step uses), so the file reflects exactly what was
fetched for that particular program. It never raises for a business
condition - a program that cannot be read is simply skipped.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from idms_db2_phase2.parsers.cobol_parser import CobolParser
from idms_db2_phase2.services.name_derivation_resolver import (
    NameDerivationResolver,
)
from zowe.zowe_resolver import resolve_dependencies
from zowe.zowe_rules import (
    MANIFEST_CELL_SEPARATOR,
    MANIFEST_EMPTY_CELL,
    MANIFEST_FILE_NAME_TEMPLATE,
    MANIFEST_HEADER,
    MANIFEST_ROW_TEMPLATE,
    MANIFEST_TIMESTAMP_FORMAT,
)
from zowe.zowe_workspace import program_dir, review_dir

PROGRAM_GLOB = "*"
TEXT_ENCODING = "utf-8"


def _cell(values) -> str:
    """Render a list (or scalar) cell, using [] for anything empty."""
    if isinstance(values, str):
        names = [values] if values.strip() else []
    else:
        names = [str(v).strip() for v in (values or []) if str(v).strip()]

    if not names:
        return MANIFEST_EMPTY_CELL
    return MANIFEST_CELL_SEPARATOR.join(names)


def _derive_db2_program_id(source_text: str) -> str:
    source_id = CobolParser().program_id(source_text)
    if not source_id:
        return MANIFEST_EMPTY_CELL
    return NameDerivationResolver().derive(source_id) or MANIFEST_EMPTY_CELL


def _program_sources() -> list[Path]:
    folder = program_dir()
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.glob(PROGRAM_GLOB) if p.is_file())


def build_manifest_rows() -> list[str]:
    """Return one formatted manifest row per readable program source."""
    rows: list[str] = []
    for source_path in _program_sources():
        try:
            source_text = source_path.read_text(
                encoding=TEXT_ENCODING, errors="replace"
            )
        except OSError:
            continue

        deps = resolve_dependencies(source_path.stem, source_text)
        rows.append(
            MANIFEST_ROW_TEMPLATE.format(
                idms=deps.program or source_path.stem.upper(),
                copybook=_cell(deps.copybooks),
                dclgen=_cell(deps.dclgens),
                subschema=_cell(deps.subschema),
                db2=_derive_db2_program_id(source_text),
            )
        )
    return rows


def write_execution_manifest() -> tuple[Path | None, int]:
    """Write the per-execution manifest to the Review folder.

    Returns (path, row_count). When there are no program sources nothing
    is written and (None, 0) is returned.
    """
    rows = build_manifest_rows()
    if not rows:
        return None, 0

    review_folder = review_dir()
    review_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime(MANIFEST_TIMESTAMP_FORMAT)
    manifest_path = review_folder / MANIFEST_FILE_NAME_TEMPLATE.format(
        timestamp=timestamp
    )

    body = "\n".join([MANIFEST_HEADER, *rows])
    manifest_path.write_text(body + "\n", encoding=TEXT_ENCODING)

    return manifest_path, len(rows)


__all__ = [
    "build_manifest_rows",
    "write_execution_manifest",
]

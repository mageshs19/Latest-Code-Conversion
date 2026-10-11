from __future__ import annotations

import os
from pathlib import Path

# NOTE: this module must NEVER import itself. A previous version carried
#   from idms_db2_phase2.config import path_settings
# plus a module-level print(path_settings.describe()). That made every
# importer of this module die with AttributeError before a single path
# was resolved, which looked exactly like "Zowe is not finding files".

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
LOGS_DIR = PROJECT_ROOT / "logs"


INPUT_DIR_ENV_KEY = "IDMS_INPUT_DIR"
LAYOUT_ENV_KEY = "IDMS_LAYOUT"


LAYOUT_FLAT = "FLAT"
LAYOUT_KIND = "KIND"


# ------------------------------------------------------------ input root
# The Zowe pipeline fetches Program, Copybook, DCLGen and Subschema into
# <project root>\mainframe\workspace and then sets IDMS_INPUT_DIR to that
# folder. Making the workspace the DEFAULT means the tree resolves the
# same way whether the pipeline set the variable or not, so a direct
# runner invocation reads the same files the pipeline just downloaded.
#
# IDMS_INPUT_DIR still wins when it is set, so nothing about the Zowe
# contract changes.
WORKSPACE_DIR_NAME = "workspace"
DEFAULT_WORKSPACE_DIR = PROJECT_ROOT / "mainframe" / WORKSPACE_DIR_NAME

FALLBACK_INPUT_DIR = DEFAULT_WORKSPACE_DIR


def _input_root() -> Path:
    configured = os.environ.get(INPUT_DIR_ENV_KEY, "").strip().strip('"')
    return Path(configured) if configured else FALLBACK_INPUT_DIR


DEFAULT_INPUT_DIR = _input_root()


# --------------------------------------------------------- first-level dirs
DEFAULT_MAPPING_SHEET_DIR = DEFAULT_INPUT_DIR / "Mapping Sheet"
DEFAULT_DCLGEN_DIR = DEFAULT_INPUT_DIR / "DCLGen"
DEFAULT_COPYBOOK_DIR = DEFAULT_INPUT_DIR / "Copybook"
DEFAULT_PROGRAM_DIR = DEFAULT_INPUT_DIR / "Program"
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR / "Output"


# Mapping Sheet is LOCAL project metadata. zowe_fetcher states it plainly:
# "Mapping Sheet is local and is never fetched." It therefore does not
# exist inside the workspace, and a root that points at the workspace
# would resolve it to an empty folder. The project copy is the fallback.
DEFAULT_LOCAL_MAPPING_SHEET_DIR = PROJECT_ROOT / "Mapping Sheet"


KIND_RETRIEVAL_FOLDER = "Retrieval"
KIND_UPDATE_FOLDER = "Update"


# --------------------------------------------------------------- layout
def _configured_layout() -> str:
    value = os.environ.get(LAYOUT_ENV_KEY, "").strip().upper()
    return value if value in (LAYOUT_FLAT, LAYOUT_KIND) else ""


def _detect_layout() -> str:
    """FLAT unless the legacy kind sub-folders actually exist."""
    configured = _configured_layout()
    if configured:
        return configured

    nested = (
        (DEFAULT_PROGRAM_DIR / KIND_RETRIEVAL_FOLDER).is_dir()
        or (DEFAULT_PROGRAM_DIR / KIND_UPDATE_FOLDER).is_dir()
    )
    return LAYOUT_KIND if nested else LAYOUT_FLAT


INPUT_LAYOUT = _detect_layout()
LAYOUT_IS_FLAT = INPUT_LAYOUT == LAYOUT_FLAT


def _kind_dir(parent: Path, kind: str) -> Path:
    """<parent> when flat, <parent>/<kind> when the split layout is in use."""
    return parent if LAYOUT_IS_FLAT else parent / kind


# ------------------------------------------------------- resolved folders
DEFAULT_RETRIEVAL_MAPPING_SHEET_DIR = _kind_dir(
    DEFAULT_MAPPING_SHEET_DIR, KIND_RETRIEVAL_FOLDER
)
DEFAULT_UPDATE_MAPPING_SHEET_DIR = _kind_dir(
    DEFAULT_MAPPING_SHEET_DIR, KIND_UPDATE_FOLDER
)


DEFAULT_RETRIEVAL_PROGRAM_DIR = _kind_dir(
    DEFAULT_PROGRAM_DIR, KIND_RETRIEVAL_FOLDER
)
DEFAULT_UPDATE_PROGRAM_DIR = _kind_dir(
    DEFAULT_PROGRAM_DIR, KIND_UPDATE_FOLDER
)


# Output MUST follow the same shape. The pipeline hands the review step
# --folder <root>\Output; writing to <root>\Output\Retrieval would leave
# review with nothing to do while convert reported OK.
DEFAULT_RETRIEVAL_OUTPUT_DIR = _kind_dir(
    DEFAULT_OUTPUT_DIR, KIND_RETRIEVAL_FOLDER
)
DEFAULT_UPDATE_OUTPUT_DIR = _kind_dir(
    DEFAULT_OUTPUT_DIR, KIND_UPDATE_FOLDER
)


# ------------------------------------------------------------ extensions
SUPPORTED_MAPPING_EXTENSIONS = (
    ".csv",
    ".xlsx",
)


SUPPORTED_TEXT_EXTENSIONS = (
    ".txt",
    ".cbl",
    ".cob",
    ".cpy",
)


SUPPORTED_LRF_EXTENSIONS = (
    ".txt",
    ".sub",
    ".sch",
    ".cpy",
    ".cbl",
)


# --------------------------------------------------------- LRF subschema
# Local workbench drops the subschema in <root>\LRF. Zowe lands it in
# <root>\Subschema (see zowe_workspace.WORKSPACE_SUBFOLDERS). Both are
# read, LRF first, so a program using COPY IDMS LR expands in either mode.
DEFAULT_LRF_DIR = DEFAULT_INPUT_DIR / "LRF"
DEFAULT_SUBSCHEMA_DIR = DEFAULT_INPUT_DIR / "Subschema"


# ------------------------------------------------------- sentinel paths
DEFAULT_SHEET_MAPPING_PATH = DEFAULT_MAPPING_SHEET_DIR / "Excel_Sheet_mapping.csv"
DEFAULT_RETRIEVAL_SOURCE_PATH = DEFAULT_RETRIEVAL_PROGRAM_DIR / "Retrieval.txt"
DEFAULT_UPDATE_SOURCE_PATH = DEFAULT_UPDATE_PROGRAM_DIR / "Update.txt"


# ------------------------------------------------------------- helpers
def existing_files(paths: list[Path]) -> list[Path]:
    """Return only paths that exist and are files."""
    return [
        path
        for path in paths
        if path.exists() and path.is_file()
    ]


def files_in_folder(
    folder: Path,
    extensions: tuple[str, ...],
) -> list[Path]:
    """Return supported files from a folder in stable name order."""
    if not folder.exists() or not folder.is_dir():
        return []

    normalized_extensions = tuple(
        extension.lower()
        for extension in extensions
    )

    return sorted(
        [
            path
            for path in folder.iterdir()
            if path.is_file()
            and path.suffix.lower() in normalized_extensions
        ],
        key=lambda item: item.name.lower(),
    )


# -------------------------------------------------------- mapping sheet
def mapping_sheet_paths() -> list[Path]:
    """Sheet Mapping workbooks: input root first, then the project copy.

    Under Zowe the input root IS the workspace, and the workspace has no
    Mapping Sheet folder because the sheet is never fetched. Falling back
    to the project copy is what keeps every Sheet-Mapping lookup working
    in both modes - including the reverse column lookup that supplies
    cursor key DISPLAY labels.
    """
    paths = files_in_folder(
        DEFAULT_MAPPING_SHEET_DIR,
        SUPPORTED_MAPPING_EXTENSIONS,
    )

    if paths:
        return paths

    return files_in_folder(
        DEFAULT_LOCAL_MAPPING_SHEET_DIR,
        SUPPORTED_MAPPING_EXTENSIONS,
    )


def retrieval_mapping_sheet_paths() -> list[Path]:
    mode_paths = files_in_folder(
        DEFAULT_RETRIEVAL_MAPPING_SHEET_DIR,
        SUPPORTED_MAPPING_EXTENSIONS,
    )

    if mode_paths:
        return mode_paths

    return mapping_sheet_paths()


def update_mapping_sheet_paths() -> list[Path]:
    mode_paths = files_in_folder(
        DEFAULT_UPDATE_MAPPING_SHEET_DIR,
        SUPPORTED_MAPPING_EXTENSIONS,
    )

    if mode_paths:
        return mode_paths

    return mapping_sheet_paths()


# ---------------------------------------------------- dclgen / copybook
def dclgen_paths() -> list[Path]:
    return files_in_folder(
        DEFAULT_DCLGEN_DIR,
        SUPPORTED_TEXT_EXTENSIONS,
    )


def copybook_paths() -> list[Path]:
    return files_in_folder(
        DEFAULT_COPYBOOK_DIR,
        SUPPORTED_TEXT_EXTENSIONS,
    )


# ---------------------------------------------------------------- LRF
def lrf_paths() -> list[Path]:
    """LRF subschema files: the LRF folder first, then Subschema."""
    paths = files_in_folder(DEFAULT_LRF_DIR, SUPPORTED_LRF_EXTENSIONS)
    if paths:
        return paths

    return files_in_folder(DEFAULT_SUBSCHEMA_DIR, SUPPORTED_LRF_EXTENSIONS)


def ensure_lrf_dir() -> None:
    """Create the optional LRF folder when it does not exist."""
    DEFAULT_LRF_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------ programs
def retrieval_program_paths() -> list[Path]:
    return files_in_folder(
        DEFAULT_RETRIEVAL_PROGRAM_DIR,
        SUPPORTED_TEXT_EXTENSIONS,
    )


def update_program_paths() -> list[Path]:
    return files_in_folder(
        DEFAULT_UPDATE_PROGRAM_DIR,
        SUPPORTED_TEXT_EXTENSIONS,
    )


# -------------------------------------------------------------- output
def ensure_output_dirs() -> None:
    """Create only the folders the ACTIVE layout uses.

    Creating Output\\Retrieval in flat mode would leave an empty folder
    beside the real output and invite the next reader to look in the
    wrong place.
    """
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if LAYOUT_IS_FLAT:
        return

    DEFAULT_RETRIEVAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_UPDATE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------- diagnostics
def describe() -> str:
    """One block showing where every input actually resolved.

    NEVER called at import time. A module-level print pollutes every
    importer - including pytest collection - and an exception inside it
    takes down the whole package. Callers print this explicitly.
    """
    source = "IDMS_INPUT_DIR" if os.environ.get(INPUT_DIR_ENV_KEY) else "default"
    rows = [
        f"Input root    : {DEFAULT_INPUT_DIR}  (from {source})",
        f"Layout        : {INPUT_LAYOUT}",
        f"Mapping Sheet : {DEFAULT_MAPPING_SHEET_DIR}",
        f"  fallback    : {DEFAULT_LOCAL_MAPPING_SHEET_DIR}",
        f"DCLGen        : {DEFAULT_DCLGEN_DIR}",
        f"Copybook      : {DEFAULT_COPYBOOK_DIR}",
        f"Program       : {DEFAULT_PROGRAM_DIR}",
        f"LRF           : {DEFAULT_LRF_DIR}",
        f"Subschema     : {DEFAULT_SUBSCHEMA_DIR}",
        f"Output        : {DEFAULT_OUTPUT_DIR}",
    ]
    return "\n".join(rows)


# ----------------------------------------------- import-time snapshots
# Kept because retrieval_input_selector.py and update_input_selector.py
# import them directly. They are SNAPSHOTS taken at import; call
# dclgen_paths() / copybook_paths() / lrf_paths() for a live read.
DEFAULT_DCLGEN_CANDIDATE_PATHS = dclgen_paths()
DEFAULT_COPYBOOK_CANDIDATE_PATHS = copybook_paths()
DEFAULT_LRF_CANDIDATE_PATHS = lrf_paths()


__all__ = [
    "PROJECT_ROOT",
    "SRC_DIR",
    "LOGS_DIR",
    "INPUT_DIR_ENV_KEY",
    "LAYOUT_ENV_KEY",
    "INPUT_LAYOUT",
    "LAYOUT_IS_FLAT",
    "WORKSPACE_DIR_NAME",
    "DEFAULT_WORKSPACE_DIR",
    "DEFAULT_INPUT_DIR",
    "DEFAULT_MAPPING_SHEET_DIR",
    "DEFAULT_LOCAL_MAPPING_SHEET_DIR",
    "DEFAULT_RETRIEVAL_MAPPING_SHEET_DIR",
    "DEFAULT_UPDATE_MAPPING_SHEET_DIR",
    "DEFAULT_DCLGEN_DIR",
    "DEFAULT_COPYBOOK_DIR",
    "DEFAULT_LRF_DIR",
    "DEFAULT_SUBSCHEMA_DIR",
    "DEFAULT_PROGRAM_DIR",
    "DEFAULT_RETRIEVAL_PROGRAM_DIR",
    "DEFAULT_UPDATE_PROGRAM_DIR",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_RETRIEVAL_OUTPUT_DIR",
    "DEFAULT_UPDATE_OUTPUT_DIR",
    "DEFAULT_SHEET_MAPPING_PATH",
    "DEFAULT_RETRIEVAL_SOURCE_PATH",
    "DEFAULT_UPDATE_SOURCE_PATH",
    "SUPPORTED_MAPPING_EXTENSIONS",
    "SUPPORTED_TEXT_EXTENSIONS",
    "SUPPORTED_LRF_EXTENSIONS",
    "DEFAULT_DCLGEN_CANDIDATE_PATHS",
    "DEFAULT_COPYBOOK_CANDIDATE_PATHS",
    "DEFAULT_LRF_CANDIDATE_PATHS",
    "describe",
    "existing_files",
    "files_in_folder",
    "mapping_sheet_paths",
    "retrieval_mapping_sheet_paths",
    "update_mapping_sheet_paths",
    "dclgen_paths",
    "copybook_paths",
    "lrf_paths",
    "ensure_lrf_dir",
    "retrieval_program_paths",
    "update_program_paths",
    "ensure_output_dirs",
]
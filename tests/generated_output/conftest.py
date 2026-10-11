from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from config import path_settings

COBOL_GLOB = "*.cbl"
SOURCE_GLOB = "*.py"
WATCHED_SOURCE_DIRS = ("converter", "rules", "patterns", "catalogs")
OUTPUT_DIR_NAMES = (
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_RETRIEVAL_OUTPUT_DIR",
    "DEFAULT_UPDATE_OUTPUT_DIR",
)
BODY_START = 7
BODY_END = 72
STAMP_FORMAT = "%d-%m-%Y %H:%M:%S"


def _candidate_output_dirs() -> list[Path]:
    folders: list[Path] = []
    seen: set[str] = set()
    for name in OUTPUT_DIR_NAMES:
        folder = getattr(path_settings, name, None)
        if folder is None:
            continue
        path = Path(folder)
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        folders.append(path)
    return folders


def _newest_generated_cbl() -> Path | None:
    newest: Path | None = None
    for folder in _candidate_output_dirs():
        if not folder.exists() or not folder.is_dir():
            continue
        for path in folder.glob(COBOL_GLOB):
            if not path.is_file():
                continue
            if newest is None:
                newest = path
                continue
            if path.stat().st_mtime > newest.stat().st_mtime:
                newest = path
    return newest


def _newest_source_mtime() -> float:
    root = Path(getattr(path_settings, "PROJECT_ROOT", Path.cwd()))
    newest = 0.0
    for name in WATCHED_SOURCE_DIRS:
        folder = root / name
        if not folder.exists():
            continue
        for path in folder.rglob(SOURCE_GLOB):
            if path.is_file():
                newest = max(newest, path.stat().st_mtime)
    return newest


def _stamp(mtime: float) -> str:
    return datetime.fromtimestamp(mtime).strftime(STAMP_FORMAT)


@pytest.fixture(scope="session")
def generated_artifact() -> Path:
    artifact = _newest_generated_cbl()
    if artifact is None:
        searched = ", ".join(
            str(folder) for folder in _candidate_output_dirs()
        ) or "(none)"
        pytest.skip(f"No generated .cbl found. Searched: {searched}")

    artifact_mtime = artifact.stat().st_mtime
    source_mtime = _newest_source_mtime()
    if source_mtime and artifact_mtime < source_mtime:
        pytest.skip(
            "Generated artifact is older than the generator source.\n"
            f"  artifact : {artifact}\n"
            f"  generated: {_stamp(artifact_mtime)}\n"
            f"  source   : {_stamp(source_mtime)}\n"
            "Regenerate the program, then re-run this module."
        )
    return artifact


@pytest.fixture(scope="session")
def generated_bodies(generated_artifact: Path) -> list[str]:
    text = generated_artifact.read_text(encoding="utf-8", errors="replace")
    return [
        line[BODY_START:BODY_END].strip()
        for line in text.splitlines()
        if line[BODY_START:BODY_END].strip()
    ]


@pytest.fixture(scope="session")
def previous_body(generated_bodies: list[str]):
    def _previous(index: int) -> str:
        if index <= 0:
            return ""
        return generated_bodies[index - 1]

    return _previous
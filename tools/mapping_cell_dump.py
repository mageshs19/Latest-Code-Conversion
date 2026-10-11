# LOCATION: tools/mapping_cell_dump.py
# ACTION: CREATE NEW FILE
r"""Dump every Sheet Mapping row that mentions the cursor driving keys.

The reverse lookup returns the FIRST matching row. When a column appears
on more than one row - a base entry plus a REDEFINES or view variant -
that choice matters and must be made on evidence, not on row order.

Run from the project root:

    $env:PYTHONPATH = "."
    python tools\mapping_cell_dump.py
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

COLUMNS = (
    "CT_RKTPROD_479BEFF",
    "NR_IDSTOCK_479BEFF",
    "NR_CDSTK_479BEFF",
    "NS_DBSTK_479BEFF",
)

FIELDS = (
    "cobol_record_idms",
    "new_db2_record",
    "new_db2_field_name",
    "cross_application_db2_table",
    "cross_application_db2_field_name",
    "cobol_zone",
    "reference_field_name_copybook",
    "db2_key",
    "idms_key",
    "relation",
    "remarks",
)

LINE = "=" * 78
SUB = "-" * 78


def first_import(candidates: list[str], name: str):
    for dotted in candidates:
        try:
            module = importlib.import_module(dotted)
        except Exception:
            continue
        obj = getattr(module, name, None)
        if obj is not None:
            return obj
    return None


def normalize(value: str) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def load_rows() -> list:
    path_settings = importlib.import_module("config.path_settings")
    sheets = path_settings.mapping_sheet_paths()
    if not sheets:
        print("No mapping sheet found.")
        return []

    sheet = sheets[0]
    print(f"Sheet: {sheet}")
    print("")

    parser = first_import(
        [
            "converter.parsers.sheet_mapping_parser",
            "converter.parsers.mapping_sheet_parser",
        ],
        "SheetMappingParser",
    )
    wrapper = first_import(
        [
            "converter.infrastructure.local_uploaded_file",
            "converter.infrastructure.file_loader",
            "runners.retrieval.retrieval_input_loader",
        ],
        "LocalUploadedFile",
    )

    if parser is None or wrapper is None:
        print("Parser or file wrapper not importable.")
        return []

    return list(parser().parse_uploaded_file(wrapper(Path(sheet))) or [])


def main() -> int:
    print("")
    print(LINE)
    print("SHEET MAPPING CELL DUMP - cursor driving keys")
    print(LINE)
    print("")

    rows = load_rows()
    print(f"Total rows: {len(rows)}")

    wanted = {normalize(column) for column in COLUMNS}

    for column in COLUMNS:
        target = normalize(column)
        matches = []

        for index, row in enumerate(rows):
            candidates = {
                normalize(getattr(row, "new_db2_field_name", "")),
                normalize(getattr(row, "cross_application_db2_field_name", "")),
            }
            if target in candidates:
                matches.append((index, row))

        print("")
        print(LINE)
        print(f"{column}   ->   {len(matches)} row(s)")
        print(LINE)

        if not matches:
            print("  NO ROW. The label will fall back to the DCLGEN host name.")
            continue

        if len(matches) > 1:
            print("  !! MORE THAN ONE ROW. The first one wins. Check which is correct.")

        for index, row in matches:
            print("")
            print(f"  row #{index}")
            print(SUB)
            for name in FIELDS:
                value = str(getattr(row, name, "") or "").strip()
                if value:
                    print(f"    {name:<36}: {value}")

    print("")
    print(LINE)
    print("DUMP COMPLETE")
    print(LINE)
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
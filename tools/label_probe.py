# LOCATION: tools/label_probe.py
# ACTION: CREATE NEW FILE
"""Developer probe: why are cursor key DISPLAY labels wrong?

Answers, in order, the only questions that matter:

  1. What environment is this running in?
  2. Where did every input folder resolve to?
  3. Is any input actually present?
  4. Which FILE is each live class loaded from?
  5. Is __init__.py serving a different (stale) class object?
  6. Does the wiring accept a MappingRepository at all?
  7. Is KEY_LABEL_SOURCE switched on?
  8. Does the Sheet-Mapping reverse lookup return a name for the four
     driving-key columns of DZBEFFTV?

Every section is independently guarded. A failure in one section must
never stop the rest, because the whole point of this probe is to run on
a broken tree.

Run from the project root:

    $env:PYTHONPATH = "."
    python tools\label_probe.py

Exit codes: 0 probe completed, 2 probe itself could not start.
"""

from __future__ import annotations

import importlib
import inspect
import os
import platform
import sys
import traceback
from pathlib import Path

LINE = "=" * 78
SUB = "-" * 78
PAD = 34

# The four driving-key columns of the child cursor DZEVEFC1.
PARENT_GROUP = "DCLDZBEFFTV"
PARENT_TABLE = "DZBEFFTV"
KEY_COLUMNS = (
    "CT_RKTPROD_479BEFF",
    "NR_IDSTOCK_479BEFF",
    "NR_CDSTK_479BEFF",
    "NS_DBSTK_479BEFF",
)
KEY_HOSTS = (
    "CT-RKTPROD-479BEFF",
    "NR-IDSTOCK-479BEFF",
    "NR-CDSTK-479BEFF",
    "NS-DBSTK-479BEFF",
)


# ---------------------------------------------------------------- helpers
def show(label: str, value) -> None:
    print(f"  {str(label):<{PAD}}: {value}")


def head(number: int, title: str) -> None:
    print("")
    print(LINE)
    print(f"{number}. {title}")
    print(LINE)


def fail(section: str, error: BaseException) -> None:
    print(f"  !! {section} FAILED: {type(error).__name__}: {error}")
    for entry in traceback.format_exc().splitlines()[-4:]:
        print(f"     {entry}")


def try_import(dotted: str, name: str):
    """Import `name` from module `dotted`. Returns None on any failure."""
    try:
        module = importlib.import_module(dotted)
    except Exception:
        return None
    return getattr(module, name, None)


def first_import(candidates: list[str], name: str):
    """First successful import of `name` from the candidate modules."""
    for dotted in candidates:
        obj = try_import(dotted, name)
        if obj is not None:
            return obj, dotted
    return None, ""


def count_files(folder) -> str:
    try:
        path = Path(folder)
        if not path.is_dir():
            return "FOLDER MISSING"
        files = [p for p in path.iterdir() if p.is_file()]
        if not files:
            return "0 files  <-- EMPTY"
        names = ", ".join(sorted(p.name for p in files)[:6])
        more = "" if len(files) <= 6 else f", +{len(files) - 6} more"
        return f"{len(files)} files  [{names}{more}]"
    except Exception as exc:  # noqa: BLE001
        return f"unreadable: {exc}"


# ------------------------------------------------------------------- main
def main() -> int:
    print("")
    print(LINE)
    print("CURSOR KEY LABEL PROBE")
    print(LINE)

    # -------------------------------------------------- 1. environment
    head(1, "ENVIRONMENT")
    try:
        show("python", sys.version.split()[0])
        show("platform", platform.platform())
        show("cwd", Path.cwd())
        show("PYTHONPATH", os.environ.get("PYTHONPATH", "(not set)"))
        show("IDMS_INPUT_DIR", os.environ.get("IDMS_INPUT_DIR", "(not set)"))
        show("IDMS_INPUT_LAYOUT", os.environ.get("IDMS_INPUT_LAYOUT", "(not set)"))
        show("sys.path[0]", sys.path[0] if sys.path else "(empty)")
    except Exception as exc:  # noqa: BLE001
        fail("ENVIRONMENT", exc)

    # ------------------------------------------------ 2. resolved paths
    head(2, "RESOLVED INPUT PATHS (config/path_settings.py)")
    path_settings = None
    try:
        path_settings = importlib.import_module("config.path_settings")
        for name in (
            "PROJECT_ROOT",
            "SRC_DIR",
            "LOGS_DIR",
            "DEFAULT_INPUT_DIR",
            "DEFAULT_MAPPING_SHEET_DIR",
            "DEFAULT_DCLGEN_DIR",
            "DEFAULT_COPYBOOK_DIR",
            "DEFAULT_PROGRAM_DIR",
            "DEFAULT_OUTPUT_DIR",
            "INPUT_LAYOUT",
        ):
            show(name, getattr(path_settings, name, "(absent)"))
    except Exception as exc:  # noqa: BLE001
        fail("PATH SETTINGS", exc)

    # ------------------------------------------------- 3. input present
    head(3, "ARE THE INPUTS ACTUALLY THERE?")
    try:
        if path_settings is None:
            print("  skipped: path_settings did not import")
        else:
            for name in (
                "DEFAULT_MAPPING_SHEET_DIR",
                "DEFAULT_DCLGEN_DIR",
                "DEFAULT_COPYBOOK_DIR",
                "DEFAULT_PROGRAM_DIR",
            ):
                folder = getattr(path_settings, name, None)
                if folder is None:
                    show(name, "(absent)")
                    continue
                show(name.replace("DEFAULT_", ""), count_files(folder))
    except Exception as exc:  # noqa: BLE001
        fail("INPUT PRESENCE", exc)

    # ---------------------------------------------- 4. live class files
    head(4, "LIVE CLASS FILES")
    KeyDiagnosticsBuilder = None
    CursorParagraphBodyBuilder = None
    JoinKeyLabelResolver = None
    try:
        KeyDiagnosticsBuilder, kdb_module = first_import(
            [
                "converter.generators.cursor_paragraph.cursor_key_diagnostics",
                "converter.generators.cursor_paragraph.key_diagnostics_builder",
                "converter.generators.cursor_paragraph",
            ],
            "KeyDiagnosticsBuilder",
        )
        CursorParagraphBodyBuilder, cpb_module = first_import(
            [
                "converter.generators.cursor_paragraph.cursor_paragraph_body_builder",
                "converter.generators.cursor_paragraph",
            ],
            "CursorParagraphBodyBuilder",
        )
        JoinKeyLabelResolver, jkl_module = first_import(
            [
                "converter.generators.cursor_paragraph.join_key_label_resolver",
                "converter.generators.cursor_paragraph",
            ],
            "JoinKeyLabelResolver",
        )

        for label, obj, dotted in (
            ("KeyDiagnosticsBuilder", KeyDiagnosticsBuilder, kdb_module),
            ("CursorParagraphBodyBuilder", CursorParagraphBodyBuilder, cpb_module),
            ("JoinKeyLabelResolver", JoinKeyLabelResolver, jkl_module),
        ):
            if obj is None:
                show(label, "NOT IMPORTABLE from any candidate module")
                continue
            show(label + " module", dotted)
            try:
                show(label + " file", inspect.getfile(obj))
            except Exception:  # noqa: BLE001
                show(label + " file", "(builtin / unavailable)")
    except Exception as exc:  # noqa: BLE001
        fail("LIVE CLASS FILES", exc)

    # ------------------------------------------- 5. __init__ shadowing
    head(5, "IS __init__.py SHADOWING THE MODULE?")
    try:
        package = importlib.import_module("converter.generators.cursor_paragraph")
        show("package file", getattr(package, "__file__", "(namespace pkg)"))
        for label, live in (
            ("KeyDiagnosticsBuilder", KeyDiagnosticsBuilder),
            ("CursorParagraphBodyBuilder", CursorParagraphBodyBuilder),
            ("JoinKeyLabelResolver", JoinKeyLabelResolver),
        ):
            exported = getattr(package, label, None)
            if exported is None:
                show(label, "not exported by package (fine)")
                continue
            same = exported is live
            show(label + " same object", same)
            if not same:
                try:
                    show(label + " package export file", inspect.getfile(exported))
                except Exception:  # noqa: BLE001
                    pass
                print("     <-- __init__.py IS SHADOWING THE MODULE")
    except Exception as exc:  # noqa: BLE001
        fail("SHADOW CHECK", exc)

    # -------------------------------------------------- 6. wiring check
    head(6, "DOES THE WIRING ACCEPT A MappingRepository?")
    try:
        if CursorParagraphBodyBuilder is None:
            print("  skipped: body builder not importable")
        else:
            sig = inspect.signature(CursorParagraphBodyBuilder.__init__)
            show("body builder parameters", ", ".join(sig.parameters))
            show(
                "accepts mapping_repository",
                "mapping_repository" in sig.parameters,
            )

        if KeyDiagnosticsBuilder is None:
            print("  skipped: key diagnostics not importable")
        else:
            sig = inspect.signature(KeyDiagnosticsBuilder.__init__)
            show("key diagnostics parameters", ", ".join(sig.parameters))
            show(
                "accepts label_resolver",
                "label_resolver" in sig.parameters,
            )

        generator, gen_module = first_import(
            ["converter.generators.cursor_paragraph_generator"],
            "CursorParagraphGenerator",
        )
        if generator is None:
            show("CursorParagraphGenerator", "NOT IMPORTABLE")
        else:
            sig = inspect.signature(generator.__init__)
            show("generator parameters", ", ".join(sig.parameters))
            show(
                "generator accepts mapping_repository",
                "mapping_repository" in sig.parameters,
            )
    except Exception as exc:  # noqa: BLE001
        fail("WIRING CHECK", exc)

    # ------------------------------------------------ 7. rules switches
    head(7, "RULES SWITCHES")
    try:
        rules = importlib.import_module("rules.cursor_paragraph_rules")
        for name in (
            "KEY_LABEL_SOURCE",
            "KEY_LABEL_SOURCE_MAPPING",
            "KEY_LABEL_SOURCE_HOST",
            "KEY_LABEL_MIN_WIDTH",
            "FETCH_KEY_LABEL_WIDTH",
            "FETCH_KEY_DIAGNOSTIC_LIMIT",
            "ALIGN_KEY_QUALIFIER",
        ):
            show(name, getattr(rules, name, "(absent)"))

        source = getattr(rules, "KEY_LABEL_SOURCE", None)
        mapping = getattr(rules, "KEY_LABEL_SOURCE_MAPPING", None)
        if source is not None and mapping is not None:
            show("MAPPING MODE ACTIVE", source == mapping)
        if hasattr(rules, "FETCH_KEY_LABEL_WIDTH"):
            print("     <-- STALE CONSTANT PRESENT (should be deleted)")
    except Exception as exc:  # noqa: BLE001
        fail("RULES SWITCHES", exc)

    # ------------------------------------------------- 8. source checks
    head(8, "IS THE NEW CODE ON THE PATH?")
    try:
        if KeyDiagnosticsBuilder is None:
            print("  skipped: key diagnostics not importable")
        else:
            src = inspect.getsource(KeyDiagnosticsBuilder)
            checks = {
                "uses KEY_LABEL_MIN_WIDTH": "KEY_LABEL_MIN_WIDTH" in src,
                "derived offset len(display)-len(host)":
                    "len(display) - len(host)" in src,
                "calls label_resolver.label_for": "label_for" in src,
                "STALE FETCH_KEY_LABEL_WIDTH": "FETCH_KEY_LABEL_WIDTH" in src,
                "guards None resolver": "raise ValueError" in src,
            }
            for label, value in checks.items():
                show(label, value)
    except Exception as exc:  # noqa: BLE001
        fail("SOURCE CHECKS", exc)

    # ------------------------------------------- 9. the actual lookup
    head(9, "SHEET MAPPING REVERSE LOOKUP (the real test)")
    try:
        MappingRepository, _ = first_import(
            ["converter.repositories.mapping_repository"],
            "MappingRepository",
        )
        if MappingRepository is None:
            print("  MappingRepository NOT IMPORTABLE - cannot test lookup")
        else:
            rows = load_mapping_rows(path_settings)
            show("sheet mapping rows loaded", len(rows))

            if not rows:
                print("")
                print("  No rows. The lookup cannot succeed. Check section 3.")
            else:
                repo = MappingRepository(rows)
                show("repository.count()", safe_call(repo, "count"))

                print("")
                print(SUB)
                print("  COLUMN -> COBOL NAME (blank means FALLBACK will happen)")
                print(SUB)
                for column, host in zip(KEY_COLUMNS, KEY_HOSTS):
                    answer = ""
                    try:
                        answer = repo.cobol_field_for_column(
                            table_name=PARENT_TABLE,
                            column_name=column,
                        )
                    except Exception as exc:  # noqa: BLE001
                        answer = f"RAISED {type(exc).__name__}: {exc}"
                    flag = "   " if answer else " ! "
                    print(f" {flag}{column:<24} -> {answer or '(EMPTY)':<20} host={host}")

                if JoinKeyLabelResolver is not None:
                    print("")
                    resolver = JoinKeyLabelResolver(repo)
                    show("table_of(DCLDZBEFFTV)", safe_call(resolver, "table_of", PARENT_GROUP))
                    show(
                        "candidate_tables(DZBEFFTV)",
                        safe_call(resolver, "candidate_tables", PARENT_TABLE),
                    )
                    print("")
                    print(SUB)
                    print("  RESOLVED LABELS")
                    print(SUB)
                    for column, host in zip(KEY_COLUMNS, KEY_HOSTS):
                        try:
                            label = resolver.label_for(
                                table=resolver.table_of(PARENT_GROUP),
                                column=column,
                                host=host,
                            )
                        except Exception as exc:  # noqa: BLE001
                            label = f"RAISED {type(exc).__name__}: {exc}"
                        print(f"    {column:<24} -> {label}")
                    print("")
                    print("  resolver.messages:")
                    for message in getattr(resolver, "messages", []) or ["(none)"]:
                        print(f"    - {message}")
    except Exception as exc:  # noqa: BLE001
        fail("SHEET MAPPING LOOKUP", exc)

    # -------------------------------------- 10. reproduce with no repo
    head(10, "RENDER WITH NO REPOSITORY (reproduces the defect)")
    try:
        if KeyDiagnosticsBuilder is None:
            print("  skipped: key diagnostics not importable")
        else:
            try:
                builder = KeyDiagnosticsBuilder()
                print("  KeyDiagnosticsBuilder() constructed with ZERO arguments.")
                print("  <-- A missing dependency is a VALID construction. This is the bug.")
                hosts = [f"{h} OF {PARENT_GROUP}" for h in KEY_HOSTS]
                for line in builder.lines_for_hosts(hosts):
                    print(f"    |{line}|")
            except TypeError as exc:
                print(f"  Constructor correctly REQUIRES arguments: {exc}")
            except Exception as exc:  # noqa: BLE001
                fail("NO-REPO RENDER", exc)
    except Exception as exc:  # noqa: BLE001
        fail("NO-REPO RENDER", exc)

    print("")
    print(LINE)
    print("PROBE COMPLETE")
    print(LINE)
    print("")
    return 0


# ------------------------------------------------------------- utilities
def safe_call(obj, method: str, *args):
    try:
        return getattr(obj, method)(*args)
    except Exception as exc:  # noqa: BLE001
        return f"RAISED {type(exc).__name__}: {exc}"


def load_mapping_rows(path_settings) -> list:
    """Load Sheet Mapping rows using whatever loader this tree exposes."""
    if path_settings is None:
        return []

    folder = getattr(path_settings, "DEFAULT_MAPPING_SHEET_DIR", None)
    if folder is None or not Path(folder).is_dir():
        return []

    sheets = [p for p in Path(folder).iterdir() if p.is_file()]
    if not sheets:
        return []

    sheet = sorted(sheets)[0]
    print(f"  using sheet: {sheet}")

    parser, _ = first_import(
        [
            "converter.parsers.sheet_mapping_parser",
            "converter.parsers.mapping_sheet_parser",
        ],
        "SheetMappingParser",
    )
    wrapper, _ = first_import(
        [
            "converter.infrastructure.local_uploaded_file",
            "converter.infrastructure.file_loader",
            "runners.retrieval.retrieval_input_loader",
        ],
        "LocalUploadedFile",
    )

    if parser is None:
        print("  SheetMappingParser NOT IMPORTABLE - adjust the candidate list")
        return []
    if wrapper is None:
        print("  LocalUploadedFile NOT IMPORTABLE - adjust the candidate list")
        return []

    try:
        return list(parser().parse_uploaded_file(wrapper(sheet)) or [])
    except Exception as exc:  # noqa: BLE001
        print(f"  sheet parse FAILED: {type(exc).__name__}: {exc}")
        return []


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(2)
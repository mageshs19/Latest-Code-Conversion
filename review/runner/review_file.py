"""Review a generated DB2 COBOL file, or every .cbl in a folder.

Needs no Sheet Mapping, DCLGEN or Copybook. Checks that require metadata
report SKIPPED instead of failing.

    python review\\runner\\review_file.py --path C:\\S\\S-Input\\Output\\Retrieval\\VMDZ4420.cbl
    python review\\runner\\review_file.py --folder C:\\S\\S-Input\\Output\\Retrieval
    python review\\runner\\review_file.py --folder C:\\S\\S-Input\\Output\\Retrieval --latest
    python review\\runner\\review_file.py --path out.cbl --source in.txt --kind UPDATE

Exit codes: 0 accepted, 1 rejected, 2 error or nothing to review.

PROGRAM KIND IS A PER-PROGRAM FACT
----------------------------------
``--kind`` used to be resolved ONCE and handed to every file in the run.
The zowe pipeline passes no --kind at all, so the default UNKNOWN reached
every ReviewContext, and Check.applies() --

    return scope == BOTH or scope == str(ctx.program_kind).upper()

-- silently skipped every APPLIES_TO = UPDATE check on every program. A
folder of seven programs reviewed as "Program Kind : UNKNOWN" and passed
while carrying an orphan END-IF and a truncating VARCHAR length.

review.standards.program_kind_detector was written to fix exactly this
and had no production caller. It does now:

* ``--kind`` remains an operator OVERRIDE and always wins.
* When it is absent the kind is detected PER FILE from the program text.
* The banner reports what was actually resolved, not what was requested.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Path bootstrap. Plain inline code, and it MUST run before any review
# import, because "python review\runner\review_file.py" puts only
# review\runner on sys.path.
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = PROJECT_ROOT / "src"

for _c in (PROJECT_ROOT, SRC_DIR):
    if str(_c) not in sys.path:
        sys.path.insert(0, str(_c))
# ---------------------------------------------------------------------------

import argparse  # noqa: E402
from collections import Counter  # noqa: E402

from review.engine.context import (  # noqa: E402
    KIND_RETRIEVAL,
    KIND_UNKNOWN,
    KIND_UPDATE,
    ReviewContext,
)
from review.engine.reviewer import (  # noqa: E402
    Reviewer,
    blockers,
    is_accepted,
)
from review.report import csv_writer, text_writer  # noqa: E402
from review.report.text_writer import render  # noqa: E402
from review.runner._bootstrap import (  # noqa: E402
    COBOL_GLOB,
    EXIT_ACCEPTED,
    EXIT_ERROR,
    EXIT_REJECTED,
    REPORT_DIR,
    read_text,
    stamp,
)
from review.standards import wording as w  # noqa: E402
from review.standards.program_kind_detector import (  # noqa: E402
    detect_program_kind,
)

VALID_KINDS = (KIND_RETRIEVAL, KIND_UPDATE, KIND_UNKNOWN)

# Banner formatting for a mixed folder. Values only, no prose: the
# surrounding sentence stays in wording.py.
KIND_COUNT_TEMPLATE = "{kind} x{count}"
KIND_SEPARATOR = ", "


class NothingToReview(Exception):
    """The folder exists but holds no generated .cbl."""

    def __init__(self, folder: Path) -> None:
        self.folder = Path(folder)
        super().__init__(w.MSG_NO_OUTPUT_FOUND.format(folder=self.folder))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Code review a generated DB2 COBOL file."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--path", help="a single .cbl file to review")
    source.add_argument("--folder", help="a folder of .cbl files to review")
    parser.add_argument(
        "--latest",
        action="store_true",
        help="with --folder, review only the newest file",
    )
    parser.add_argument(
        "--source",
        help="original IDMS COBOL source file, optional",
    )
    parser.add_argument(
        "--kind",
        default=KIND_UNKNOWN,
        help=(
            "RETRIEVAL, UPDATE or UNKNOWN. UNKNOWN (the default) detects "
            "the kind per program from the generated text."
        ),
    )
    parser.add_argument(
        "--report",
        default=str(REPORT_DIR),
        help="folder to write the reports into",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print one summary line per file instead of the full report",
    )
    return parser.parse_args()


def resolve_targets(args: argparse.Namespace) -> list[Path]:
    if args.path:
        path = Path(args.path)
        if not path.is_file():
            raise FileNotFoundError(w.MSG_FILE_NOT_FOUND.format(path=path))
        return [path]

    folder = Path(args.folder)
    if not folder.exists():
        raise FileNotFoundError(w.MSG_FOLDER_NOT_FOUND.format(folder=folder))
    if not folder.is_dir():
        raise FileNotFoundError(w.MSG_PATH_NOT_FOLDER.format(folder=folder))

    files = sorted(
        (item for item in folder.glob(COBOL_GLOB) if item.is_file()),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise NothingToReview(folder)

    if args.latest:
        return files[:1]
    return sorted(files, key=lambda item: item.name.lower())


def resolve_kind(value: str) -> str:
    """The operator's --kind, or UNKNOWN when absent or unrecognised."""
    kind = str(value or "").strip().upper()
    return kind if kind in VALID_KINDS else KIND_UNKNOWN


def build_context(cbl_path: Path, kind: str, source_text: str) -> ReviewContext:
    """Build the review input for ONE file.

    ``kind`` is the operator override. It wins whenever it names a real
    kind. UNKNOWN means "nobody told us", and the kind is then recovered
    from the program text, which is the only per-program evidence a batch
    run has.

    ReviewContext.__post_init__ normalises the result, so an unexpected
    value degrades to UNKNOWN rather than raising.
    """
    converted = read_text(cbl_path)

    resolved = kind
    if resolved == KIND_UNKNOWN:
        resolved = detect_program_kind(converted, source_text)

    return ReviewContext(
        program_name=cbl_path.stem,
        program_kind=resolved,
        target_program_id="",
        source_file=cbl_path.name,
        converted_cobol=converted,
        source_cobol=source_text,
    )


def describe_kinds(contexts: list[ReviewContext]) -> str:
    """What the run actually resolved, in a stable order.

    One file reports its kind. A mixed folder reports each kind with a
    count, so "UNKNOWN" can never again stand in for seven programs that
    were never classified.
    """
    if not contexts:
        return KIND_UNKNOWN
    if len(contexts) == 1:
        return contexts[0].program_kind

    counts = Counter(ctx.program_kind for ctx in contexts)
    return KIND_SEPARATOR.join(
        KIND_COUNT_TEMPLATE.format(kind=kind, count=counts[kind])
        for kind in VALID_KINDS
        if counts.get(kind)
    )


def print_banner(
    args,
    targets: list[Path],
    kind_summary: str,
    report_dir: Path,
) -> None:
    print("")
    print(w.H_RUN_FILE)
    print(w.RULE)
    if args.folder:
        print(w.MSG_REVIEWED_FOLDER.format(folder=Path(args.folder)))
    print(w.MSG_FILE_COUNT.format(count=len(targets)))
    print(w.MSG_PROGRAM_KIND.format(kind=kind_summary))
    print(w.MSG_REPORT_FOLDER.format(folder=report_dir))
    print("")


def print_nothing_to_review(exc: NothingToReview) -> int:
    print("")
    print(w.MSG_NO_OUTPUT_TITLE)
    print(w.RULE)
    print(w.MSG_NO_OUTPUT_FOUND.format(folder=exc.folder))
    print("")
    print(w.MSG_NO_OUTPUT_HINT)
    print("")
    return EXIT_ERROR


def run() -> int:
    args = parse_arguments()

    report_dir = Path(args.report)
    report_dir.mkdir(parents=True, exist_ok=True)

    kind = resolve_kind(args.kind)

    source_text = ""
    if args.source:
        source_path = Path(args.source)
        if not source_path.is_file():
            raise FileNotFoundError(
                w.MSG_SOURCE_NOT_FOUND.format(path=source_path)
            )
        source_text = read_text(source_path)

    targets = resolve_targets(args)

    # Contexts are built BEFORE the banner so the banner can report the
    # kinds that were resolved rather than the one that was requested.
    # Each file is read exactly once, here.
    contexts = [
        build_context(cbl_path, kind, source_text) for cbl_path in targets
    ]

    reviewer = Reviewer()
    when = stamp()
    results = []

    print_banner(args, targets, describe_kinds(contexts), report_dir)

    for cbl_path, context in zip(targets, contexts):
        result = reviewer.review(context)
        results.append(result)

        stem = f"{cbl_path.stem}_{when}"
        text_writer.write(result, report_dir, stem)
        csv_writer.write(result, report_dir, stem)

        if args.quiet:
            ids = ", ".join(c.check_id for c in blockers(result))
            print(w.MSG_QUIET_LINE.format(
                verdict=w.ACCEPTED if is_accepted(result) else w.REJECTED,
                name=cbl_path.name,
                suffix=w.MSG_QUIET_BLOCKING.format(ids=ids) if ids else "",
            ))
        else:
            print(render(result))

    if len(results) > 1:
        csv_writer.write_summary(results, report_dir, f"summary_{when}")

    accepted = sum(1 for item in results if is_accepted(item))
    rejected = len(results) - accepted

    print(w.RULE)
    print(w.MSG_SUMMARY.format(
        reviewed=len(results), accepted=accepted, rejected=rejected,
    ))
    print(w.MSG_REPORTS_WRITTEN.format(folder=report_dir))
    print("")

    return EXIT_ACCEPTED if rejected == 0 else EXIT_REJECTED


def main() -> None:
    try:
        raise SystemExit(run())
    except SystemExit:
        raise
    except NothingToReview as exc:
        raise SystemExit(print_nothing_to_review(exc))
    except FileNotFoundError as exc:
        print(w.MSG_ERROR.format(message=exc))
        raise SystemExit(EXIT_ERROR)
    except Exception as exc:  # noqa: BLE001
        print(w.MSG_ERROR.format(message=exc))
        raise SystemExit(EXIT_ERROR)


if __name__ == "__main__":
    main()
# LOCATION: tools/probe_verwerking.py
# ACTION: REPLACE ENTIRE FILE
"""Run the business-paragraph injector against the REAL generated span.

    python tools\\probe_verwerking.py [PROGRAM] [PARAGRAPH]

CORRECTION - the probe cut the span before the line under test

The boundary test was a bare paragraph-header regex:

    ^[A-Z0-9][A-Z0-9-]*[.]$

"END-IF." satisfies it - E, then "ND-IF", then the period - so the scan
treated the orphan terminator as the NEXT paragraph header and ended the
span one line short of it. The probe then reported "removed 0" about a
span that did not contain the thing being probed.

That is the same defect the production code guards with
NON_PARAGRAPH_WORDS, and the reason this tool now imports it rather than
re-deriving the rule.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from converter.composers.restart.process_paragraph_injector import (
    ProcessParagraphInjector,
)
from converter.composers.restart.restart_injection_composer import (
    NON_PARAGRAPH_WORDS,
)
from converter.composers.restart.restart_line_utils import RestartLineUtils

OUTPUT_DIR = Path("mainframe/workspace/Output")
PROGRAM = sys.argv[1] if len(sys.argv) > 1 else "VMDZ1567"
PARAGRAPH = (sys.argv[2] if len(sys.argv) > 2 else "VERWERKING").upper()

HEADER = re.compile(r"^(?P<name>[A-Z0-9][A-Z0-9-]*)[.]$")

utils = RestartLineUtils()


def body_of(line: str) -> str:
    return str(utils.logical(line) or "").strip().upper()


def is_header(text: str) -> bool:
    """A scope terminator wears the header shape but heads nothing."""
    match = HEADER.match(text)
    return bool(match) and match.group("name") not in NON_PARAGRAPH_WORDS


def main() -> int:
    files = sorted(OUTPUT_DIR.glob(f"{PROGRAM}*.cbl"))
    if not files:
        print(f"no {PROGRAM}*.cbl under {OUTPUT_DIR.resolve()}")
        return 1

    path = files[-1]
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()

    start = end = -1
    for index, line in enumerate(raw):
        text = body_of(line)
        if text == f"{PARAGRAPH}.":
            start = index + 1
        elif start >= 0 and is_header(text):
            end = index
            break
    if start < 0:
        print(f"paragraph {PARAGRAPH}. not found in {path.name}")
        return 1
    if end < 0:
        end = len(raw)

    span = raw[start:end]
    print("file      :", path.name)
    print("paragraph :", PARAGRAPH)
    print(f"span      : {start} -> {end}  ({len(span)} line(s))")
    print("ends before:", repr(body_of(raw[end])) if end < len(raw) else "EOF")

    probe = ProcessParagraphInjector.__new__(ProcessParagraphInjector)
    probe.line_utils = utils
    probe.messages = []
    kept = probe._strip_orphan_terminators(span)

    print("--- messages ---")
    for message in probe.messages or ["(none)"]:
        print(" ", message)

    print(f"--- removed {len(span) - len(kept)} line(s) ---")

    print("--- scope lines in the span, before ---")
    for line in span:
        text = body_of(line)
        if text.startswith(("IF ", "EVALUATE ", "END-IF", "END-EVALUATE")):
            print(" ", repr(text))

    print("--- scope lines still present, after ---")
    for line in kept:
        text = body_of(line)
        if text.startswith(("IF ", "EVALUATE ", "END-IF", "END-EVALUATE")):
            print(" ", repr(text))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
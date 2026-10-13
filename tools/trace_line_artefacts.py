"""Names the method that first produces a string carrying a stranded sequence.

trace_artefacts.py measured whole programs and attributed 374 artefacts to
FixedFormatComposer.format. That method is fifty lines of delegation, so the
attribution was correct and useless.

This one works per STRING. A method is blamed when something it RETURNS ends
in a stranded 8-digit sequence and nothing it RECEIVED did. That is the exact
transition, stated as a test rather than as a theory.

    python tools/trace_line_artefacts.py

CORRECTION 1 - dirty_line was renamed and the call sites were not
------------------------------------------------------------------
dirty_text() replaced dirty_line(), but wrap() still called the old name.
The wrapper only runs when a traced method is called, so nothing failed at
import: the first traced call raised NameError inside a try/finally and the
report printed "none". A rename that leaves a caller behind is the same
defect as a locator declared in two files - this one in the tool built to
find it.

CORRECTION 2 - the test assumed an 80-column record
-----------------------------------------------------
    body = value[6:72]

area_body, physical_body and the parser's `body` are FRAGMENTS. The 6:72
window landed in the middle of them, so a fragment ending in a stranded
sequence was judged clean or dirty depending only on its length, and the
probe blamed the first method that happened to produce a short one -
_compose_line, three times, out of 374.

For a full record the real right sequence at 73-80 is excluded. For a
fragment the whole string is examined.

CORRECTION 3 - only str results were examined
-----------------------------------------------
wrapper.wrap_body() and repair_boolean_operator_only_lines() return LISTS,
and parse_line() returns a DICT whose "body" entry is the value we care
about. Checking only isinstance(result, str) made the two most likely
culprits invisible to the probe. Lists, tuples and dict values are examined
now, on both sides of the call.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
import runpy
import sys

# --------------------------------------------------------------------
# What counts as dirty
# --------------------------------------------------------------------
ARTEFACT = re.compile(r"\s\d{8}\s*$")
QUOTED = re.compile(r"'[^']*'")

# Columns 73-80 of a complete record hold the legitimate right sequence
# and must not be mistaken for a stranded one.
RECORD_BODY_END = 72
MIN_INTERESTING_LENGTH = 9

TARGET_PACKAGES = ("converter.composers",)
NAME_FILTER = "fixed_format"

MAX_SAMPLES_PER_METHOD = 4
SAMPLE_WIDTH = 76


def dirty_text(value) -> bool:
    """True when a single-line string ENDS in a stranded 8-digit sequence.

    CORRECTION 4 - "is this a record" was answered by LENGTH.

        window = masked[:72] if len(masked) > 72 else masked

    A 73-character fragment - record[7:], the body WITH its sequence area
    still attached - is longer than 72, so it was clipped to 72 and its
    final digit removed. Seven digits failed the test, the input was
    judged clean, and FixedFormatWrapper was blamed 158 times for
    collapsing whitespace around a sequence that arrived with the string.

    A record is 80+ columns AND carries eight digits at 73-80. Anything
    else is a fragment and is examined whole.
    """
    if not isinstance(value, str):
        return False
    if "\n" in value:
        return False
    if len(value) < MIN_INTERESTING_LENGTH:
        return False

    masked = QUOTED.sub(lambda m: " " * len(m.group()), value)

    is_record = (
        len(masked) >= 80
        and masked[RECORD_BODY_END:80].isdigit()
    )
    window = masked[:RECORD_BODY_END] if is_record else masked

    return bool(ARTEFACT.search(window))


def strings_in(value, depth: int = 0) -> list[str]:
    """Every single-line string reachable in `value`. CORRECTION 3."""
    if depth > 2:
        return []

    if isinstance(value, str):
        return [value] if "\n" not in value else []

    if isinstance(value, (list, tuple, set)):
        found: list[str] = []
        for item in value:
            found.extend(strings_in(item, depth + 1))
        return found

    if isinstance(value, dict):
        found = []
        for item in value.values():
            found.extend(strings_in(item, depth + 1))
        return found

    return []


# --------------------------------------------------------------------
# Attribution
# --------------------------------------------------------------------
class Blame:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.samples: dict[str, list[str]] = {}

    def record(self, label: str, incoming: list[str], outgoing: str) -> None:
        self.counts[label] = self.counts.get(label, 0) + 1

        bucket = self.samples.setdefault(label, [])
        if len(bucket) >= MAX_SAMPLES_PER_METHOD * 2:
            return

        shown = incoming[0] if incoming else "(no string argument)"
        bucket.append("IN : " + shown[:SAMPLE_WIDTH])
        bucket.append("OUT: " + outgoing[:SAMPLE_WIDTH])

    def report(self) -> None:
        print("")
        print("=== methods that first produced a stranded sequence ===")
        if not self.counts:
            print("  none - no single method turns a clean string dirty")
            print("  the artefact is already present in format()'s INPUT")
            return

        for label, total in sorted(
            self.counts.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"  {total:>5}   {label}")
            for sample in self.samples.get(label, []):
                print(f"            {sample}")


BLAME = Blame()


# --------------------------------------------------------------------
# Instrumentation
# --------------------------------------------------------------------
def _is_plain_method(cls, name: str) -> bool:
    """Static and class methods are left alone: setattr of a plain
    function would lose their binding."""
    try:
        raw = inspect.getattr_static(cls, name)
    except AttributeError:
        return False
    if isinstance(raw, (staticmethod, classmethod, property)):
        return False
    return inspect.isfunction(raw)


def wrap(cls, name: str) -> None:
    original = getattr(cls, name, None)
    if not callable(original):
        return

    label = f"{cls.__name__}.{name}"

    def traced(*args, **kwargs):
        result = original(*args, **kwargs)

        outgoing = [v for v in strings_in(result) if dirty_text(v)]
        if outgoing:
            incoming: list[str] = []
            for value in list(args) + list(kwargs.values()):
                incoming.extend(strings_in(value))

            if not any(dirty_text(value) for value in incoming):
                BLAME.record(label, incoming, outgoing[0])

        return result

    traced.__name__ = getattr(original, "__name__", name)
    setattr(cls, name, traced)


def install() -> None:
    methods = 0
    classes = 0

    for package_name in TARGET_PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip package {package_name}: {exc}")
            continue

        for info in pkgutil.walk_packages(
            package.__path__, prefix=package_name + "."
        ):
            if NAME_FILTER not in info.name:
                continue
            try:
                module = importlib.import_module(info.name)
            except Exception as exc:  # noqa: BLE001
                print(f"  skip {info.name}: {type(exc).__name__}: {exc}")
                continue

            for attr_name in dir(module):
                obj = getattr(module, attr_name, None)
                if not inspect.isclass(obj):
                    continue
                if obj.__module__ != info.name:
                    continue

                here = 0
                for method_name in dir(obj):
                    if method_name.startswith("__"):
                        continue
                    if not _is_plain_method(obj, method_name):
                        continue
                    wrap(obj, method_name)
                    here += 1

                if here:
                    classes += 1
                    methods += here
                    print(f"  traced {obj.__name__} ({here})")

    print(f"  total {methods} method(s) on {classes} class(es)")


if __name__ == "__main__":
    print("=== installing line trace ===")
    install()
    print("=== running the update runner ===")
    sys.argv = ["run_update.py"]
    try:
        runpy.run_path("runners/run_update.py", run_name="__main__")
    finally:
        BLAME.report()
"""Attributes fixed-format sequence artefacts to the pass that creates them.

A body carrying an 8-digit run that is not inside quotes is a stranded
right sequence - a record that was rebuilt or joined without stripping
columns 73-80 first.

    python tools/trace_artefacts.py

CORRECTION 1 - TARGETS was declared twice
-------------------------------------------
The second assignment silently won, so adding a class to the first list
changed nothing and round two traced the same six classes as round one.
There is ONE list now, and it is DISCOVERED rather than typed: the real
question is "which classes touch the program text", not "which classes
did I remember to name".

CORRECTION 2 - single-line helpers drowned the signal
------------------------------------------------------
_logical() returns one line, so artefacts() could only ever answer 0 or
1 on it, and those +1/-1 flickers filled the report while the whole-text
methods sat quietly at 1. Only a text of at least MIN_LINES lines is
measured now; everything shorter is ignored.

CORRECTION 3 - the counter never reset between programs
---------------------------------------------------------
A batch converts several programs. Carrying the previous program's count
into the next one produced meaningless deltas at every boundary. A drop
to zero or a new low is treated as a new program.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import re
import runpy
import sys

# --------------------------------------------------------------------
# What counts as an artefact
# --------------------------------------------------------------------
ARTEFACT = re.compile(r"\s\d{8}\s*$")
QUOTED = re.compile(r"'[^']*'")

# A text shorter than this is a fragment, not a program. Measuring
# fragments is what made round one unreadable.
MIN_LINES = 50

# Only report a change at least this large, so one-line churn stays quiet.
REPORT_THRESHOLD = 1

# --------------------------------------------------------------------
# Where to look. ONE list. Packages, not classes.
# --------------------------------------------------------------------
TARGET_PACKAGES = (
    "converter.postprocess",
    "converter.services",
    "converter.composers",
)

SKIP_MODULE_TOKENS = ("__init__", "test_", "_test")


def artefacts(text) -> int:
    """Artefact count, or -1 when `text` is not a whole program."""
    if not isinstance(text, str):
        return -1

    lines = text.splitlines()
    if len(lines) < MIN_LINES:
        return -1

    total = 0
    for line in lines:
        if len(line) < 8:
            continue
        if line[6:7] in ("*", "/"):
            continue
        body = line[6:72]
        masked = QUOTED.sub(lambda m: " " * len(m.group()), body)
        if ARTEFACT.search(masked):
            total += 1
    return total


class Tracker:
    """Running state. One instance, so nothing can shadow it."""

    def __init__(self) -> None:
        self.last = 0
        self.step = 0
        self.blame: dict[str, int] = {}

    def observe(self, label: str, count: int) -> None:
        self.step += 1

        # A new program starts when the count drops to zero from a
        # non-trivial level, or on the first measurement.
        if count == 0 and self.last > 2:
            self.last = 0
            print(f"  ---- new program ----", flush=True)
            return

        delta = count - self.last
        self.last = count

        if abs(delta) < REPORT_THRESHOLD:
            return

        print(
            f"  [{self.step:>4}] {label:<62} {count:>4}  {delta:+d}",
            flush=True,
        )

        if delta > 0:
            self.blame[label] = self.blame.get(label, 0) + delta

    def report(self) -> None:
        print("")
        print("=== cumulative artefacts introduced, worst first ===")
        if not self.blame:
            print("  none")
            return
        for label, total in sorted(
            self.blame.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"  {total:>5}   {label}")


TRACKER = Tracker()


def _is_plain_method(cls, name: str) -> bool:
    """True for an ordinary function. Static and class methods are left
    alone: setattr of a plain function would lose their binding."""
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

        text = result if isinstance(result, str) else None
        if text is None and isinstance(result, list):
            text = "\n".join(str(item) for item in result)
        if text is None and isinstance(result, tuple) and result:
            first = result[0]
            if isinstance(first, str):
                text = first

        count = artefacts(text)
        if count >= 0:
            TRACKER.observe(label, count)

        return result

    traced.__name__ = getattr(original, "__name__", name)
    setattr(cls, name, traced)


def install() -> None:
    traced_classes = 0
    traced_methods = 0

    for package_name in TARGET_PACKAGES:
        try:
            package = importlib.import_module(package_name)
        except Exception as exc:  # noqa: BLE001
            print(f"  skip package {package_name}: {exc}")
            continue

        for info in pkgutil.walk_packages(
            package.__path__, prefix=package_name + "."
        ):
            if any(token in info.name for token in SKIP_MODULE_TOKENS):
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

                wrapped_here = 0
                for method_name in dir(obj):
                    if method_name.startswith("__"):
                        continue
                    if not _is_plain_method(obj, method_name):
                        continue
                    wrap(obj, method_name)
                    wrapped_here += 1

                if wrapped_here:
                    traced_classes += 1
                    traced_methods += wrapped_here

    print(f"  traced {traced_methods} method(s) on {traced_classes} class(es)")


if __name__ == "__main__":
    print("=== installing trace ===")
    install()
    print("=== running the update runner ===")
    sys.argv = ["run_update.py"]
    try:
        runpy.run_path("runners/run_update.py", run_name="__main__")
    finally:
        TRACKER.report()
# LOCATION: tools/trace_obtain_calc.py
# ACTION: CREATE NEW FILE
"""Reports the FIRST pipeline boundary at which a token disappears.

TEMPORARY INSTRUMENTATION. Delete once the consumer is identified.

Wraps each pass named in TARGETS, tests every string argument and every
string in the return value for TOKEN, and prints kept / LOST per call.
Signatures differ across the pipeline, so arguments are inspected by
VALUE rather than by position - nothing here depends on a parameter name.
"""

from __future__ import annotations

import importlib
import inspect
import os
import runpy

TOKEN = "OBTAIN CALC"

TARGETS = [
    ("converter.transformers.cobol_transformer",
     "CobolTransformer", "transform"),
    ("converter.pipeline.conversion_service",
     "ConversionService", "_stage"),
    ("converter.transformers.field_reference_rewriter",
     "FieldReferenceRewriter", "rewrite"),
    ("converter.pipeline.conversion_service",
     "ConversionService", "_apply_db2_infrastructure"),
    ("converter.pipeline.conversion_service",
     "ConversionService", "_apply_legacy_restart_generator"),
    ("converter.pipeline.conversion_service",
     "ConversionService", "_apply_cleanup_composers"),
    ("converter.pipeline.conversion_service",
     "ConversionService", "_apply_commit_cleanup"),
    # Module path varies by tree; failures are reported, never fatal.
    ("converter.pipeline.conversion.conversion_layout_pipeline",
     "ConversionLayoutPipeline", "finish"),
    ("converter.pipeline.conversion_layout_pipeline",
     "ConversionLayoutPipeline", "finish"),
]


def _carries(value) -> bool:
    if isinstance(value, str):
        return TOKEN in value.upper()
    if isinstance(value, (list, tuple)):
        return any(_carries(item) for item in value)
    return False


def _wrap(module_name: str, class_name: str, method_name: str) -> str:
    module = importlib.import_module(module_name)
    owner = getattr(module, class_name)
    static = isinstance(
        inspect.getattr_static(owner, method_name), staticmethod
    )
    original = getattr(owner, method_name)
    label = f"{class_name}.{method_name}"

    def traced(*args, **kwargs):
        before = _carries(list(args)) or _carries(list(kwargs.values()))
        result = original(*args, **kwargs)
        after = _carries(result)
        if before and not after:
            print(f"[TRACE] LOST  -> {label}", flush=True)
        elif before:
            print(f"[TRACE] kept  -> {label}", flush=True)
        return result

    setattr(owner, method_name, staticmethod(traced) if static else traced)
    return label


if __name__ == "__main__":
    os.environ.setdefault("DUMP_EXPANDED", os.path.join(os.getcwd(), "_expanded"))

    for module_name, class_name, method_name in TARGETS:
        try:
            print("[TRACE] wrapped", _wrap(module_name, class_name, method_name))
        except Exception as error:  # noqa: BLE001
            print(f"[TRACE] skip {class_name}.{method_name}: {error}")

    runpy.run_module("runners.convert_programs", run_name="__main__")
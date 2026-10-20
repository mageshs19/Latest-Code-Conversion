# LOCATION: tools/trace_lr_select.py
# ACTION: CREATE NEW FILE
"""Reports the FIRST pipeline boundary at which the generated LR keyed
SELECT disappears - or proves it was never produced.

TEMPORARY INSTRUMENTATION. Delete once the consumer is identified.

'FROM DZBEFFTV' is unique to the generated keyed read: the cursor
DECLARE reads FROM DZEVEFTV, and the INCLUDE carries no FROM.
"""

from __future__ import annotations

import importlib
import inspect
import runpy

TOKEN = "FROM DZBEFFTV"

TARGETS = [
    ("converter.transformers.cobol_transformer",
     "CobolTransformer", "transform"),
    ("converter.pipeline.conversion.conversion_pipeline_steps",
     "ConversionPipelineSteps", "_stage"),
    ("converter.transformers.field_reference_rewriter",
     "FieldReferenceRewriter", "rewrite"),
    ("converter.pipeline.conversion.conversion_pipeline_steps",
     "ConversionPipelineSteps", "_apply_db2_infrastructure"),
    ("converter.pipeline.conversion.conversion_pipeline_steps",
     "ConversionPipelineSteps", "_apply_legacy_restart_generator"),
    ("converter.pipeline.conversion.conversion_pipeline_steps",
     "ConversionPipelineSteps", "_apply_cleanup_composers"),
    ("converter.pipeline.conversion.conversion_pipeline_steps",
     "ConversionPipelineSteps", "_apply_commit_cleanup"),
    ("converter.pipeline.conversion.conversion_layout_pipeline",
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
        elif before or after:
            print(f"[TRACE] kept  -> {label}", flush=True)
        return result

    setattr(owner, method_name, staticmethod(traced) if static else traced)
    return label


if __name__ == "__main__":
    for module_name, class_name, method_name in TARGETS:
        try:
            print("[TRACE] wrapped", _wrap(module_name, class_name, method_name))
        except Exception as error:  # noqa: BLE001
            print(f"[TRACE] skip {class_name}.{method_name}: {error}")

    runpy.run_module("runners.convert_programs", run_name="__main__")
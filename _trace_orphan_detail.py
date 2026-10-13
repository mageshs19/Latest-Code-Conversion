import re
import runpy
import sys

TARGET_PROGRAM = "VMDZ7200"

def verwerking_slice(cobol_text):
    if not cobol_text or "VERWERKING" not in cobol_text.upper():
        return None
    lines = cobol_text.splitlines()
    start = None
    for i, raw in enumerate(lines):
        body = raw[7:72] if len(raw) > 7 else raw
        if body.strip().upper() == "VERWERKING.":
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    header_pattern = re.compile(r"^[A-Z0-9][A-Z0-9-]*\.$")
    for i in range(start + 1, len(lines)):
        raw = lines[i]
        body = raw[7:72] if len(raw) > 7 else raw
        stripped = body.strip().upper()
        if header_pattern.match(stripped) and "IF" not in stripped and "WHEN" not in stripped:
            end = i
            break
    return lines[start:end]

def orphan_lines(slice_lines):
    if not slice_lines:
        return []
    depth = {"IF": 0, "EVALUATE": 0}
    orphans = []
    end_pattern = re.compile(r"^END-(IF|EVALUATE)\.?$")
    for raw in slice_lines:
        body = raw[7:72] if len(raw) > 7 else raw
        indicator = raw[6] if len(raw) > 6 else " "
        if indicator in ("*", "/"):
            continue
        text = " ".join(body.upper().split())
        m = end_pattern.match(text)
        if m:
            verb = m.group(1)
            if depth[verb] <= 0:
                orphans.append(raw.rstrip())
            else:
                depth[verb] -= 1
            continue
        tokens = text.replace(".", " ").split()
        if tokens and tokens[0] in depth:
            depth[tokens[0]] += 1
    return orphans

def is_target(cobol_text):
    return bool(cobol_text) and TARGET_PROGRAM in cobol_text.upper()

def dump_if_target(tag, cobol_text):
    if not is_target(cobol_text):
        return
    sl = verwerking_slice(cobol_text)
    orphans = orphan_lines(sl)
    print("---- " + tag + " ---- orphans=" + str(len(orphans)))
    if sl:
        for raw in sl:
            print("    " + raw.rstrip())
    if orphans:
        print("    ORPHAN LINES:")
        for o in orphans:
            print("      -> " + o)

import converter.pipeline.run as run_mod
_orig_run_stage = run_mod.run_stage

def traced_run_stage(name, doc, *a, **kw):
    before_text = getattr(doc, "cobol", "")
    if is_target(before_text):
        dump_if_target("BEFORE " + name, before_text)
    result = _orig_run_stage(name, doc, *a, **kw)
    after_text = getattr(result, "cobol", "")
    if is_target(after_text):
        dump_if_target("AFTER " + name, after_text)
    return result

run_mod.run_stage = traced_run_stage

try:
    from converter.composers.restart.restart_injection_composer import RestartInjectionComposer
    _orig_process = RestartInjectionComposer._process

    def traced_process(self, lines, config):
        text_before = "\n".join(lines)
        if is_target(text_before):
            dump_if_target("BEFORE RestartInjectionComposer._process", text_before)
        result = _orig_process(self, lines, config)
        text_after = "\n".join(result)
        if is_target(text_after):
            dump_if_target("AFTER RestartInjectionComposer._process", text_after)
        return result

    RestartInjectionComposer._process = traced_process
except Exception as e:
    print("(could not patch RestartInjectionComposer._process: " + str(e) + ")")

# Widen: patch every composer class the factory is known to construct
WIDE_PATCH_TARGETS = [
    ("converter.composers.output_write_paragraph_composer", "OutputWriteParagraphComposer", "compose"),
    ("converter.composers.record_materialisation.record_materialisation_composer", "RecordMaterialisationComposer", "compose"),
    ("converter.composers.cobol_cleanup_composer", "CobolCleanupComposer", "compose"),
    ("converter.composers.final_cobol_fix_composer", "FinalCobolFixComposer", "compose"),
    ("converter.composers.structural_safety_composer", "StructuralSafetyComposer", "compose"),
]

for module_name, class_name, method_name in WIDE_PATCH_TARGETS:
    try:
        mod = __import__(module_name, fromlist=[class_name])
        cls = getattr(mod, class_name)
        orig_method = getattr(cls, method_name)

        def make_wrapper(orig, label):
            def wrapper(self, text, *a, **kw):
                if is_target(text):
                    dump_if_target("BEFORE " + label, text)
                result = orig(self, text, *a, **kw)
                out_text = result if isinstance(result, str) else getattr(result, "cobol", "")
                if is_target(out_text):
                    dump_if_target("AFTER " + label, out_text)
                return result
            return wrapper

        setattr(cls, method_name, make_wrapper(orig_method, class_name))
    except Exception as e:
        print("(skip " + class_name + ": " + str(e) + ")")

sys.argv = ["run_update.py"]
runpy.run_path("runners/run_update.py", run_name="__main__")

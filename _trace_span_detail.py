import re
import runpy
import sys

TARGET = "VMDZ1567"

def program_id_of(text):
    if not text:
        return "?"
    m = re.search(r"PROGRAM-ID\.\s+([A-Z0-9-]+)", text, re.IGNORECASE)
    return m.group(1).upper() if m else "?"

SEEN_PROGRAMS = set()
DONE = {"fired": False}

try:
    from converter.composers.restart.restart_injection_composer import RestartInjectionComposer
    _orig_process = RestartInjectionComposer._process

    def traced_process(self, lines, config):
        full_text_before = "\n".join(lines)
        pid = program_id_of(full_text_before)
        SEEN_PROGRAMS.add(pid)

        if pid != TARGET or DONE["fired"]:
            return _orig_process(self, lines, config)

        span = self._span_named(lines, config.names.process_paragraph)
        if span is None:
            print("TRACE: span is None -- paragraph not found for", pid)
            return _orig_process(self, lines, config)

        print("=== SPAN ===")
        print("process_paragraph name:", config.names.process_paragraph)
        print("span.start:", span.start, " span.end:", span.end)

        body = lines[span.start:span.end]
        print()
        print("=== BODY (lines[span.start:span.end]) ===")
        for i, l in enumerate(body):
            print(str(span.start+i).rjust(5) + " | " + l)

        print()
        print("=== 5 LINES IMMEDIATELY AFTER span.end ===")
        for i, l in enumerate(lines[span.end:span.end+5]):
            print(str(span.end+i).rjust(5) + " | " + l)

        from converter.composers.restart.process_paragraph_injector import ProcessParagraphInjector
        injector = ProcessParagraphInjector(config, self.line_utils)
        repaired = injector.inject(body)

        print()
        print("=== REPAIRED (injector.inject output) ===")
        for i, l in enumerate(repaired):
            print(str(i).rjust(5) + " | " + l)

        print()
        print("=== injector.messages ===")
        for m in injector.messages:
            print("  - " + m)

        spliced = lines[:span.start] + list(repaired) + lines[span.end:]
        join1 = span.start
        join2 = span.start + len(repaired)

        print()
        print("=== JOIN POINT 1 (span.start=" + str(join1) + ") ===")
        for i in range(max(0, join1-3), min(len(spliced), join1+3)):
            marker = " <== " if i == join1 else "     "
            print(str(i).rjust(5) + marker + spliced[i])

        print()
        print("=== JOIN POINT 2 (end of repaired=" + str(join2) + ") ===")
        for i in range(max(0, join2-3), min(len(spliced), join2+3)):
            marker = " <== " if i == join2 else "     "
            print(str(i).rjust(5) + marker + spliced[i])

        DONE["fired"] = True
        return _orig_process(self, lines, config)

    RestartInjectionComposer._process = traced_process
except Exception as e:
    print("(could not patch: " + str(e) + ")")

sys.argv = ["run_update.py"]
runpy.run_path("runners/run_update.py", run_name="__main__")

print()
print("=== PROGRAMS SEEN BY RestartInjectionComposer._process THIS RUN ===")
for p in sorted(SEEN_PROGRAMS):
    print("  -", p)
print("Target fired:", DONE["fired"])

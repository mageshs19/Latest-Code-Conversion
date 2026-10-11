# LOCATION: converter/composers/restart/restart_injection_composer.py
# ACTION: REPLACE ENTIRE FILE
"""Orchestrates the restart injection for one update program.

CONTRACT

    compose(text, role=..., program_kind=..., totals=...) -> (text, messages)

This module ORCHESTRATES. Every COBOL line it writes comes from M4, M5,
M6, M7 or M8. It owns the ORDER of the passes and the geometry of the
splice, nothing else.

ALL OR NOTHING

A retrieval program, a program that does not reference the restart
table, a missing DCLGEN role or an unusable RestartConfig all return
the SOURCE UNCHANGED plus one message per reason.

CORRECTION 1 - collaborator construction was GUESSED

LegacyRestartCleanup(config, line_utils) is config-aware on purpose: it
cannot separate a LEGACY restart paragraph from the family this run is
about to write unless it knows the generated names. The first cut
caught TypeError and retried with fewer arguments, which reported the
wrong arity and could have built a cleanup configured for a different
program. Guessing a collaborator is the same defect as inventing a data
name. The constructor is now called the way it is declared.

CORRECTION 2 - END-EXEC. was read as a paragraph header

`END-EXEC.` wears the header SHAPE - one word, one period - and was not
in NON_PARAGRAPH_DOTTED_LINES, which only knew CONTINUE / EXIT /
END-IF. The consequence is not cosmetic: every pass here is SPAN based,
so a false boundary truncates the enclosing paragraph.

NON_PARAGRAPH_WORDS is therefore a SUPERSET of the shared vocabulary
plus every COBOL scope terminator. It is exported so the tests assert
against production vocabulary instead of a private copy.

FOLLOW-UP for M10: converter/composers/restart/legacy_restart_cleanup.py
removes paragraphs by span too and carries the same blind spot.

CORRECTION 3 - the blank separator drifted

The insertion boundary is now CANONICALISED: trailing blanks at the
insertion point are removed and exactly one separator is written per
paragraph, so the line count cannot drift whatever the input looked
like.

CORRECTION 4 - the business span was reported as "short" without proof

An orphan END-IF survived the business paragraph repair, and the first
theory was that _span_named handed the injector a truncated body. The
diagnostic below proved the opposite: the span is 58 lines, the whole
paragraph. Both the SPAN and the SCOPE LINES inside it are now
reported, so the next person reads a measurement instead of inheriting
a theory. A comment asserting a cause nobody measured is worse than no
comment.

WHY THE FAMILY IS APPENDED AFTER THE MAINLINE, NOT BEFORE ITS STOP RUN

A paragraph HEADER between the mainline statements and its own STOP RUN
recreates the fall-through defect M6 closed. The family is appended
after the paragraph whose last statement is STOP RUN and before
END PROGRAM when one is present.

IDEMPOTENCE

  * the mainline paragraph BODY is replaced wholesale,
  * the reader is rebuilt only while needs_rebuild() is true,
  * ProcessParagraphInjector is idempotent by its own M7 contract,
  * any paragraph carrying a generated name is DROPPED before the
    family is spliced, and the boundary is canonicalised.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from converter.composers.restart.legacy_restart_cleanup import (
    LegacyRestartCleanup,
)
from converter.composers.restart.process_paragraph_injector import (
    ProcessParagraphInjector,
)
from converter.generators.restart.read_paragraph_builder import (
    RestartReadParagraphBuilder,
)
from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_flow_builder import (
    RestartFlowBuilder,
)
from converter.generators.restart.restart_main_flow_builder import (
    RestartMainFlowBuilder,
)
from converter.generators.restart.restart_name_resolver import (
    RestartNameResolver,
)
from converter.generators.restart.restart_sql_builder import RestartSqlBuilder
from patterns.restart_patterns import (
    OPEN_INPUT_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
)
from rules.restart_cleanup_rules import NON_PARAGRAPH_DOTTED_LINES
from rules.restart_standard_rules import (
    NOT_APPLICABLE_REASONS,
    RESTART_DIAGNOSTICS,
    RESTART_PARAGRAPH_ROLES,
    ROLE_COMMIT,
    ROLE_CONTROL,
)
from converter.composers.restart.restart_storage_injector import (
    RestartStorageInjector,
)

PROGRAM_KIND_RETRIEVAL = "retrieval"
PROGRAM_KIND_UPDATE = "update"

MESSAGE_PREFIX = "Restart injection:"
END_PROGRAM = "END PROGRAM"
MAINLINE_LABEL = "PROCEDURE DIVISION"

# Statement prefixes worth reporting when a span is handed to a repair
# pass. Scope openers and closers only - enough to audit the arithmetic
# the injector performs, without dumping the paragraph.
SCOPE_REPORT_PREFIXES = ("IF ", "EVALUATE ", "END-IF", "END-EVALUATE")

# COBOL scope terminators and no-ops. Every one of them is one word
# followed by a period, which is also the paragraph-header shape. These
# are LANGUAGE tokens, never site vocabulary, so naming them here does
# not put a program / paragraph / record name in a composer.
SCOPE_TERMINATOR_WORDS = (
    "CONTINUE",
    "END-ADD",
    "END-CALL",
    "END-COMPUTE",
    "END-DELETE",
    "END-DIVIDE",
    "END-EVALUATE",
    "END-EXEC",
    "END-IF",
    "END-MULTIPLY",
    "END-PERFORM",
    "END-READ",
    "END-RETURN",
    "END-REWRITE",
    "END-SEARCH",
    "END-START",
    "END-STRING",
    "END-SUBTRACT",
    "END-UNSTRING",
    "END-WRITE",
    "EXIT",
    "GOBACK",
)

NON_PARAGRAPH_WORDS = tuple(
    sorted(
        {
            *(
                str(word).strip().upper().rstrip(".")
                for word in NON_PARAGRAPH_DOTTED_LINES
            ),
            *SCOPE_TERMINATOR_WORDS,
        }
        - {""}
    )
)

# Attributes a DCLGEN role may carry a restart-table token under. The
# attribute NAMES are schema; the VALUES are site vocabulary.
ROLE_TOKEN_ATTRIBUTES = (
    "table_name",
    "include_name",
    "host_record",
    "host_record_name",
)

SHARED_CLEANUP_METHODS = ("compose", "apply", "clean")

POSITIONAL_KINDS = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)


@dataclass(frozen=True)
class _Span:
    """One paragraph: header line, first body line, first line after."""

    name: str
    header: int
    start: int
    end: int


class RestartInjectionComposer:
    """Applies the complete restart family to one converted program."""

    def __init__(
        self,
        line_utils,
        *,
        scheme: str | None = None,
        shared_cleanups: Iterable[Any] = (),
    ) -> None:
        self.line_utils = line_utils
        self.scheme = scheme
        self.shared_cleanups = tuple(shared_cleanups or ())
        self.messages: list[str] = []

    #
    # Public surface
    #
    def compose(
        self,
        text: str,
        *,
        role: Any = None,
        program_kind: str = PROGRAM_KIND_UPDATE,
        totals: Sequence[str] = (),
    ) -> tuple[str, list[str]]:
        """Return (converted text, messages). Never raises on refusal."""
        self.messages = []
        source = str(text or "")
        lines = self._lines(source)

        reason = self._not_applicable(lines, role, program_kind)
        if reason:
            self._say(reason)
            return source, list(self.messages)

        names, report = RestartNameResolver(self.line_utils).resolve(lines)
        self.messages.extend(report.messages)

        config = self._config(role, names)
        if not config.is_usable():
            self._refuse(config)
            return source, list(self.messages)

        self._diagnostic("payload_measured", length=config.payload_full_length)
        if self.scheme:
            self._diagnostic("scheme_selected", scheme=self.scheme)

        lines = self._clean(lines, config)
        lines = self._storage(lines, config)
        lines = self._mainline(lines, config, totals)
        lines, appended = self._reader(lines, config)
        lines = self._process(lines, config)
        lines = self._splice(lines, config, appended)

        return self._hand_off(lines)

    #
    # 1. Classification
    #
    def _not_applicable(self, lines: list[str], role: Any, kind: str) -> str:
        if str(kind or "").strip().lower() != PROGRAM_KIND_UPDATE:
            return NOT_APPLICABLE_REASONS["retrieval"]
        if role is None:
            return NOT_APPLICABLE_REASONS["dclgen_unresolved"]
        if not self._references_restart_table(lines, role):
            return NOT_APPLICABLE_REASONS["no_restart_table"]
        return ""

    def _references_restart_table(self, lines: list[str], role: Any) -> bool:
        tokens = [
            str(getattr(role, attribute, "") or "").strip().upper()
            for attribute in ROLE_TOKEN_ATTRIBUTES
        ]
        tokens = [token for token in tokens if token]
        if not tokens:
            return False
        body = " ".join(self._logical(line) for line in lines)
        return any(token in body for token in tokens)

    #
    # 2 + 3. Config
    #
    def _config(self, role: Any, names) -> RestartConfig:
        if self.scheme is None:
            return RestartConfig.build(role, names)
        return RestartConfig.build(role, names, self.scheme)

    def _refuse(self, config: RestartConfig) -> None:
        for name in config.missing():
            self._say(f"{name} unresolved; no restart family emitted.")
        if config.retention_days <= 0:
            self._say(
                "the restart role carries no retention value; "
                "no restart family emitted."
            )

    #
    # 4. Legacy cleanup
    #
    def _clean(self, lines: list[str], config: RestartConfig) -> list[str]:
        cleanup = LegacyRestartCleanup(config, self.line_utils)
        cleaned = list(cleanup.clean(list(lines)))
        self.messages.extend(getattr(cleanup, "messages", []) or [])
        removed = len(lines) - len(cleaned)
        if removed > 0:
            self._diagnostic("legacy_removed", count=removed)
        return cleaned

    #
    # 4b. Working storage
    #
    def _storage(self, lines: list[str], config: RestartConfig) -> list[str]:
        """Declare the fields the generated paragraphs will reference.

        Runs BEFORE the mainline so every later span is computed over
        the final DATA DIVISION. It declares only what is absent, so a
        program that already carries the groups is untouched.
        """
        injector = RestartStorageInjector(config, self.line_utils)
        placed = injector.inject(lines)
        self.messages.extend(injector.messages)
        return placed
    #
    # 5. Mainline
    #
    def _mainline(
        self,
        lines: list[str],
        config: RestartConfig,
        totals: Sequence[str],
    ) -> list[str]:
        builder = RestartMainFlowBuilder(config)
        body = builder.build(totals)
        self.messages.extend(builder.messages)
        if not body:
            return lines

        span = self._mainline_span(lines)
        if span is None:
            self._say("no OPEN INPUT found; the mainline was left unchanged.")
            return lines

        self._diagnostic(
            "control_injected", paragraph=config.paragraph(ROLE_CONTROL)
        )
        self._diagnostic(
            "commit_injected", paragraph=config.paragraph(ROLE_COMMIT)
        )
        self._diagnostic("stop_run_injected", paragraph=span.name)
        return lines[: span.start] + list(body) + lines[span.end :]

    def _mainline_span(self, lines: list[str]) -> _Span | None:
        index = self._open_input_index(lines)
        if index < 0:
            return None

        spans = self._spans(lines)
        for span in spans:
            if span.header <= index < span.end:
                return span

        # Headerless mainline: the statements between PROCEDURE DIVISION
        # and the first paragraph header. Refusing them would leave the
        # program with no STOP RUN at all.
        start = self._procedure_index(lines)
        if start < 0 or index <= start:
            return None
        end = spans[0].header if spans else self._insert_index(lines)
        if index >= end:
            return None
        self._say(
            "the mainline carries no paragraph header; using the "
            "statements that follow PROCEDURE DIVISION."
        )
        return _Span(
            name=MAINLINE_LABEL, header=start, start=start + 1, end=end
        )

    def _open_input_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if logical and OPEN_INPUT_PATTERN.match(logical):
                return index
        return -1

    #
    # 6. Reader
    #
    def _reader(
        self,
        lines: list[str],
        config: RestartConfig,
    ) -> tuple[list[str], list[Any]]:
        builder = RestartReadParagraphBuilder(config)
        span = self._span_named(lines, config.names.read_paragraph)

        if span is None:
            paragraph = builder.build()
            self.messages.extend(builder.messages)
            self._say(
                f"{config.names.read_paragraph} was not declared; "
                "it is appended with the restart family."
            )
            return lines, [paragraph]

        if not self._needs_rebuild(builder, lines[span.start : span.end]):
            self._say(f"{span.name} already complete; not rebuilt.")
            return lines, []

        paragraph = builder.build()
        self.messages.extend(builder.messages)
        rendered = list(paragraph.lines())
        return lines[: span.header] + rendered + lines[span.end :], []

    @staticmethod
    def _needs_rebuild(builder: Any, body: list[str]) -> bool:
        """Ask M8 using the arity it declares, measured once."""
        method = builder.needs_rebuild
        try:
            wanted = [
                parameter
                for parameter in inspect.signature(method).parameters.values()
                if parameter.kind in POSITIONAL_KINDS
            ]
        except (TypeError, ValueError):
            wanted = [None]
        return bool(method(body) if wanted else method())

    #
    # 7. Business paragraph
    #
    def _process(self, lines: list[str], config: RestartConfig) -> list[str]:
        span = self._span_named(lines, config.names.process_paragraph)
        if span is None:
            self._say(
                f"{config.names.process_paragraph} not found; "
                "the business paragraph was left unchanged."
            )
            return lines

        body = lines[span.start : span.end]
        self._report_span(span, body)

        # The injector gets THIS composer's line utility, so the two
        # cannot disagree about where a logical line starts and ends.
        injector = ProcessParagraphInjector(config, self.line_utils)
        repaired = injector.inject(body)
        self.messages.extend(injector.messages)
        return lines[: span.start] + list(repaired) + lines[span.end :]

    def _report_span(self, span: _Span, body: list[str]) -> None:
        """Say what the repair pass was given, not what we assume.

        An orphan END-IF survived this paragraph and the first theory
        was a truncated span. The span turned out to be the whole
        paragraph, so the theory was wrong and the measurement is what
        belongs in the log.
        """
        self._say(
            f"{span.name}: repairing lines {span.start}-{span.end} "
            f"({span.end - span.start} line(s))."
        )

        scope = [
            logical
            for logical in (self._logical(line) for line in body)
            if logical.startswith(SCOPE_REPORT_PREFIXES)
        ]
        self._say(f"{span.name}: scope lines handed to the injector = {scope}")

    #
    # 8. The restart family
    #
    def _splice(
        self,
        lines: list[str],
        config: RestartConfig,
        appended: list[Any],
    ) -> list[str]:
        sql = RestartSqlBuilder(config)
        flow = RestartFlowBuilder(config)
        built = list(sql.build_all()) + list(flow.build_all())
        self.messages.extend(sql.messages)
        self.messages.extend(flow.messages)

        ordered = self._in_role_order(built) + list(appended)
        if not ordered:
            return lines

        lines = self._drop(lines, {str(p.name).upper() for p in ordered})

        rendered: list[str] = []
        for paragraph in ordered:
            rendered.append("")
            rendered.extend(paragraph.lines())

        index = self._insert_index(lines)
        head = list(lines[:index])
        tail = list(lines[index:])
        # Canonical boundary: one separator per paragraph, written here
        # and nowhere else, so the blank count cannot drift.
        while head and not str(head[-1]).strip():
            head.pop()

        self._diagnostic("paragraphs_generated", count=len(ordered))
        return head + rendered + tail

    @staticmethod
    def _in_role_order(paragraphs: list[Any]) -> list[Any]:
        by_role = {paragraph.role: paragraph for paragraph in paragraphs}
        ordered = [
            by_role[role]
            for role in RESTART_PARAGRAPH_ROLES
            if role in by_role
        ]
        ordered.extend(
            paragraph
            for paragraph in paragraphs
            if paragraph.role not in RESTART_PARAGRAPH_ROLES
        )
        return ordered

    def _drop(self, lines: list[str], names: set[str]) -> list[str]:
        doomed: set[int] = set()
        for span in self._spans(lines):
            if span.name.upper() not in names:
                continue
            start = span.header
            while start > 0 and not str(lines[start - 1]).strip():
                start -= 1
            doomed.update(range(start, span.end))
            self._say(f"replaced the existing {span.name} paragraph.")
        if not doomed:
            return lines
        return [
            line for index, line in enumerate(lines) if index not in doomed
        ]

    #
    # Paragraph geometry
    #
    def _spans(self, lines: list[str]) -> list[_Span]:
        headers = self._headers(lines)
        limit = self._insert_index(lines)
        spans: list[_Span] = []
        for position, (index, name) in enumerate(headers):
            following = (
                headers[position + 1][0]
                if position + 1 < len(headers)
                else limit
            )
            spans.append(
                _Span(
                    name=name,
                    header=index,
                    start=index + 1,
                    end=max(min(following, limit), index + 1),
                )
            )
        return spans

    def _headers(self, lines: list[str]) -> list[tuple[int, str]]:
        found: list[tuple[int, str]] = []
        started = False
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if not logical:
                continue
            if PROCEDURE_DIVISION_PATTERN.match(logical):
                started = True
                continue
            if not started:
                continue
            match = PARAGRAPH_HEADER_PATTERN.match(logical)
            if not match:
                continue
            name = match.group("name").upper()
            if self._is_not_a_paragraph(name):
                continue
            found.append((index, name))
        return found

    @staticmethod
    def _is_not_a_paragraph(name: str) -> bool:
        """END-EXEC. / END-IF. / EXIT. wear the header SHAPE but head nothing."""
        return (
            str(name or "").strip().upper().rstrip(".") in NON_PARAGRAPH_WORDS
        )

    def _span_named(self, lines: list[str], name: str) -> _Span | None:
        target = str(name or "").strip().upper()
        if not target:
            return None
        for span in self._spans(lines):
            if span.name.upper() == target:
                return span
        return None

    def _procedure_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            logical = self._logical(line)
            if logical and PROCEDURE_DIVISION_PATTERN.match(logical):
                return index
        return -1

    def _insert_index(self, lines: list[str]) -> int:
        for index, line in enumerate(lines):
            if self._logical(line).startswith(END_PROGRAM):
                return index
        return len(lines)

    #
    # 9. Shared retrieval cleanups
    #
    def _hand_off(self, lines: list[str]) -> tuple[str, list[str]]:
        text = self._join(lines)
        for cleanup in self.shared_cleanups:
            call = cleanup if callable(cleanup) else None
            if call is None:
                for attribute in SHARED_CLEANUP_METHODS:
                    candidate = getattr(cleanup, attribute, None)
                    if callable(candidate):
                        call = candidate
                        break
            if call is None:
                self._say(
                    f"shared cleanup {cleanup!r} is not callable; skipped."
                )
                continue
            result = call(text)
            if isinstance(result, str) and result:
                text = result
            self.messages.extend(getattr(cleanup, "messages", []) or [])
        return text, list(self.messages)

    #
    # Line handling - the SHARED retrieval utility, never a local parser
    #
    def _logical(self, line: str) -> str:
        text = str(self.line_utils.logical(line) or "").strip()
        if not text or self.line_utils.is_comment(text):
            return ""
        return " ".join(text.upper().split())

    def _lines(self, text: str) -> list[str]:
        if self._has_text_helpers():
            return list(self.line_utils.lines(text))
        return str(text or "").splitlines()

    def _join(self, lines: list[str]) -> str:
        if self._has_text_helpers():
            return str(self.line_utils.join(list(lines)))
        return "\n".join(str(line) for line in lines)

    def _has_text_helpers(self) -> bool:
        """Split and join must come from the SAME source or the round
        trip loses idempotence."""
        return callable(getattr(self.line_utils, "lines", None)) and callable(
            getattr(self.line_utils, "join", None)
        )

    #
    # Reporting
    #
    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")

    def _diagnostic(self, key: str, **values) -> None:
        template = RESTART_DIAGNOSTICS.get(str(key or ""), "")
        if template:
            self.messages.append(template.format(**values))


__all__ = [
    "END_PROGRAM",
    "MAINLINE_LABEL",
    "MESSAGE_PREFIX",
    "NON_PARAGRAPH_WORDS",
    "PROGRAM_KIND_RETRIEVAL",
    "PROGRAM_KIND_UPDATE",
    "RestartInjectionComposer",
    "SCOPE_REPORT_PREFIXES",
    "SCOPE_TERMINATOR_WORDS",
]
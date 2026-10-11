"""Orchestrates the restart injection for one update program.

CONTRACT

    compose(text, role=..., program_kind=..., totals=...) -> (text, messages)

This module ORCHESTRATES. Every COBOL line it writes comes from M4, M5,
M6, M7 or M8; every boundary it uses comes from
RestartParagraphGeometry. It owns the ORDER of the passes and the
geometry of the splice, nothing else.

ALL OR NOTHING

A retrieval program, a missing DCLGEN role, a role with no restart
table and no supporting evidence, or an unusable RestartConfig all
return the SOURCE UNCHANGED plus one message per reason.

CORRECTION 1 - collaborator construction was GUESSED
LegacyRestartCleanup(config, line_utils) is config-aware on purpose: it
cannot separate a LEGACY restart paragraph from the family this run is
about to write unless it knows the generated names. The first cut
caught TypeError and retried with fewer arguments. Guessing a
collaborator is the same defect as inventing a data name. The
constructor is now called the way it is declared.

CORRECTION 2 - END-EXEC. was read as a paragraph header
Moved to restart_injection_geometry.py, CORRECTION A.

CORRECTION 3 - the blank separator drifted
The insertion boundary is CANONICALISED: trailing blanks at the
insertion point are removed and exactly one separator is written per
paragraph, so the line count cannot drift whatever the input looked
like.

CORRECTION 4 - the business span was reported as "short" without proof
An orphan END-IF survived the business paragraph repair, and the first
theory was a truncated span. The diagnostic proved the opposite: the
span is the whole paragraph. Both the SPAN and the SCOPE LINES inside
it are reported, so the next person reads a measurement instead of
inheriting a theory.

CORRECTION 5 - the applicability gate was CIRCULAR
_not_applicable() scanned the CONVERTED text for the restart table and
refused when it was absent. It is always absent: that reference is the
code this composer writes. The checkpoint record that DID prove
applicability had already been commented out by the unmapped-record
pass, and _logical() drops comments, so the last evidence was invisible
too. A program whose context, role and retention had all resolved -

    Restart context: checkpoint record FFRECAB found in the source.
    Restart context: built for DZ01RSTV with a retention of 7 day(s).
    Restart role:    built from Sheet Mapping table DZ01RSTV, ...

was then refused with

    Restart injection: Program does not reference a restart table;
                       restart control not applied.

A RESOLVED ROLE IS NOW THE AUTHORITY. RestartRoleResolver only builds a
role after RestartContextBuilder found a checkpoint record in the
PRE-TRANSFORMATION source, so the question the text scan was asking has
already been answered upstream, correctly, by something that could
still see the evidence.

The text scan survives as a FALLBACK for a role carrying no usable
token, and it now reads comment lines.

CORRECTION 6 - the mainline was located by OPEN INPUT
_mainline_span() returned the paragraph containing the first
OPEN INPUT. OPEN INPUT is where the generated flow BEGINS; it is not
what makes a paragraph the mainline. VMDZ1526 opens its file in an
initialisation paragraph, so the flow - which ends in STOP RUN - was
spliced into the INITIALISER while the real mainline kept its own.
The program carried TWO STOP RUNs and the restart control ran inside
initialisation.

The rule is now one sentence:

    The mainline is the paragraph that TERMINATES the program, and the
    flow replaces it from the first OPEN INPUT or the first
    PERFORM <process_paragraph>, whichever comes first - suppressing
    the template's OPEN and priming READ when they already exist
    outside the replaced region.

_termination_index() answers the first clause, _replacement_start()
the second, and the suppression flags the third.

CORRECTION 7 - suppression asked too broad a question
The priming read and the loop-tail read that ProcessParagraphInjector
appends to the business paragraph are the SAME statement text serving
different purposes. Asking "does this statement exist outside the
replaced region" found the tail, suppressed the priming read, and made
the pass non-idempotent: run 1 wrote it, run 2 deleted it, and the loop
would then process a record it had never read.
tests/restart/test_m10b_stage_adapter.py caught it.

The search now excludes BOTH the region being replaced AND the process
paragraph, so what remains is an initialisation the program genuinely
performs before the generated flow. OPEN INPUT needs no such narrowing:
a second OPEN is always wrong, wherever it is.

CORRECTION 8 - locators were duplicated in this file
_termination_index and _perform_index_within were declared here AND in
restart_injection_geometry.py, where the composer's copies shadowed the
base class. Location logic has ONE owner. They live in geometry; this
file calls them.

WHY THE FAMILY IS APPENDED AFTER THE MAINLINE, NOT BEFORE ITS STOP RUN

A paragraph HEADER between the mainline statements and its own STOP RUN
recreates the fall-through defect M6 closed. The family is appended
after the paragraph whose last statement is STOP RUN and before
END PROGRAM when one is present.

IDEMPOTENCE

  * the mainline paragraph BODY is replaced from a measured anchor,
  * suppression excludes the replaced region and the process
    paragraph, so a second run measures the same program,
  * the reader is rebuilt only while needs_rebuild() is true,
  * ProcessParagraphInjector is idempotent by its own M7 contract,
  * any paragraph carrying a generated name is DROPPED before the
    family is spliced, and the boundary is canonicalised.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

import inspect
from typing import Any, Iterable, Sequence

from converter.composers.restart.legacy_restart_cleanup import (
    LegacyRestartCleanup,
)
from converter.composers.restart.process_paragraph_injector import (
    ProcessParagraphInjector,
)
from converter.composers.restart.restart_injection_geometry import (  # noqa: F401
    END_PROGRAM,
    MAINLINE_LABEL,
    NON_PARAGRAPH_WORDS,
    SCOPE_REPORT_PREFIXES,
    SCOPE_TERMINATOR_WORDS,
    RestartParagraphGeometry,
    Span,
)
from converter.composers.restart.restart_storage_injector import (
    RestartStorageInjector,
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
from rules.restart_standard_rules import (
    NOT_APPLICABLE_REASONS,
    RESTART_DIAGNOSTICS,
    RESTART_PARAGRAPH_ROLES,
    ROLE_COMMIT,
    ROLE_CONTROL,
)

PROGRAM_KIND_RETRIEVAL = "retrieval"
PROGRAM_KIND_UPDATE = "update"

MESSAGE_PREFIX = "Restart injection:"

# Attributes a DCLGEN role may carry a restart-table token under. The
# attribute NAMES are schema; the VALUES are site vocabulary.
ROLE_TOKEN_ATTRIBUTES = (
    "table_name",
    "include_name",
    "host_record",
    "host_record_name",
)

# --- Applicability authority - see CORRECTION 5 ----------------------
# A resolved role is proof that restart applies. Set False only to
# reproduce the previous, circular text-scan behaviour for a baseline.
ROLE_ESTABLISHES_APPLICABILITY = True

# The fallback scan reads comment lines, because the checkpoint record
# is commented out before this composer runs.
SCAN_COMMENTS_FOR_RESTART_REFERENCE = True

SHARED_CLEANUP_METHODS = ("compose", "apply", "clean")

POSITIONAL_KINDS = (
    inspect.Parameter.POSITIONAL_ONLY,
    inspect.Parameter.POSITIONAL_OR_KEYWORD,
)

# Retained for callers and tests that imported the private name.
_Span = Span


class RestartInjectionComposer(RestartParagraphGeometry):
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

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 1. Classification  -- CORRECTION 5
    # -----------------------------------------------------------------
    def _not_applicable(self, lines: list[str], role: Any, kind: str) -> str:
        if str(kind or "").strip().lower() != PROGRAM_KIND_UPDATE:
            return NOT_APPLICABLE_REASONS["retrieval"]

        if role is None:
            return NOT_APPLICABLE_REASONS["dclgen_unresolved"]

        tokens = self._role_tokens(role)

        if tokens and ROLE_ESTABLISHES_APPLICABILITY:
            self._say(
                f"the restart role resolves {', '.join(tokens)}; "
                "restart control applies."
            )
            return ""

        if not tokens:
            self._say(
                "the restart role carries no restart-table token; "
                "falling back to a text scan."
            )

        if not self._references_restart_table(lines, role):
            return NOT_APPLICABLE_REASONS["no_restart_table"]

        return ""

    @staticmethod
    def _role_tokens(role: Any) -> list[str]:
        """Every restart-table token the role carries, upper-cased."""
        seen: list[str] = []
        for attribute in ROLE_TOKEN_ATTRIBUTES:
            token = str(getattr(role, attribute, "") or "").strip().upper()
            if token and token not in seen:
                seen.append(token)
        return seen

    def _references_restart_table(self, lines: list[str], role: Any) -> bool:
        """Fallback evidence: does the text mention the restart table?"""
        tokens = self._role_tokens(role)
        if not tokens:
            return False

        reader = (
            self._logical_any
            if SCAN_COMMENTS_FOR_RESTART_REFERENCE
            else self._logical
        )
        body = " ".join(reader(line) for line in lines)
        return any(token in body for token in tokens)

    # -----------------------------------------------------------------
    # 2 + 3. Config
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 4. Legacy cleanup
    # -----------------------------------------------------------------
    def _clean(self, lines: list[str], config: RestartConfig) -> list[str]:
        cleanup = LegacyRestartCleanup(config, self.line_utils)
        cleaned = list(cleanup.clean(list(lines)))
        self.messages.extend(getattr(cleanup, "messages", []) or [])
        removed = len(lines) - len(cleaned)
        if removed > 0:
            self._diagnostic("legacy_removed", count=removed)
        return cleaned

    # -----------------------------------------------------------------
    # 4b. Working storage
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 5. Mainline  -- CORRECTION 6 and CORRECTION 7
    # -----------------------------------------------------------------
    def _mainline(
        self,
        lines: list[str],
        config: RestartConfig,
        totals: Sequence[str],
    ) -> list[str]:
        """Replace the terminating paragraph's flow with the generated one.

        ORDER - the span is measured FIRST. The previous version built
        the body before locating the span, so the builder could not be
        told what the program already carries and the template was
        written whole, every time.
        """
        span = self._mainline_span(lines)
        if span is None:
            return lines

        start = self._replacement_start(lines, span, config)

        preserved = start - span.start
        if preserved > 0:
            self._say(
                f"{span.name}: preserved {preserved} initialisation "
                "line(s) ahead of the generated flow."
            )

        suppress_open, open_index = self._suppress_open(lines, start, span)
        suppress_read, read_index = self._suppress_prime_read(
            lines, start, span, config
        )

        if suppress_open:
            self._say(
                f"OPEN INPUT already present at line {open_index}, "
                "outside the replaced region; the template's OPEN is "
                "suppressed."
            )
        if suppress_read:
            self._say(
                f"the priming PERFORM {config.names.read_paragraph} is "
                f"already present at line {read_index}, outside the "
                "replaced region; the template's is suppressed."
            )

        builder = RestartMainFlowBuilder(config)
        body = builder.build(
            totals,
            suppress_open=suppress_open,
            suppress_prime_read=suppress_read,
        )
        self.messages.extend(builder.messages)
        if not body:
            return lines

        self._diagnostic(
            "control_injected", paragraph=config.paragraph(ROLE_CONTROL)
        )
        self._diagnostic(
            "commit_injected", paragraph=config.paragraph(ROLE_COMMIT)
        )
        self._diagnostic("stop_run_injected", paragraph=span.name)
        return lines[:start] + list(body) + lines[span.end :]

    def _mainline_span(self, lines: list[str]) -> Span | None:
        """The paragraph that TERMINATES the program. See CORRECTION 6."""
        index = self._termination_index(lines)
        if index < 0:
            self._say("no STOP RUN found; the mainline was left unchanged.")
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
        return Span(
            name=MAINLINE_LABEL, header=start, start=start + 1, end=end
        )

    def _replacement_start(
        self,
        lines: list[str],
        span: Span,
        config: RestartConfig,
    ) -> int:
        """Where the generated flow replaces the mainline body.

        The flow replaces from the first OPEN INPUT or the first
        PERFORM <process_paragraph>, WHICHEVER COMES FIRST. Everything
        above that is the program's own initialisation and is KEPT.

        Replacing from span.start deleted it, silently. Those MOVEs
        populate the run-date field the control paragraph uses as the
        checkpoint key, so every run read and wrote the checkpoint row
        for 00.00.0000 and the timestamp paragraph became something
        nothing performs.

        Falls back to span.start when the paragraph carries neither
        anchor, so a mainline shaped differently is replaced as before
        rather than half-repaired.
        """
        candidates = [
            index
            for index in (
                self._open_input_index_within(lines, span.start, span.end),
                self._perform_index_within(
                    lines,
                    span.start,
                    span.end,
                    config.names.process_paragraph,
                ),
            )
            if index >= 0
        ]
        return min(candidates) if candidates else span.start

    def _suppress_open(
        self,
        lines: list[str],
        start: int,
        span: Span,
    ) -> tuple[bool, int]:
        """Does the program already OPEN the file outside the region?

        No narrowing is needed: a second OPEN is always wrong, wherever
        it is. After a first run the generated OPEN sits INSIDE the
        replaced region, so this measurement is stable across runs.
        """
        index = self._open_input_index(lines)
        return (index >= 0 and not (start <= index < span.end)), index

    def _suppress_prime_read(
        self,
        lines: list[str],
        start: int,
        span: Span,
        config: RestartConfig,
    ) -> tuple[bool, int]:
        """Does an initialisation already prime the reader? CORRECTION 7.

        The loop tail inside the process paragraph is the SAME statement
        text and must not be mistaken for a priming read, so the process
        paragraph is excluded along with the region being replaced.
        """
        excluded: list[tuple[int, int]] = [(start, span.end)]

        process = self._span_named(lines, config.names.process_paragraph)
        if process is not None:
            excluded.append((process.header, process.end))

        index = self._statement_index_outside(
            lines,
            excluded,
            f"PERFORM {config.names.read_paragraph}.",
        )
        return index >= 0, index

    # -----------------------------------------------------------------
    # 6. Reader
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 7. Business paragraph
    # -----------------------------------------------------------------
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

    def _report_span(self, span: Span, body: list[str]) -> None:
        """Say what the repair pass was given, not what we assume."""
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

    # -----------------------------------------------------------------
    # 8. The restart family
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # 9. Shared retrieval cleanups
    # -----------------------------------------------------------------
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

    # -----------------------------------------------------------------
    # Reporting
    # -----------------------------------------------------------------
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
    "ROLE_ESTABLISHES_APPLICABILITY",
    "ROLE_TOKEN_ATTRIBUTES",
    "RestartInjectionComposer",
    "SCAN_COMMENTS_FOR_RESTART_REFERENCE",
    "SCOPE_REPORT_PREFIXES",
    "SCOPE_TERMINATOR_WORDS",
]
# LOCATION: converter/generators/restart/restart_flow_builder.py
# ACTION: CREATE NEW FILE
"""Builds the five restart flow paragraphs.

    control        - read the checkpoint and route on SQLCODE
    restart_found  - block a completed run, reposition a resumed one
    write_restart  - create the checkpoint on the first run of a date
    commit         - save the checkpoint and commit the unit of work
    abend          - call the site abend module

WHAT THIS MODULE FIXES

The previously generated 810-JOB-IS-RESTART did neither of its two jobs:

    IF CO-ID-RS = '1'
       THEN DISPLAY 'PREVIOUS RUN COMPLETE'
       CONTINUE                              <- should ABEND
    ELSE MOVE NB-READ TO WS-NB-INPUT-REC     <- no repositioning
    END-IF.

So a completed run was allowed to run again, updating every row twice,
and a rerun reprocessed from record 1. Both obligations are carried by
RESTART_FOUND_TEMPLATE and asserted by the M5 tests.

IT RENDERS, IT DOES NOT DECIDE

Every line comes from rules/restart_statement_templates.py, filled from
RestartConfig.placeholders(). This class owns no COBOL text of its own.
That is why the retention value and the payload length reach the output
correctly: they are properties of the config, measured or supplied, and
this builder cannot override them.

REFUSAL

A config that is not usable - an unresolved name, an unmeasured payload,
a role with no retention - produces NO paragraphs and one message per
missing entry. Half a restart family is worse than none: the mainline
would perform paragraphs that were never written.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_paragraph import RestartParagraph
from rules.restart_sql_templates import DEBUG_TRACE
from rules.restart_standard_rules import (
    ROLE_ABEND,
    ROLE_COMMIT,
    ROLE_CONTROL,
    ROLE_RESTART_FOUND,
    ROLE_WRITE_RESTART,
)
from rules.restart_statement_templates import (
    ABEND_TEMPLATE,
    COMMIT_TEMPLATE,
    CONTROL_TEMPLATE,
    RESTART_FOUND_TEMPLATE,
    WRITE_RESTART_TEMPLATE,
)

# Role -> template. Order is the order the paragraphs are emitted in.
FLOW_TEMPLATES = (
    (ROLE_CONTROL, CONTROL_TEMPLATE),
    (ROLE_RESTART_FOUND, RESTART_FOUND_TEMPLATE),
    (ROLE_WRITE_RESTART, WRITE_RESTART_TEMPLATE),
    (ROLE_COMMIT, COMMIT_TEMPLATE),
    (ROLE_ABEND, ABEND_TEMPLATE),
)

SENTENCE_TERMINATOR = "."


class RestartFlowBuilder:
    """Renders control / restart_found / write_restart / commit / abend."""

    def __init__(self, config: RestartConfig) -> None:
        self.config = config
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def build_all(self) -> list[RestartParagraph]:
        self.messages = []

        if not self._usable():
            return []

        values = self.config.placeholders()
        paragraphs = [
            self._paragraph(role, template, values)
            for role, template in FLOW_TEMPLATES
        ]
        self.messages.append(
            f"Restart flow: generated {len(paragraphs)} paragraph(s)."
        )
        return paragraphs

    def build(self, role: str) -> RestartParagraph | None:
        """One paragraph by role, or None when the config is unusable."""
        for candidate in self.build_all():
            if candidate.role == role:
                return candidate
        return None

    # -----------------------------------------------------------------
    # Gate
    # -----------------------------------------------------------------

    def _usable(self) -> bool:
        if self.config.is_usable():
            return True

        for name in self.config.missing():
            self.messages.append(
                f"Restart flow: {name} unresolved; no paragraph written."
            )
        if self.config.retention_days <= 0:
            self.messages.append(
                "Restart flow: the restart role carries no retention "
                "value; no paragraph written."
            )
        return False

    # -----------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------

    def _paragraph(
        self,
        role: str,
        template: tuple[str, ...],
        values: dict[str, object],
    ) -> RestartParagraph:
        rendered = [line.format(**values) for line in template]
        name = self._header_name(rendered[0], role)
        body = self._terminated(rendered[1:])

        return RestartParagraph(
            role=role,
            name=name,
            debug_trace=DEBUG_TRACE.format(paragraph=name),
            body=tuple(body),
        )

    def _header_name(self, header: str, role: str) -> str:
        """The paragraph name the template rendered, minus its period."""
        name = header.strip().rstrip(SENTENCE_TERMINATOR)
        expected = self.config.paragraph(role)
        if name != expected:
            self.messages.append(
                f"Restart flow: template header '{name}' does not match "
                f"the configured name '{expected}'; used the template."
            )
        return name

    def _terminated(self, body: list[str]) -> list[str]:
        """Guarantee the paragraph closes its sentence.

        A paragraph left ending on a bare scope terminator runs into the
        next paragraph header and the compiler rejects the program.
        """
        executable = [index for index, line in enumerate(body) if line.strip()]
        if not executable:
            return body

        last = executable[-1]
        if body[last].rstrip().endswith(SENTENCE_TERMINATOR):
            return body

        updated = list(body)
        updated.insert(last + 1, SENTENCE_TERMINATOR)
        self.messages.append(
            "Restart flow: added the missing sentence terminator."
        )
        return updated


__all__ = ["FLOW_TEMPLATES", "RestartFlowBuilder"]
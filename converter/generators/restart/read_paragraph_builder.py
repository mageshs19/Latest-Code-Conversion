# LOCATION: converter/generators/restart/read_paragraph_builder.py
# ACTION: CREATE NEW FILE
"""Builds the reader paragraph that feeds the checkpoint.

    <reader>.
        INITIALIZE <record>.

        READ <file> INTO <record>
             AT END SET <eof> TO TRUE.

        IF <not eof>
        THEN
             ADD +1 TO <commit counter>
             ADD +1 TO <input counter>
             MOVE <record> TO <input save area>
        END-IF.

WHY EACH STATEMENT EXISTS

    INITIALIZE   a short record leaves the tail of the previous one in
                 place, so a field the input did not supply is read as
                 the value from the record before it.

    ADD commit   drives the every-hundred commit test. Without it the
                 test never fires and the checkpoint is written once, at
                 end of file.

    ADD input    becomes NB-READ. Without it the checkpoint says zero
                 records were read and every restart resumes from one.

    MOVE save    becomes KY-RESTART. Without it the saved key is blank
                 and an operator cannot see where the job stopped.

The generated reader carried none of the four:

        READ OPERATIES INTO VMDZ205I
           AT END MOVE 'Y' TO SW-EOF.

It also set the switch by literal rather than through its 88-level, so
the driving loop had to compare a literal too.

NOT A RESTART-FAMILY PARAGRAPH

The reader belongs to the PROGRAM, not to the restart family: it has no
scheme number, no catalog suffix, and its name is resolved from the
source. That is why ROLE_READ lives here and not in
RESTART_PARAGRAPH_ROLES - adding it there would require every numbering
scheme to invent a number for a paragraph the site already named.

No program, paragraph, record, table, DCLGEN, cursor or host variable
name is hardcoded.
"""

from __future__ import annotations

from converter.generators.restart.restart_config import RestartConfig
from converter.generators.restart.restart_paragraph import RestartParagraph
from rules.restart_sql_templates import DEBUG_TRACE
from rules.restart_statement_templates import READ_PARAGRAPH_TEMPLATE

ROLE_READ = "read"
PERIOD = "."


class RestartReadParagraphBuilder:
    """Renders the reader paragraph, and reports what a source one lacks."""

    def __init__(self, config: RestartConfig) -> None:
        self.config = config
        self.messages: list[str] = []

    # -----------------------------------------------------------------
    # Public surface
    # -----------------------------------------------------------------

    def build(self) -> RestartParagraph | None:
        """The reader paragraph, or None when the config is unusable."""
        self.messages = []

        if not self._usable():
            return None

        values = self.config.placeholders()
        rendered = [line.format(**values) for line in READ_PARAGRAPH_TEMPLATE]
        name = rendered[0].strip().rstrip(PERIOD)

        self.messages.append(
            f"Read paragraph: rendered {name} with the four checkpoint "
            "statements."
        )
        return RestartParagraph(
            role=ROLE_READ,
            name=name,
            debug_trace=DEBUG_TRACE.format(paragraph=name),
            body=tuple(rendered[1:]),
        )

    def required_statements(self) -> tuple[str, ...]:
        """The four statements a source reader must carry."""
        names = self.config.names
        return (
            f"INITIALIZE {names.record_name}",
            f"ADD +1 TO {names.commit_counter}",
            f"ADD +1 TO {names.input_counter}",
            f"MOVE {names.record_name} TO {names.input_save_area}",
        )

    def missing_statements(self, lines: list[str]) -> tuple[str, ...]:
        """Which required statements a source reader does not carry."""
        body = " ".join(self._logical(line) for line in lines or [])
        return tuple(
            statement
            for statement in self.required_statements()
            if self._logical(statement) not in body
        )

    def needs_rebuild(self, lines: list[str]) -> bool:
        """True when the source reader is missing anything required."""
        missing = self.missing_statements(lines)
        for statement in missing:
            self.messages.append(
                f"Read paragraph: source reader lacks '{statement}'."
            )
        return bool(missing)

    # -----------------------------------------------------------------
    # Gate
    # -----------------------------------------------------------------

    def _usable(self) -> bool:
        if self.config.is_usable():
            return True

        for name in self.config.missing():
            self.messages.append(
                f"Read paragraph: {name} unresolved; nothing rendered."
            )
        if self.config.retention_days <= 0:
            self.messages.append(
                "Read paragraph: the restart role carries no retention "
                "value; nothing rendered."
            )
        return False

    # -----------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------

    @staticmethod
    def _logical(line: str) -> str:
        return " ".join(str(line or "").upper().split())


__all__ = ["ROLE_READ", "RestartReadParagraphBuilder"]
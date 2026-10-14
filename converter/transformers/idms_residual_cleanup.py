# LOCATION: converter/transformers/idms_residual_cleanup.py
# ACTION: REPLACE ENTIRE FILE
"""Removes residual IDMS lines the main converters leave behind.

THREE CONCERNS, ONE OWNER

    declarative / control   SCHEMA SECTION, PROTOCOL, COPY IDMS ...
    executable              BIND, FINISH, FIND CURRENT ...
    orphaned references     what COPY IDMS removal leaves undefined

CORRECTION 1 - the orphaned-reference detector had no consumer
----------------------------------------------------------------
``COPY_IDMS_PATTERN`` removes EVERY COPY IDMS member, including
SUBSCHEMA-LR-CTRL, which DECLARES LR-STATUS, ERROR-STATUS and
DML-SEQUENCE. The declarations went; the references did not:

    DISPLAY 'NR-ST:' NR-ST-FORM-AS OF VMDZ205I
           ' NS-DB:' NS-DB-STOCK-FORM-AS OF VMDZ205I
           ' LR-STATUS:' LR-STATUS            <- undefined data name

``REMOVED_COPYBOOK_FIELD_PATTERN`` was written for exactly this and was
never called, so CHK-29.01 could not pass. It is wired here.

CORRECTION 2 - ERROR-STATUS has an owner, and it is not this pass
-------------------------------------------------------------------
``MOVE <value> TO ERROR-STATUS`` is NOT an orphaned reference. It is the
INPUT to a four-pass chain in CobolCleanupComposer:

    replace_error_status_with_flag      -> MOVE 'Y' TO SW-STATUS-D
    ensure_sw_status_d_declaration      -> 10 SW-STATUS-D PIC X VALUE 'N'
    ensure_child_fetch_early_stop       -> UNTIL <eoc> OR
                                               SW-STATUS-D = 'Y'
    move_output_write_after_child_loop  -> IF NOT SW-STATUS-D = 'Y'

This transformer runs FIRST. Commenting the statement here starves all
four: they match nothing, change nothing and report nothing, and the
program silently loses its deletion-event handling.

Measured on VMDZ4420: five working statements vanished from a program
the COBOL team had already signed off, and the child cursor stopped
exiting early. Nothing had been deleted from the codebase - the chain
had simply been robbed of its input.

LR-STATUS and DML-SEQUENCE have no such owner and are still handled
here. Only this one statement form is handed back, and the hand-back is
reported so the decision is visible in the run log.

WHY THE FORM MATTERS - and why the whole statement is not commented
---------------------------------------------------------------------
In the block above, lines 1 and 2 carry LIVE DCLGEN fields. Commenting
the whole DISPLAY would delete two working abend diagnostics to remove
one dead operand. The dead field occupies its OWN continuation line, so
that line alone is replaced.

DISPLAY_STATEMENT_PATTERN and MOVE_TO_STATEMENT_PATTERN decide which
rule applies. Without them the verb itself counts as a live operand and
a wholly dead DISPLAY is refused:

    DISPLAY '##&&LR-STATUS : ', LR-STATUS.
      -> strip literal, strip field, strip punctuation -> "DISPLAY"
      -> non-empty -> refused, wrongly

EVERY DECISION IS REPORTED
----------------------------
A removal, a refusal and a hand-back all append a message. A pass that
silently deletes generated output cannot be reviewed, and CHK-29.05 asks
for the replacement to be documented in the program itself.

No program, record, table, DCLGEN, cursor or host variable name is
hardcoded. Regex lives in patterns/, message text in rules/.
"""

from __future__ import annotations

import re

from patterns.cobol_cleanup_patterns import ERROR_STATUS_MOVE_PATTERN
from patterns.cobol_transformer_patterns import (
    BIND_STATEMENT_PATTERN,
    EXIT_LINE_PATTERN,
    FIND_CURRENT_STATEMENT_PATTERN,
    FINISH_STATEMENT_PATTERN,
    IDMS_ABORT_PARAGRAPH_PATTERN,
    IDMS_DECLARATIVE_PATTERNS,
    IDMS_EXECUTABLE_PATTERNS,
)
from patterns.idms_patterns import (
    DISPLAY_STATEMENT_PATTERN,
    MOVE_TO_STATEMENT_PATTERN,
    REMOVED_COPYBOOK_FIELD_PATTERN,
)
from rules.idms_transformer_messages import (
    ERROR_STATUS_MOVE_OWNED_ELSEWHERE,
    REMOVED_FIELD_LINE_TEMPLATE,
    REMOVED_FIELD_REFUSED_TEMPLATE,
)


# A quoted COBOL literal. Removed BEFORE the field scan so a label such
# as ' LR-STATUS:' is never mistaken for a reference to the field.
_LITERAL_PATTERN = re.compile(r"'[^']*'")

# Punctuation that carries no operand.
_PUNCTUATION = ",."

# Leading verbs stripped when the matching form pattern fired, so the
# verb itself is not counted as a surviving live operand.
_DISPLAY_VERB_PATTERN = re.compile(r"^\s*DISPLAY\b", flags=re.IGNORECASE)


class IdmsResidualCleanup:
    """Detects and removes residual IDMS lines.

    Conservative by design: a removed executable statement inside
    PROCEDURE DIVISION is replaced by CONTINUE so the business flow
    keeps a statement where one is required.
    """

    def __init__(self) -> None:
        self.messages: list[str] = []

    def reset(self) -> None:
        """Drop diagnostics from the previous program.

        One instance is reused across a batch run, so without this the
        second program inherits the first program's messages.
        """
        self.messages = []

    # =================================================================
    # Declarative and control lines
    # =================================================================
    def is_idms_declarative_or_control(
        self,
        logical_line: str,
    ) -> bool:
        statement = str(logical_line or "").strip().rstrip(".")

        for pattern in IDMS_DECLARATIVE_PATTERNS:
            if pattern.search(statement):
                return True

        return False

    def removed_declarative_lines(
        self,
        logical_line: str,
    ) -> list[str]:
        return [
            f"* DB2: Removed residual IDMS control statement: "
            f"{logical_line}",
        ]

    # =================================================================
    # Executable statements
    # =================================================================
    def is_idms_executable_cleanup(
        self,
        logical_line: str,
    ) -> bool:
        statement = str(logical_line or "").strip().rstrip(".")

        for pattern in IDMS_EXECUTABLE_PATTERNS:
            if pattern.search(statement):
                return True

        return False

    def removed_executable_lines(
        self,
        *,
        logical_line: str,
        current_division: str,
    ) -> list[str]:
        statement = str(logical_line or "").strip()

        if FINISH_STATEMENT_PATTERN.search(statement):
            if current_division == "PROCEDURE":
                return [
                    "* DB2: IDMS FINISH converted to COMMIT.",
                    "MOVE 'COMMIT' TO SQL-LOCATION.",
                    "EXEC SQL",
                    "    COMMIT",
                    "END-EXEC.",
                ]

            return [
                f"* DB2: Removed IDMS FINISH outside PROCEDURE "
                f"DIVISION: {statement}",
            ]

        if BIND_STATEMENT_PATTERN.search(statement):
            return self.procedure_safe_removal(
                message=(
                    f"* DB2: Removed IDMS BIND statement: {statement}"
                ),
                current_division=current_division,
            )

        if FIND_CURRENT_STATEMENT_PATTERN.search(statement):
            return self.procedure_safe_removal(
                message=(
                    f"* DB2: Removed IDMS FIND CURRENT statement: "
                    f"{statement}"
                ),
                current_division=current_division,
            )

        return self.procedure_safe_removal(
            message=(
                f"* DB2: Removed residual IDMS executable statement: "
                f"{statement}"
            ),
            current_division=current_division,
        )

    def procedure_safe_removal(
        self,
        *,
        message: str,
        current_division: str,
    ) -> list[str]:
        if current_division == "PROCEDURE":
            return [
                message,
                "CONTINUE.",
            ]

        return [
            message,
        ]

    # =================================================================
    # Paragraph and line shapes
    # =================================================================
    def is_idms_abort_paragraph(
        self,
        logical_line: str,
    ) -> bool:
        statement = str(logical_line or "").strip()

        return bool(IDMS_ABORT_PARAGRAPH_PATTERN.match(statement))

    def is_exit_line(
        self,
        logical_line: str,
    ) -> bool:
        statement = str(logical_line or "").strip()

        return bool(EXIT_LINE_PATTERN.match(statement))

    # =================================================================
    # Orphaned copybook-field references
    # =================================================================
    def references_removed_field(
        self,
        logical_line: str,
    ) -> bool:
        """True when this line names a field whose copybook was removed.

        Literals are stripped first: ``' LR-STATUS:'`` is a label, not
        a reference, and a line carrying only the label is live.

        This is the GATE. A caller asks here before calling
        ``removed_field_lines``, so a statement refused here is never
        touched at all. See CORRECTION 2 in the module docstring: the
        ERROR-STATUS MOVE belongs to CobolCleanupComposer and is handed
        back before any field scan runs.
        """
        statement = str(logical_line or "")
        if not statement.strip():
            return False

        if self._owned_by_cleanup_composer(statement):
            self.messages.append(ERROR_STATUS_MOVE_OWNED_ELSEWHERE)
            return False

        without_literals = _LITERAL_PATTERN.sub("", statement)

        return bool(
            REMOVED_COPYBOOK_FIELD_PATTERN.search(without_literals)
        )

    def removed_field_lines(
        self,
        logical_line: str,
    ) -> list[str]:
        """Comment the line, or refuse and say why.

        SAFE - the dead field is the only operand on the line, so the
        line can be replaced by a comment. Two shapes qualify:

            a whole DISPLAY whose only data name is dead
            a DISPLAY continuation carrying only a label and the field

        REFUSAL - the line also carries a LIVE data name. Removing it
        would delete a working diagnostic, so the line is kept and the
        decision is reported above it.

        A MOVE touching a dead field cannot compile either way, so it
        is always commented and always reported - unless another pass
        owns it, which is tested first.
        """
        statement = str(logical_line or "").strip()
        if not statement:
            return [statement]

        # The gate above already refuses this form. Repeated here so a
        # caller that reaches this method directly cannot bypass the
        # owner. ONE predicate, two call sites.
        if self._owned_by_cleanup_composer(statement):
            return [statement]

        without_literals = _LITERAL_PATTERN.sub("", statement)
        match = REMOVED_COPYBOOK_FIELD_PATTERN.search(without_literals)

        if not match:
            return [statement]

        field = match.group("field").upper()

        # A MOVE naming a dead field is dead whichever side it sits on.
        if MOVE_TO_STATEMENT_PATTERN.match(statement):
            self.messages.append(
                f"Cleanup: commented MOVE naming {field}; its declaring "
                f"copybook was removed by the IDMS conversion."
            )
            return [
                REMOVED_FIELD_LINE_TEMPLATE.format(
                    field=field,
                    line=statement,
                )
            ]

        if self._only_dead_operands(statement):
            self.messages.append(
                f"Cleanup: removed orphaned {field} reference; its "
                f"declaring copybook was removed by the IDMS conversion."
            )
            return [
                REMOVED_FIELD_LINE_TEMPLATE.format(
                    field=field,
                    line=statement,
                )
            ]

        self.messages.append(
            f"Cleanup: {field} is undefined after copybook removal but "
            f"shares a line with live operands; left unchanged for "
            f"manual review."
        )
        return [
            REMOVED_FIELD_REFUSED_TEMPLATE.format(field=field),
            statement,
        ]

    # =================================================================
    # Helpers
    # =================================================================
    @staticmethod
    def _owned_by_cleanup_composer(statement: str) -> bool:
        """True when another pass owns this statement outright.

        ERROR_STATUS_MOVE_PATTERN is the SAME constant
        CobolCleanupComposer matches on, so the two passes cannot
        disagree about which line belongs to whom. Adding a second
        pattern here would recreate the defect this guard exists to
        close.
        """
        return bool(
            ERROR_STATUS_MOVE_PATTERN.match(str(statement or "").strip())
        )

    def _only_dead_operands(
        self,
        statement: str,
    ) -> bool:
        """True when nothing live survives the strip.

        Order is load-bearing:

            1. literals   - a label is not a reference
            2. the verb   - DISPLAY is not an operand
            3. dead fields
            4. punctuation

        Removing the verb BEFORE the emptiness test is what lets a
        wholly dead single-line DISPLAY be commented rather than
        refused.
        """
        residue = _LITERAL_PATTERN.sub("", str(statement or ""))

        if DISPLAY_STATEMENT_PATTERN.match(statement):
            residue = _DISPLAY_VERB_PATTERN.sub("", residue, count=1)

        residue = REMOVED_COPYBOOK_FIELD_PATTERN.sub("", residue)

        for character in _PUNCTUATION:
            residue = residue.replace(character, "")

        return not residue.strip()


__all__ = [
    "IdmsResidualCleanup",
]
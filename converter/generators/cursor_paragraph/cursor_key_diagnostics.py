# LOCATION: converter/generators/cursor_paragraph/cursor_key_diagnostics.py
# ACTION: CREATE NEW FILE
"""DISPLAY lines that identify the failing row in a FETCH error branch.

MANUAL REFERENCE

    820-FETCH, the CHILD cursor:

        WHEN OTHER
             DISPLAY 'ERROR WHILE FETCHING CURSOR DZEVEFC1'
             DISPLAY 'NR-DB-STOCK = ' NS-DBSTK-479BEFF
                                      OF DCLDZBEFFTV

    720-FETCH, the PARENT cursor:

        WHEN OTHER
             DISPLAY 'ERROR WHILE FETCHING CURSOR DZBEFFC1'

    Cursor name only. The parent has no driving key to report - it is
    the driver.

CORRECTION - the WHERE path emitted an UNQUALIFIED host.

_where_clause_diagnostic_lines() built its own one-line DISPLAY and
argued that 'CT-RKTPROD-479BEFF OF DCLDZBEFFTV' is too wide, so the
bare name must be used. Both halves of that are wrong:

  1. A foreign-key column keeps the PARENT's column name, so
     CT-RKTPROD-479BEFF is declared in BOTH DCLDZBEFFTV and
     DCLDZEVEFTV. The bare name is NOT UNIQUE and the program does not
     compile. The manual reference wraps 'OF DCLDZBEFFTV' onto a
     continuation line for exactly this reason.

  2. "Too wide for one line" is not a reason to drop the qualifier.
     one_diagnostic() beside it already escalates 1 -> 2 -> 3 lines and
     skips only when nothing fits.

The WHERE path now routes through one_diagnostic(). There is ONE
DISPLAY renderer, so the two paths cannot diverge again.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph import cursor_host_reference as hosts
from converter.generators.cursor_paragraph.cursor_line_geometry import (
    continuation,
    fits,
)
from rules.cursor_paragraph_rules import (
    EMIT_FETCH_KEY_DIAGNOSTICS,
    FETCH_KEY_DIAGNOSTIC_LIMIT,
    FETCH_KEY_DISPLAY_TEMPLATE,
    FETCH_KEY_HOST_TEMPLATE,
    FETCH_KEY_LABEL_WIDTH,
    IND_WHEN_BODY,
)

OF_TEMPLATE = "OF {group}"


class KeyDiagnosticsBuilder:
    """Renders the row-identity DISPLAY lines of a FETCH error branch."""

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------
    def lines_for_where(self, where_conditions: list[str] | None) -> list[str]:
        """Report the RUNTIME VALUE of each driving-key host.

        The predicate text itself is already in the source; what the
        operator needs is the value the cursor was driven with.
        """
        if not EMIT_FETCH_KEY_DIAGNOSTICS or not where_conditions:
            return []

        references = [
            hosts.from_where_condition(condition)
            for condition in where_conditions[:FETCH_KEY_DIAGNOSTIC_LIMIT]
        ]
        return self._render(references)

    def lines_for_hosts(self, host_variables: list[str] | None) -> list[str]:
        """Legacy path: report the leading FETCHED columns."""
        if not EMIT_FETCH_KEY_DIAGNOSTICS:
            return []

        references = hosts.qualified_pairs(host_variables)
        return self._render(references[:FETCH_KEY_DIAGNOSTIC_LIMIT])

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, references) -> list[str]:
        lines: list[str] = []
        for reference in references:
            if not reference.is_qualified:
                # Never guess a group. An unqualified operand is a
                # not-unique data-name, so the line is dropped.
                continue
            lines.extend(self.one_diagnostic(reference.field, reference.group))
        return lines

    @staticmethod
    def one_diagnostic(field: str, group: str) -> list[str]:
        """One DISPLAY, wrapped as many times as the window demands.

        IND_WHEN_BODY(11) + "DISPLAY '"(9) + label(18) + "' = ' "(5)
        costs 43 columns, leaving 22 for the operand. A COBOL data-name
        may be 30 characters, so even the field ALONE can overflow.

        Escalation, in order:
            1. literal + field + OF group   on one line
            2. literal + field / OF group   on two lines
            3. literal / field / OF group   on three lines
            4. none of the above fits       -> emit nothing

        Step 4 is deliberate. A truncated data-name does not compile;
        losing one diagnostic line does no harm.
        """
        if not field or not group:
            return []

        label = field[:FETCH_KEY_LABEL_WIDTH].ljust(FETCH_KEY_LABEL_WIDTH)
        qualified = FETCH_KEY_HOST_TEMPLATE.format(field=field, group=group)

        single = IND_WHEN_BODY + FETCH_KEY_DISPLAY_TEMPLATE.format(
            label=label,
            host=qualified,
        )
        if fits(single):
            return [single]

        of_group = continuation(OF_TEMPLATE.format(group=group))
        if not of_group:
            return []

        head = IND_WHEN_BODY + FETCH_KEY_DISPLAY_TEMPLATE.format(
            label=label,
            host=field,
        )
        if fits(head):
            return [head, of_group]

        literal = (
            IND_WHEN_BODY
            + FETCH_KEY_DISPLAY_TEMPLATE.format(label=label, host="").rstrip()
        )
        field_line = continuation(field)

        if fits(literal) and field_line:
            return [literal, field_line, of_group]

        return []


__all__ = ["KeyDiagnosticsBuilder"]
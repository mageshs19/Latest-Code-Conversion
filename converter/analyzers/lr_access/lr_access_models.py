# LOCATION: converter/analyzers/lr_access/lr_access_models.py
# ACTION: CREATE NEW FILE
"""One classified LR access site. Data only - no parsing, no rendering.

PAIRING IS BY (RECORD, SET), NOT BY PROXIMITY
----------------------------------------------
VMDZ7200 puts the OBTAIN FIRST at line 181, the loop header at 139 and
the OBTAIN NEXT at 207 - three different paragraphs, with the loop
BEFORE the access it drives. VMDZ4302 interleaves two nested loops whose
FIRST/NEXT pairs are 26 and 52 lines apart.

A line span therefore cannot identify a site. The identity is the
(record, set) pair, and the line numbers are evidence recorded against
it, not the thing that defines it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rules.lr_access_rules import (
    KIND_BOUNDED_SEARCH,
    KIND_DEFAULT,
    KIND_FIRST_ONLY,
    KIND_KEYED_READ,
    LOOP_NONE,
)


@dataclass
class LrAccessSite:
    """One LR access and the shape the renderer must produce."""

    # ---- identity
    record_name: str = ""          # COBOL form
    within_name: str = ""          # COBOL form; "" for a keyed read

    # ---- classification
    kind: str = KIND_DEFAULT
    loop_form: str = LOOP_NONE

    # ---- evidence, for the log and for the loop-removal pass
    first_line: int = 0            # the OBTAIN FIRST / OBTAIN CALC
    next_line: int = 0             # the OBTAIN NEXT, 0 when none
    loop_header_line: int = 0      # the PERFORM
    loop_end_line: int = 0         # END-PERFORM, 0 for paragraph forms
    loop_condition: str = ""       # JOINED, never one physical line

    # ---- SQL inputs
    table_name: str = ""
    key_columns: list[str] = field(default_factory=list)

    # Loop terms that are NOT end-of-set tests. Folded into the WHERE.
    bound_predicates: list[str] = field(default_factory=list)

    # Filters the LR statement carried beyond the path keyword. The
    # expander already parses these and writes them into a comment
    # saying "add to the generated cursor WHERE" - a note to a human
    # that nothing consumed. VMDZ1526 carries two.
    extra_filters: list[str] = field(default_factory=list)

    order_by: list[str] = field(default_factory=list)

    # ---- P5
    not_found_literals: set[str] = field(default_factory=set)
    end_of_set_literals: set[str] = field(default_factory=set)

    diagnostics: list[str] = field(default_factory=list)

    @property
    def key(self) -> tuple[str, str]:
        return (self.record_name, self.within_name)

    @property
    def is_singleton(self) -> bool:
        """Renders as one SELECT rather than a cursor."""
        return self.kind in (
            KIND_KEYED_READ,
            KIND_FIRST_ONLY,
            KIND_BOUNDED_SEARCH,
        )

    @property
    def removes_loop(self) -> bool:
        """The driving loop has no work left once this is a singleton.

        Only an INLINE loop is removable by this model: a paragraph or
        THRU loop drives business code as well as the access, and
        deleting it would delete that work. Those sites keep their loop
        and must not be rendered as singletons until a pass exists that
        can separate the two.
        """
        return (
            self.kind == KIND_BOUNDED_SEARCH
            and self.loop_end_line > self.loop_header_line > 0
        )

    @property
    def where_predicates(self) -> list[str]:
        return list(self.bound_predicates) + list(self.extra_filters)


__all__ = ["LrAccessSite"]
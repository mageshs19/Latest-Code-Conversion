# LOCATION: converter/generators/cursor_paragraph/cursor_host_reference.py
# ACTION: CREATE NEW FILE
"""Parses a DB2 host reference into its DCLGEN group and field.

ONE parser, three accepted spellings, because the resolver may deliver
any of them:

    :DCLDZBEFFTV.CT-RKTPROD-479BEFF
    DCLDZBEFFTV.CT-RKTPROD-479BEFF
    CT-RKTPROD-479BEFF OF DCLDZBEFFTV

CORRECTION - the WHERE path had its OWN parser.

_where_host_field() returned the FIELD ONLY and discarded the group,
which is how an unqualified DISPLAY reached the generated program. A
foreign-key column keeps the PARENT's column name, so the same
data-name is declared in BOTH DCLGEN groups and an unqualified
reference is NOT UNIQUE - the compiler rejects it. The group is never
discarded now.
"""

from __future__ import annotations

from dataclasses import dataclass

from rules.cursor_paragraph_rules import (
    HOST_GROUP_SEPARATOR,
    HOST_REFERENCE_PREFIX,
)

OF_KEYWORD = " OF "
PREDICATE_SEPARATOR = "="


@dataclass(frozen=True)
class HostReference:
    """One DCLGEN host field and the group that owns it."""

    field: str = ""
    group: str = ""

    @property
    def is_qualified(self) -> bool:
        return bool(self.field and self.group)


def parse(reference: str) -> HostReference:
    """Split any accepted host spelling. Unqualified yields group ""."""
    text = str(reference or "").strip()
    if text.startswith(HOST_REFERENCE_PREFIX):
        text = text[len(HOST_REFERENCE_PREFIX):].strip()
    if not text:
        return HostReference()

    upper = text.upper()

    if OF_KEYWORD in upper:
        cut = upper.rindex(OF_KEYWORD)
        return HostReference(
            field=text[:cut].strip().upper(),
            group=text[cut + len(OF_KEYWORD):].strip().upper(),
        )

    if HOST_GROUP_SEPARATOR in text:
        group, _sep, field = text.partition(HOST_GROUP_SEPARATOR)
        return HostReference(
            field=field.strip().upper(),
            group=group.strip().upper(),
        )

    return HostReference(field=text.upper())


def from_where_condition(condition: str) -> HostReference:
    """The host named on the RIGHT of one WHERE predicate.

        CT_RKTPROD_479BEFF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Anything without a separator returns an empty reference and the
    caller drops the line rather than guessing at a name.
    """
    text = str(condition or "").strip()
    if PREDICATE_SEPARATOR not in text:
        return HostReference()
    return parse(text.split(PREDICATE_SEPARATOR, 1)[1])


def group_of(host_variables: list[str] | None) -> str:
    """The DCLGEN group owning a FETCH INTO list, or ""."""
    for host in host_variables or []:
        reference = parse(host)
        if reference.group:
            return reference.group
    return ""


def qualified_pairs(host_variables: list[str] | None) -> list[HostReference]:
    """Every QUALIFIED host in a list. Unqualified entries are skipped."""
    return [
        reference
        for reference in (parse(host) for host in (host_variables or []))
        if reference.is_qualified
    ]


__all__ = [
    "HostReference",
    "parse",
    "from_where_condition",
    "group_of",
    "qualified_pairs",
]
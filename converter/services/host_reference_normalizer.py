"""SQL host reference -> COBOL qualified reference. ONE owner.

    :DCLDZBFARTV.NR-IDFMAS-479BFAR  ->  NR-IDFMAS-479BFAR OF DCLDZBFARTV

WHY THIS MODULE EXISTS

The conversion was implemented twice. RecordHostResolver.normalize
declared its own GROUP_SEPARATOR = "." and was correct.
FieldReferenceHostResolver imported HOST_GROUP_SEPARATOR from
rules/field_reference_rewriter_rules.py, where the SAME NAME carries a
DIFFERENT VALUE - " OF " - because two other rules modules declare it
as ".".

The test therefore asked "does this reference already contain ' OF '",
the answer was always no, the branch never ran, and the raw SQL dot
form was emitted into COBOL:

    MOVE DA-DD-MM-CCYY TO DCLDZBFARTV.DA-INFSDGD-479BFAR

which the compiler reads as a sentence terminator. The replacement
engine then appended ' OF DCLDZBFARTV' on top, so one statement carried
both conventions and overflowed column 72.

The separator is a FACT about the input format, not a site preference.
It has one value and one owner.
"""

from __future__ import annotations

HOST_PREFIX = ":"
SQL_GROUP_SEPARATOR = "."
COBOL_QUALIFIER_TEMPLATE = "{host} OF {group}"


class HostReferenceNormalizer:
    """Total: an unparsable reference yields '', never an exception."""

    @staticmethod
    def to_cobol(reference) -> str:
        text = str(reference or "").strip().lstrip(HOST_PREFIX)
        if not text:
            return ""

        if SQL_GROUP_SEPARATOR in text:
            group, _sep, host = text.partition(SQL_GROUP_SEPARATOR)
            host = host.strip().upper()
            group = group.strip().upper()
            if not host or not group:
                return text.upper()
            return COBOL_QUALIFIER_TEMPLATE.format(host=host, group=group)

        return text.upper()

    @staticmethod
    def is_sql_form(reference) -> bool:
        text = str(reference or "").strip().lstrip(HOST_PREFIX)
        return SQL_GROUP_SEPARATOR in text


__all__ = [
    "COBOL_QUALIFIER_TEMPLATE",
    "HOST_PREFIX",
    "SQL_GROUP_SEPARATOR",
    "HostReferenceNormalizer",
]
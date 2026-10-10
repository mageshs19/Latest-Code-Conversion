# LOCATION: converter/resolvers/business_paragraph_resolver.py
# ACTION: CREATE NEW FILE
"""Resolves the business paragraph a cursor's row logic lives in.

Anchors are derived from the CONVERSION MARKER TEMPLATES themselves, so
no marker text is duplicated here. Adding or rewording a template in
rules/idms_transformer_messages.py automatically updates this resolver.
"""

from __future__ import annotations

from rules.idms_transformer_messages import (
    CONVERTED_FIND_FIRST_TEMPLATE,
    CONVERTED_OBTAIN_FIRST_TEMPLATE,
    CONVERTED_OBTAIN_NEXT_TEMPLATE,
)

#: Templates whose presence in a paragraph marks it as row-level logic.
NAVIGATION_MARKER_TEMPLATES = (
    CONVERTED_OBTAIN_NEXT_TEMPLATE,
    CONVERTED_OBTAIN_FIRST_TEMPLATE,
    CONVERTED_FIND_FIRST_TEMPLATE,
)


def marker_prefix(template: str) -> str:
    """The literal head of a template, up to its first placeholder.

    'CONVERTED_OBTAIN_FIRST_TEMPLATE' carries {record} and {set}, so the
    comparable part is everything before the first '{'. Matching on the
    prefix keeps the resolver independent of record and set names.
    """
    head = str(template or "").split("{", 1)[0]
    return " ".join(head.split()).upper()


class BusinessParagraphResolver:

    def __init__(self, line_utils, paragraph_index, log) -> None:
        self.lines_utils = line_utils
        self.paragraphs = paragraph_index
        self.log = log
        self._prefixes = tuple(
            marker_prefix(t) for t in NAVIGATION_MARKER_TEMPLATES if marker_prefix(t)
        )

    def business_paragraph(self, lines, cursor_set) -> str:
        """Highest-confidence first. Never guesses."""
        name = self._paragraph_of_navigation_marker(lines, cursor_set)
        if name:
            return name

        name = self._paragraph_holding_perform(lines, cursor_set.close_name)
        if name and name not in cursor_set.names.values():
            return name

        return ""                      # caller logs business_paragraph_unknown

    def _paragraph_of_navigation_marker(self, lines, cursor_set) -> str:
        for index, line in enumerate(lines):
            body = self.lines_utils.comment_body(line)
            if not body:
                continue
            compressed = " ".join(body.split()).upper()
            if not compressed.startswith(self._prefixes):
                continue
            header = self.paragraphs.enclosing_header(lines, index)
            if header and header.name not in cursor_set.names.values():
                return header.name
        return ""
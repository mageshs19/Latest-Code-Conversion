# LOCATION: converter/generators/db2_infrastructure/cursor_declare/declare_operand_parser.py
# ACTION: CREATE NEW FILE
"""Reads the COLUMN out of a free-text SQL fragment.

Two readers, one vocabulary:

    left_operand('NR_ID = :DCLG.NR-ID')  -> 'NR_ID'
    order_by_column('NR_ID DESC')        -> 'NR_ID'

CORRECTION - the parser understood SYMBOLS only.

A predicate with a KEYWORD operator carries no = < > character:

    DA_CRFMAS_479BFAS IS NOT NULL
    NR_ID_479BFAS BETWEEN :H1 AND :H2
    CO_ID_479BFAS IN (:H1, :H2)
    NM_ID_479BFAS LIKE :H1

so the WHOLE predicate came back as the "column", failed the ownership
test, and a perfectly valid cursor was refused with a DB2 WARNING. The
first operand token is taken instead, whichever operator form follows.

CORRECTION - a QUALIFIED operand never matched. T.NR_ID and NR_ID are
the same column; only the bare name is compared.

No regex. Every literal comes from rules/cursor_declaration_rules.py.
"""

from __future__ import annotations

from rules.cursor_declaration_rules import (
    HOST_VARIABLE_PREFIX,
    OPERAND_QUALIFIER_SEPARATOR,
    OPERAND_TRIM_CHARACTERS,
    ORDER_BY_DIRECTIONS,
    SYMBOL_OPERATORS,
)


class DeclareOperandParser:
    """Stateless operand reader."""

    @classmethod
    def left_operand(cls, condition: str) -> str:
        """The column on the left of a predicate, bare and unqualified.

        Returns "" for a host variable or an unreadable predicate, so
        the guard never refuses on something it cannot parse.
        """
        text = str(condition or "").strip()
        if not text:
            return ""

        cut = len(text)
        for token in SYMBOL_OPERATORS:
            position = text.find(token)
            if position >= 0:
                cut = min(cut, position)

        head = text[:cut].strip()
        if not head:
            return ""

        words = head.split()
        if not words:
            return ""

        return cls.bare_column(words[0])

    @classmethod
    def order_by_column(cls, entry: str) -> str:
        """The bare COLUMN part of '<column> [ASC|DESC]'."""
        parts = str(entry or "").strip().split()
        if not parts:
            return ""

        directions = {
            str(value or "").strip().upper()
            for value in (ORDER_BY_DIRECTIONS or ())
        }

        if len(parts) >= 2 and parts[-1].upper() in directions:
            parts = parts[:-1]

        if not parts:
            return ""

        return cls.bare_column(parts[0])

    @staticmethod
    def bare_column(token: str) -> str:
        """'T.NR_ID' -> 'NR_ID'. A host reference yields ''."""
        text = str(token or "").strip().strip(OPERAND_TRIM_CHARACTERS)
        if not text:
            return ""

        if text.startswith(HOST_VARIABLE_PREFIX):
            return ""

        if OPERAND_QUALIFIER_SEPARATOR in text:
            text = text.rsplit(OPERAND_QUALIFIER_SEPARATOR, 1)[-1]

        return text.strip(OPERAND_TRIM_CHARACTERS)


__all__ = ["DeclareOperandParser"]
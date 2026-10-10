# LOCATION: converter/generators/cursor_paragraph/join_key_label_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""DB2 column -> IDMS COBOL field name, for a job-log label.

    DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF
             ^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^
             Sheet Mapping   DCLGEN

Sheet Mapping is the authority for the COBOL field name; DCLGEN is the
authority for the host variable. They are different facts and the label
is a LOOKUP, never a derivation:

    NS-DBSTK-479BEFF  ->  NR-DB-STOCK      NS becomes NR

No string rule produces that. When the lookup fails the host name is
displayed instead AND the fallback is reported - a silent fallback is
how the wrong label shipped unnoticed.

CORRECTION - this module imported DIAG_JOIN_KEY_LABEL_FALLBACK, a
standalone constant that no longer exists. The wording now lives in
KEY_DIAGNOSTIC_MESSAGES, one dictionary literal, alongside every other
message this feature emits. A second standalone copy would be a second
place to edit and one commit away from two wordings for one event.

This class RESOLVES. It owns no template, no indent and no layout.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_paragraph_rules import (
    DCLGEN_GROUP_PREFIX,
    KEY_DIAGNOSTIC_MESSAGES,
)

LABEL_FALLBACK_KEY = "label_fallback"
UNKNOWN = "(unknown)"


class JoinKeyLabelResolver:
    """Sheet Mapping COBOL field name for a DB2 column."""

    def __init__(self, mapping_repository=None) -> None:
        self.mapping_repository = mapping_repository
        self.messages: list[str] = []

    def reset(self) -> None:
        """Clear per-program diagnostics."""
        self.messages = []

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def label_for(self, table: str, column: str, host: str) -> str:
        """IDMS COBOL field name, or the host name with a diagnostic."""
        resolved = self._cobol_field(table, column)
        if resolved:
            return resolved

        self._report(table=table, column=column)
        return NameNormalizer.to_cobol(host)

    @staticmethod
    def table_of(group: str) -> str:
        """DCLDZBEFFTV -> DZBEFFTV. Returns the input when unprefixed."""
        text = str(group or "").strip().upper()
        prefix = str(DCLGEN_GROUP_PREFIX or "").upper()
        if prefix and text.startswith(prefix):
            return text[len(prefix):]
        return text

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------
    def _cobol_field(self, table: str, column: str) -> str:
        """Sheet Mapping COBOL Zone for this DB2 column.

        Probed through several accessor names because the repository has
        shipped more than one surface. A missing accessor degrades to
        "unresolved", never to an exception in the middle of a run.
        """
        if self.mapping_repository is None or not column:
            return ""

        for probe in (
            "cobol_field_for_column",
            "idms_field_for_column",
            "find_cobol_zone",
        ):
            method = getattr(self.mapping_repository, probe, None)
            if method is None:
                continue

            value = self._call(method, table, column)
            if value:
                return NameNormalizer.to_cobol(str(value))

        return ""

    @staticmethod
    def _call(method, table: str, column: str):
        """Keyword first, positional second. Both failures are survivable."""
        try:
            return method(table_name=table, column_name=column)
        except TypeError:
            pass
        except Exception:                      # noqa: BLE001
            return None

        try:
            return method(table, column)
        except Exception:                      # noqa: BLE001
            return None

    def _report(self, table: str, column: str) -> None:
        template = KEY_DIAGNOSTIC_MESSAGES.get(LABEL_FALLBACK_KEY, "")
        if not template:
            # An unknown key must never LOSE the diagnostic.
            self.messages.append(
                f"Cursor paragraphs: label fallback for {column} "
                f"of {table}."
            )
            return

        try:
            self.messages.append(
                template.format(
                    column=column or UNKNOWN,
                    table=table or UNKNOWN,
                )
            )
        except (KeyError, IndexError):
            self.messages.append(template)


__all__ = ["JoinKeyLabelResolver"]
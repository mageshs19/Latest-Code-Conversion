# LOCATION: converter/generators/cursor_paragraph/join_key_label_resolver.py
# ACTION: REPLACE ENTIRE FILE
"""DB2 column -> IDMS COBOL field name, for a job-log label.

    DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF
             ^^^^^^^^^^^     ^^^^^^^^^^^^^^^^^^
             Sheet Mapping   DCLGEN

Sheet Mapping is the authority for the COBOL field name; DCLGEN is the
authority for the host variable. They are different facts and the label
is a LOOKUP, never a derivation:

    NS-DBSTK-479BEFF  ->  NR-DB-STOCK

No string rule produces that. When the lookup fails the host name is
used AND the fallback is reported, so a wrong label is never silent.

CORRECTION - _call was decorated @staticmethod while declaring `self`

    @staticmethod
    def _call(self, method, table, column):

The decorator suppresses instance binding, so `self._call(method,
candidate, column)` bound method->self, candidate->method,
column->table and left `column` unfilled:

    TypeError: JoinKeyLabelResolver._call() missing 1 required
               positional argument: 'column'

Removing `self` was never an option: the body calls
`self._report_lookup_failure()`, which needs the instance. `_call` is
therefore a plain instance method. The decorator is the defect.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_paragraph_rules import (
    DCLGEN_GROUP_PREFIX,
    DCLGEN_TABLE_SUFFIX,
    KEY_DIAGNOSTIC_MESSAGES,
    MAPPING_TABLE_SEPARATOR,
    MAPPING_TABLE_SUFFIX,
    STRIP_REDEFINES_SUFFIX_FROM_KEY_LABEL,
)

LABEL_FALLBACK_KEY = "label_fallback"
LOOKUP_FAILED_KEY = "label_lookup_failed"
UNKNOWN = "(unknown)"
LEVEL_DIGITS = 2


class JoinKeyLabelResolver:
    """Resolves one DB2 column to the IDMS COBOL field name it came from."""

    def __init__(self, mapping_repository=None) -> None:
        self.mapping_repository = mapping_repository
        self.messages: list[str] = []

    def reset(self) -> None:
        """Drop the previous program's diagnostics.

        One resolver instance serves every cursor of every program in a
        folder run, so an uncleared list carries program 1's fallbacks
        into program 2.
        """
        self.messages = []

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    def label_for(self, table: str, column: str, host: str) -> str:
        resolved = self._cobol_field(table, column)
        if resolved:
            return resolved

        self._report(table=table, column=column)
        return NameNormalizer.to_cobol(host)

    @staticmethod
    def table_of(group: str) -> str:
        """DCLGEN group name -> table name. 'DCLDZBEFFTV' -> 'DZBEFFTV'."""
        text = str(group or "").strip().upper()
        prefix = str(DCLGEN_GROUP_PREFIX or "").upper()
        if prefix and text.startswith(prefix):
            return text[len(prefix):]
        return text

    @staticmethod
    def candidate_tables(table: str) -> list[str]:
        """Every spelling of one table, DCLGEN first then Sheet Mapping."""
        text = str(table or "").strip().upper()
        if not text:
            return []

        out = [text]
        suffix = str(DCLGEN_TABLE_SUFFIX or "").upper()
        mapped = str(MAPPING_TABLE_SUFFIX or "").upper()

        base = text[:-len(suffix)] if suffix and text.endswith(suffix) else text

        for candidate in (
            f"{base}{mapped}",
            f"{base}{MAPPING_TABLE_SEPARATOR}{mapped}",
            base,
        ):
            if candidate and candidate not in out:
                out.append(candidate)

        return out

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def _cobol_field(self, table: str, column: str) -> str:
        if self.mapping_repository is None or not column:
            return ""

        for candidate in self.candidate_tables(table):
            for probe in (
                "cobol_field_for_column",
                "idms_field_for_column",
                "find_cobol_zone",
            ):
                method = getattr(self.mapping_repository, probe, None)
                if method is None:
                    continue

                value = self._call(method, candidate, column)
                field = self._field_name(value)
                if field:
                    return field

        return ""

    def _call(self, method, table: str, column: str):
        """Invoke one repository accessor by keyword, then positionally.

        The accessor on MappingRowQuery is declared

            cobol_field_for_column(self, table_name, column_name)

        so the keyword form is tried first and is the expected path. A
        TypeError there means THIS accessor does not accept those
        keywords, not that the lookup failed - so the positional form is
        tried before anything is reported.

        Never raises. A repository that throws yields None and one
        reported diagnostic, so a single bad accessor cannot abort the
        conversion.
        """
        try:
            return method(table_name=table, column_name=column)
        except TypeError:
            pass
        except Exception as error:  # noqa: BLE001
            self._report_lookup_failure(method, error)
            return None

        try:
            return method(table, column)
        except Exception as error:  # noqa: BLE001
            self._report_lookup_failure(method, error)
            return None

    @staticmethod
    def _strip_redefines_suffix(name: str) -> str:
        """Drop a trailing REDEFINES marker: NR-ID-STOCK-R1 -> NR-ID-STOCK.

        Policy-gated. The suffix is a real part of the mapped name, so
        removing it is a DECISION, not a correction. No regex: the test
        is 'final hyphen segment is R followed by digits', which is the
        whole convention.
        """
        if not STRIP_REDEFINES_SUFFIX_FROM_KEY_LABEL:
            return name

        head, separator, tail = name.rpartition("-")
        if not separator or not head:
            return name

        if tail[:1] == "R" and tail[1:].isdigit():
            return head

        return name

    @staticmethod
    def _field_name(value) -> str:
        """Drop a COBOL Zone level prefix and terminator.

        The workbook cell reads '  04  CT-RK-TPROD       '. Normalising
        that whole string yields 04-CT-RK-TPROD, which is not a
        data-name.
        """
        text = str(value or "").strip().rstrip(".").strip()
        if not text:
            return ""

        parts = text.split()
        if len(parts) > 1 and parts[0].isdigit() and len(parts[0]) <= LEVEL_DIGITS:
            text = " ".join(parts[1:]).strip()

        if not text or text.isdigit():
            return ""

        name = NameNormalizer.to_cobol(text)
        return JoinKeyLabelResolver._strip_redefines_suffix(name)
    
    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def _report_lookup_failure(self, method, error: Exception) -> None:
        template = KEY_DIAGNOSTIC_MESSAGES.get(LOOKUP_FAILED_KEY, "")
        name = getattr(method, "__name__", str(method))
        detail = f"{type(error).__name__}: {error}"

        if template:
            try:
                text = template.format(method=name, error=detail)
            except (KeyError, IndexError):
                text = f"Cursor paragraphs: {name} raised {detail}."
        else:
            text = f"Cursor paragraphs: {name} raised {detail}."

        if text not in self.messages:
            self.messages.append(text)

    def _report(self, table: str, column: str) -> None:
        template = KEY_DIAGNOSTIC_MESSAGES.get(LABEL_FALLBACK_KEY, "")
        if not template:
            self.messages.append(
                f"Cursor paragraphs: label fallback for "
                f"{column or UNKNOWN} of {table or UNKNOWN}."
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
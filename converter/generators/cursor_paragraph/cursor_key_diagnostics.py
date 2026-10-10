# LOCATION: converter/generators/cursor_paragraph/cursor_key_diagnostics.py
# ACTION: REPLACE ENTIRE FILE
"""The row-identity DISPLAY lines inside a FETCH WHEN OTHER branch.

    DISPLAY 'CT-RKT-PROD = ' CT-RKTPROD-479BEFF
                             OF DCLDZBEFFTV
    DISPLAY 'NR-ID-STOCK = ' NR-IDSTOCK-479BEFF
                             OF DCLDZBEFFTV

ONE renderer for both diagnostic paths - the driving key and the
fetched columns. Two renderers is what let the separator drift to ':'
in one of them while the other kept '='.

Three properties, all derived, none hard-coded:

  LABEL       the IDMS COBOL field name from Sheet Mapping, resolved by
              JoinKeyLabelResolver. Falls back to the host name AND
              reports the fallback.
  WIDTH       the widest label in THIS branch, so every host starts at
              the same column without a constant that can be wrong.
  ALIGNMENT   "OF <group>" sits under the host, at an offset taken from
              the length of the rendered prefix on the line above.

A qualified reference is MANDATORY. A foreign-key column keeps the
parent's column name, so the data-name exists in two DCLGEN groups and
the bare form is a not-unique reference the compiler rejects.
"""

from __future__ import annotations

from converter.generators.cursor_paragraph.join_key_label_resolver import (
    JoinKeyLabelResolver,
)
from converter.services.name_normalizer import NameNormalizer
from rules.cursor_paragraph_rules import (
    ALIGN_KEY_QUALIFIER,
    BODY_FIRST_COLUMN,
    EMIT_KEY_DIAGNOSTICS,
    HOST_GROUP_SEPARATOR,
    HOST_REFERENCE_PREFIX,
    IND_WHEN_BODY,
    KEY_BODY_END_COLUMN,
    KEY_DIAGNOSTIC_LIMIT,
    KEY_DISPLAY_TEMPLATE,
    KEY_LABEL_MIN_WIDTH,
    KEY_LABEL_SOURCE,
    KEY_LABEL_SOURCE_MAPPING,
    KEY_QUALIFIER_TEMPLATE,
    TOKEN_OF,
)

HOST_OF_SEPARATOR = f" {TOKEN_OF} "


class KeyDiagnosticsBuilder:
    """Renders the DISPLAY pairs. Owns no label lookup of its own."""

    def __init__(
        self,
        label_resolver: JoinKeyLabelResolver | None = None,
    ) -> None:
        self.label_resolver = label_resolver or JoinKeyLabelResolver()

    @property
    def messages(self) -> list[str]:
        return self.label_resolver.messages

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def lines_for_where(self, conditions: list[str]) -> list[str]:
        """One DISPLAY pair per join predicate."""
        return self._render(
            [self._host_of_condition(c) for c in conditions or []]
        )

    def lines_for_hosts(self, hosts: list[str]) -> list[str]:
        """Fallback: display the fetched columns themselves."""
        return self._render(list(hosts or []))

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _render(self, raw_hosts: list[str]) -> list[str]:
        if not EMIT_KEY_DIAGNOSTICS:
            return []

        pairs: list[tuple[str, str, str]] = []
        seen: set[str] = set()

        for raw in raw_hosts:
            host, group = self._split(raw)
            if not host or host in seen:
                continue
            seen.add(host)
            pairs.append((self._label(host, group), host, group))

            # The manual shows five. An unbounded list buries the
            # failure in the job log.
            if 0 < KEY_DIAGNOSTIC_LIMIT <= len(pairs):
                break

        if not pairs:
            return []

        width = max(
            KEY_LABEL_MIN_WIDTH,
            max(len(label) for label, _, _ in pairs),
        )

        lines: list[str] = []
        for label, host, group in pairs:
            display = KEY_DISPLAY_TEMPLATE.format(
                label=label.ljust(width),
                host=host,
            )
            lines.append(IND_WHEN_BODY + display)

            if not group:
                continue

            qualifier = KEY_QUALIFIER_TEMPLATE.format(group=group)
            lines.append(self._qualifier_line(display, host, qualifier))

        return lines

    @staticmethod
    def _qualifier_line(display: str, host: str, qualifier: str) -> str:
        """Align the qualifier under the host, without overflowing.

        The offset is the length of everything rendered before the host
        on the line above - DERIVED, never arithmetic over a constant.
        Truncation is never acceptable: a cut data-name does not
        compile, so an over-long line falls back to the body indent.
        """
        if not ALIGN_KEY_QUALIFIER:
            return IND_WHEN_BODY + qualifier

        offset = len(display) - len(host)
        aligned = IND_WHEN_BODY + " " * offset + qualifier

        end_column = BODY_FIRST_COLUMN + len(aligned) - 1
        if end_column > KEY_BODY_END_COLUMN:
            return IND_WHEN_BODY + qualifier

        return aligned

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _label(self, host: str, group: str) -> str:
        if KEY_LABEL_SOURCE != KEY_LABEL_SOURCE_MAPPING:
            return NameNormalizer.to_cobol(host)

        return self.label_resolver.label_for(
            table=self.label_resolver.table_of(group),
            column=NameNormalizer.normalize(host),
            host=host,
        )

    @staticmethod
    def _split(reference: str) -> tuple[str, str]:
        """Accepts "H OF G", ":G.H" and a bare host. Returns (host, group)."""
        text = str(reference or "").strip().lstrip(HOST_REFERENCE_PREFIX)
        if not text:
            return "", ""

        upper = text.upper()

        if HOST_OF_SEPARATOR in upper:
            host, _sep, group = upper.partition(HOST_OF_SEPARATOR)
            return host.strip(), group.strip()

        if HOST_GROUP_SEPARATOR in upper:
            group, _sep, host = upper.partition(HOST_GROUP_SEPARATOR)
            return host.strip(), group.strip()

        return upper, ""

    @staticmethod
    def _host_of_condition(condition: str) -> str:
        """The host operand of a join predicate: right of the '='."""
        text = str(condition or "")
        _left, _sep, right = text.partition("=")
        return (right or text).strip()


__all__ = ["KeyDiagnosticsBuilder"]
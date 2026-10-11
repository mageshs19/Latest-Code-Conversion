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
    IND_KEY_CONTINUATION,
    IND_WHEN_BODY,
    KEY_BODY_END_COLUMN,
    KEY_DIAGNOSTIC_LIMIT,
    KEY_DISPLAY_LITERAL_TEMPLATE,
    KEY_DISPLAY_TEMPLATE,
    KEY_LABEL_MIN_WIDTH,
    KEY_LABEL_SOURCE,
    KEY_LABEL_SOURCE_MAPPING,
    KEY_QUALIFIER_TEMPLATE,
    SKIP_UNQUALIFIED_KEY_HOSTS,
    TOKEN_OF,
    WRAP_KEY_DISPLAY,
)

HOST_OF_SEPARATOR = f" {TOKEN_OF} "


class KeyDiagnosticsBuilder:
    """Renders the driving-key DISPLAY lines of a child cursor's
    WHEN OTHER branch.

    CORRECTION - a missing dependency was silently substituted.

    __init__ previously read

        self.label_resolver = label_resolver or JoinKeyLabelResolver()

    so KeyDiagnosticsBuilder() was legal and produced a resolver with NO
    Sheet Mapping repository. Every lookup returned "", the label fell
    back to the DCLGEN host name, and the generated COBOL carried

        DISPLAY 'CT-RKTPROD-479BEFF = ' CT-RKTPROD-479BEFF

    instead of the mapped name the manual reference shows. Nothing
    failed and nothing was logged at the call site.

    The label is Sheet Mapping DATA. A builder without a resolver cannot
    produce a correct one, so it is no longer constructible.
    """

    def __init__(
        self,
        label_resolver: JoinKeyLabelResolver | None = None,
    ) -> None:
        if label_resolver is None:
            raise ValueError(
                "KeyDiagnosticsBuilder requires a JoinKeyLabelResolver "
                "built over the run's MappingRepository. Substituting an "
                "empty resolver degrades every driving-key label to its "
                "DCLGEN host name without reporting anything."
            )

        self.label_resolver = label_resolver

    @property
    def messages(self) -> list[str]:
        return self.label_resolver.messages

    def lines_for_where(self, conditions: list[str]) -> list[str]:
        return self._render(
            [self._host_of_condition(c) for c in conditions or []]
        )

    def lines_for_hosts(self, hosts: list[str]) -> list[str]:
        return self._render(list(hosts or []))

    def _render(self, raw_hosts: list[str]) -> list[str]:
        if not EMIT_KEY_DIAGNOSTICS:
            return []

        pairs: list[tuple[str, str, str]] = []
        seen: set[str] = set()

        for raw in raw_hosts:
            host, group = self._split(raw)
            if not host or host in seen:
                continue
            if not group and SKIP_UNQUALIFIED_KEY_HOSTS:
                continue

            seen.add(host)
            pairs.append((self._label(host, group), host, group))

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
            lines.extend(self._pair_lines(label.ljust(width), host, group))
        return lines

    def _pair_lines(self, label: str, host: str, group: str) -> list[str]:
        display = KEY_DISPLAY_TEMPLATE.format(label=label, host=host)
        inline = IND_WHEN_BODY + display

        if self._fits(inline) or not WRAP_KEY_DISPLAY:
            out = [inline]
            if group:
                out.append(
                    self._qualifier_line(
                        display,
                        host,
                        KEY_QUALIFIER_TEMPLATE.format(group=group),
                    )
                )
            return out

        out = [
            IND_WHEN_BODY
            + KEY_DISPLAY_LITERAL_TEMPLATE.format(label=label),
            IND_KEY_CONTINUATION + host,
        ]
        if group:
            out.append(
                IND_KEY_CONTINUATION
                + KEY_QUALIFIER_TEMPLATE.format(group=group)
            )
        return out

    @staticmethod
    def _fits(line: str) -> bool:
        return BODY_FIRST_COLUMN + len(line) - 1 <= KEY_BODY_END_COLUMN

    @classmethod
    def _qualifier_line(
        cls,
        display: str,
        host: str,
        qualifier: str,
    ) -> str:
        if not ALIGN_KEY_QUALIFIER:
            return IND_WHEN_BODY + qualifier

        offset = len(display) - len(host)
        aligned = IND_WHEN_BODY + " " * offset + qualifier

        if not cls._fits(aligned):
            return IND_KEY_CONTINUATION + qualifier

        return aligned

    def _label(self, host: str, group: str) -> str:
        if KEY_LABEL_SOURCE != KEY_LABEL_SOURCE_MAPPING:
            return NameNormalizer.to_cobol(host)

        label = self.label_resolver.label_for(
            table=self.label_resolver.table_of(group),
            column=NameNormalizer.normalize(host),
            host=host,
        )

        # The resolver already recorded WHY on a miss, and `messages`
        # exposes it. Falling back here keeps the COBOL renderable.
        return label or NameNormalizer.to_cobol(host)

    @staticmethod
    def _split(reference: str) -> tuple[str, str]:
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
        text = str(condition or "")
        _left, _sep, right = text.partition("=")
        return (right or text).strip()


__all__ = ["KeyDiagnosticsBuilder"]
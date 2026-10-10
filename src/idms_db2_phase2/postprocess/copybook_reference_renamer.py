from __future__ import annotations

import re

from idms_db2_phase2.services.name_derivation_resolver import (
    NameDerivationResolver,
)
from patterns.copybook_reference_rename_patterns import (
    COPY_NAME_PATTERN,
    WORD_REFERENCE_PATTERN_TEMPLATE,
)


class CopybookReferenceRenamer:
    """Renames source copybook references to their derived DB2 names.

    The DB2 copybook library ships each converted copybook under its derived
    name (the VM...BD... / VM...BZ... -> VMDZ... rule), e.g. VMBD205I becomes
    VMDZ205I and VMBZ270I becomes VMDZ270I. A converted program that still
    copies the original name fails to compile, because the old member no
    longer exists in the DB2 library.

    This pass runs for every converted program. It is driven entirely by the
    COPY statements found in the program, so no copybook, record, or program
    name is hardcoded.

    What it rewrites, for each derivable copybook the program COPYs:
      - the COPY statement itself,
      - every qualified reference (OF/IN <copybook>),
      - the "<copybook>-REC" style record name and any other hyphen-qualified
        data name built on the copybook,
      - READ ... INTO <copybook>, INITIALIZE <copybook>, MOVE ... <copybook>.

    What it never touches:
      - comment / debug / page-eject lines (indicator in column 7), so the
        historical REMARKS block stays byte-for-byte identical,
      - names that are not derivable (COPY IDMS ..., ESDATMAS, subschema and
        IDMS record names whose marker is not BD/BZ),
      - IDMS records used only with IDMS verbs (OBTAIN, STORE, MODIFY) that
        have no DB2 DCLGEN equivalent.

    The derived name is always the same length as the source name (the two
    character marker is swapped for "DZ"), so a whole-line substitution keeps
    every fixed-format column - including the sequence area - aligned.
    """

    def __init__(self, resolver: NameDerivationResolver | None = None) -> None:
        self._resolver = resolver or NameDerivationResolver()

    def apply(
        self,
        text: str,
        diagnostics: list[str] | None = None,
    ) -> str:
        if not text:
            return text or ""

        lines = (
            str(text)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .split("\n")
        )

        renames = self._collect_renames(lines)
        if not renames:
            return text

        compiled = [
            (
                re.compile(
                    WORD_REFERENCE_PATTERN_TEMPLATE.format(name=re.escape(old)),
                    flags=re.IGNORECASE,
                ),
                new,
            )
            for old, new in renames.items()
        ]

        output: list[str] = []
        changed = False
        seen_copy: set[str] = set()

        for line in lines:
            if self._is_comment_or_debug(line):
                output.append(line)
                continue

            new_line = line
            for pattern, new in compiled:
                new_line = pattern.sub(new, new_line)

            if new_line != line:
                changed = True

            # Drop a duplicate COPY <new> that the rename may have produced
            # (keep the first). A copybook is copied exactly once.
            copy_match = COPY_NAME_PATTERN.search(self._body(new_line))
            if copy_match:
                copied = copy_match.group("name").upper()
                if copied in renames.values():
                    if copied in seen_copy:
                        changed = True
                        continue
                    seen_copy.add(copied)

            output.append(new_line)

        if changed and diagnostics is not None:
            pairs = ", ".join(f"{old} -> {new}" for old, new in renames.items())
            diagnostics.append(
                f"Renamed source copybook references to derived DB2 names: "
                f"{pairs}."
            )

        return "\n".join(output)

    # ------------------------------------------------------------------ #
    def _collect_renames(self, lines: list[str]) -> dict[str, str]:
        """old -> new for every derivable copybook the program COPYs."""
        renames: dict[str, str] = {}
        for line in lines:
            if self._is_comment_or_debug(line):
                continue
            match = COPY_NAME_PATTERN.search(self._body(line))
            if not match:
                continue
            name = match.group("name").strip().upper()
            if not name or not self._resolver.is_derivable(name):
                continue
            derived = self._resolver.derive(name)
            if derived and derived != name:
                renames[name] = derived
        return renames

    # ------------------------------------------------------------------ #
    # Fixed-format helpers
    # ------------------------------------------------------------------ #
    def _is_comment_or_debug(self, line: str) -> bool:
        text = str(line or "").rstrip("\n")
        if len(text) >= 7 and text[:6].strip().isdigit():
            return text[6:7] in {"*", "/", "D", "d"}
        stripped = text.strip()
        return (
            stripped.startswith("*")
            or stripped.startswith("/")
            or stripped.upper().startswith("D ")
        )

    def _body(self, line: str) -> str:
        text = str(line or "").rstrip("\n")
        if len(text) >= 72 and text[:6].strip().isdigit():
            return text[7:72]
        if len(text) > 7 and text[:6].strip().isdigit():
            return text[7:]
        return text

# LOCATION: src/idms_db2_phase2/transformers/lrf_update_expander.py
# ACTION: CREATE NEW FILE
"""Expands the UPDATE-side Logical Record Facility syntax into classic IDMS.

WHY THIS EXISTS
---------------
``LrfPathExpander`` teaches the converter the READ and DELETE logical-record
forms::

    OBTAIN FIRST <logical-record> WHERE <keyword>.   -> OBTAIN FIRST <rec> WITHIN <set>.
    ERASE        <logical-record> WHERE <keyword>.   -> ERASE <rec>.

The WRITE-side forms have the same shape but the converter never learned
them, so an update program written against a logical record kept its LRF
verbs all the way to the residual-IDMS checks::

    MODIFY <logical-record> WHERE <keyword>.   (SQL UPDATE)
    STORE  <logical-record> WHERE <keyword>.   (SQL INSERT)

This transformer closes that gap. It rewrites the update-side LRF form into
the classic IDMS form the rest of the pipeline already converts to DB2 DML,
and the update post-processor then supplies the WHERE key and audit columns.

NO-LRF CONTRACT
---------------
With no logical record metadata, or with metadata but no LRF update syntax in
the program, ``expand()`` returns the source text byte-for-byte. A program
that never used a logical record therefore behaves exactly as before.

MODIFY vs STORE
---------------
MODIFY is the SQL UPDATE case. The element record to modify is the record the
path makes current with its last FIND / OBTAIN navigation command - the only
element the subschema parser captures for a MODIFY path-group - so MODIFY is
expanded whenever that record resolves and is mapped.

STORE is the SQL INSERT case. A STORE path-group usually seeds several element
records the subschema does not pin down, so guessing which one to write is
unsafe. STORE is expanded only for a single-element logical record; otherwise
it is kept, with a ``*DB2-KEEP:`` audit comment, for manual review.

NAME FORM
---------
Generated names are COBOL form (UPPERCASE, hyphens). NameNormalizer is not
used here: normalize() yields the DB2 column form and would emit VMBTL07_R01.
"""

from __future__ import annotations

from idms_db2_phase2.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.lrf_program_patterns import LR_MODIFY_WHERE_PATTERN
from rules.lrf_conversion_rules import (
    ENABLE_LRF_PATH_EXPANSION,
    EXPANDED_UPDATE_TEMPLATE,
    LRF_UPDATE_MESSAGES,
    MODIFY_TEMPLATE,
    REQUIRE_MAPPED_DRIVING_RECORD,
    SKIPPED_NO_PATH_TEMPLATE,
    SKIPPED_NO_RECORD_TEMPLATE,
    SKIPPED_STORE_AMBIGUOUS_TEMPLATE,
    SKIPPED_UNMAPPED_TEMPLATE,
    STATEMENT_TERMINATOR,
    STORE_TEMPLATE,
)

PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"
COMMENT_INDICATORS = ("*", "/", "D", "-")
COMMENT_PREFIX_COLUMNS = "      "
DEFAULT_INDENT = "    "
VERB_STORE = "STORE"
NAVIGATION_VERBS = ("FIND", "OBTAIN")


def cobol_name(value: str) -> str:
    """UPPERCASE COBOL/IDMS form: hyphens, never underscores."""
    return str(value or "").strip().upper().replace("_", "-")


class LrfUpdateExpander:
    """Rewrites LRF MODIFY / STORE program syntax into classic IDMS syntax."""

    def __init__(
        self,
        *,
        path_resolver=None,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.path_resolver = path_resolver
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

    # ---------------------------------------------------------- public
    def expand(self, cobol_text: str) -> str:
        self.messages = []

        text = str(cobol_text or "")
        if not text.strip() or not ENABLE_LRF_PATH_EXPANSION:
            return text

        if self.path_resolver is None or self.path_resolver.is_empty():
            if self._contains_lr_update_syntax(text):
                self._log("no_logical_records")
            return text

        if not self._contains_lr_update_syntax(text):
            return text

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        output: list[str] = []
        in_procedure = False
        expanded = 0
        skipped = 0

        for line in lines:
            logical = self._logical(line)
            upper = logical.upper()

            if PROCEDURE_DIVISION_TOKEN in upper:
                in_procedure = True
                output.append(line)
                continue

            if not in_procedure or self._is_comment(line) or not logical:
                output.append(line)
                continue

            match = LR_MODIFY_WHERE_PATTERN.match(logical)
            if match:
                rendered, ok = self._expand_update(line, match)
                output.extend(rendered)
                expanded += 1 if ok else 0
                skipped += 0 if ok else 1
                continue

            output.append(line)

        if expanded or skipped:
            self._log("summary", expanded=expanded, skipped=skipped)

        if not (expanded or skipped):
            return text

        return "\n".join(output).rstrip() + "\n"

    # ------------------------------------------------------- expansion
    def _expand_update(self, line: str, match) -> tuple[list[str], bool]:
        verb = str(match.group("verb") or "").upper()
        lr_name = cobol_name(match.group("lr"))
        keyword = cobol_name(match.group("keyword"))

        path = self._lookup_path(keyword)
        if path is None:
            self._log("keyword_not_found", keyword=keyword)
            return self._keep(
                line, SKIPPED_NO_PATH_TEMPLATE.format(keyword=keyword)
            ), False

        if verb == VERB_STORE and self._store_is_ambiguous(path):
            self._log("store_ambiguous", keyword=keyword)
            return self._keep(
                line, SKIPPED_STORE_AMBIGUOUS_TEMPLATE.format(keyword=keyword)
            ), False

        record = self._driving_record(path)
        if not record:
            self._log("no_record", keyword=keyword)
            return self._keep(
                line, SKIPPED_NO_RECORD_TEMPLATE.format(keyword=keyword)
            ), False

        if REQUIRE_MAPPED_DRIVING_RECORD and not self._record_is_mapped(record):
            self._log("record_unmapped", record=record, keyword=keyword)
            return self._keep(
                line, SKIPPED_UNMAPPED_TEMPLATE.format(record=record)
            ), False

        rendered = self._comment(line, EXPANDED_UPDATE_TEMPLATE.format(
            verb=verb, lr=lr_name, keyword=keyword, record=record,
        ))
        template = STORE_TEMPLATE if verb == VERB_STORE else MODIFY_TEMPLATE
        rendered.extend(self._statement(line, template.format(record=record)))

        self._log(
            "expanded",
            verb=verb, lr=lr_name, keyword=keyword, record=record,
        )
        return rendered, True

    # --------------------------------------------------- path analysis
    def _driving_record(self, path) -> str:
        """The element record the path makes current, in COBOL form.

        For a MODIFY / STORE path-group the record to write is the one the
        last FIND / OBTAIN navigation command establishes as current. The
        subschema parser does not retain the MODIFY / STORE verb line itself,
        so the navigation record is the reliable driving record.
        """
        record = ""
        for command in getattr(path, "commands", None) or []:
            if str(getattr(command, "verb", "") or "").upper() in NAVIGATION_VERBS:
                name = cobol_name(getattr(command, "record_name", ""))
                if name:
                    record = name
        return record

    def _store_is_ambiguous(self, path) -> bool:
        """True when a STORE path seeds more than one element record."""
        elements = [
            name
            for name in self._element_records(
                getattr(path, "logical_record", "")
            )
            if str(name or "").strip()
        ]
        return len(elements) > 1

    def _lookup_path(self, keyword: str):
        repository = getattr(self.path_resolver, "lrf_repository", None)
        if repository is None:
            return None
        try:
            return repository.path_for_keyword(keyword)
        except Exception:  # noqa: BLE001
            return None

    def _element_records(self, logical_record_name: str) -> list:
        repository = getattr(self.path_resolver, "lrf_repository", None)
        if repository is None:
            return []
        try:
            return repository.element_records(logical_record_name) or []
        except Exception:  # noqa: BLE001
            return []

    def _record_is_mapped(self, record_name: str) -> bool:
        try:
            return bool(self.path_resolver.record_is_mapped(record_name))
        except Exception:  # noqa: BLE001
            return True

    # ---------------------------------------------------------- render
    def _statement(self, template_line: str, body: str) -> list[str]:
        text = body.rstrip()
        if not text.endswith(STATEMENT_TERMINATOR):
            text = f"{text}{STATEMENT_TERMINATOR}"
        indent = self._body_indent(template_line)
        return self._emit(template_line, f"{indent}{text}", indicator=" ")

    def _comment(self, template_line: str, body: str) -> list[str]:
        """Comment body starts at column 8 - no indent, no leading star."""
        text = str(body or "").lstrip("*").strip()
        return self._emit(template_line, text, indicator="*")

    def _keep(self, line: str, marker: str) -> list[str]:
        rendered = self._comment(line, marker)
        rendered.extend(self._comment(line, self._logical(line)))
        return rendered

    def _emit(self, template_line: str, body: str, indicator: str) -> list[str]:
        if not self._is_fixed(template_line):
            if indicator == "*":
                return [f"{COMMENT_PREFIX_COLUMNS}*{body}"]
            return [body]

        left, _ind, _old, right = self.fixed_format.split(template_line)
        try:
            return self.fixed_format.emit(left, indicator, body, right)
        except Exception:  # noqa: BLE001
            return [template_line]

    # --------------------------------------------------------- helpers
    def _logical(self, line: str) -> str:
        try:
            return str(self.fixed_format.logical(line) or "").strip()
        except Exception:  # noqa: BLE001
            return str(line or "").strip()

    def _is_fixed(self, line: str) -> bool:
        try:
            return bool(self.fixed_format.is_fixed_line(line))
        except Exception:  # noqa: BLE001
            return False

    def _body_indent(self, line: str) -> str:
        if not self._is_fixed(line):
            text = str(line or "")
            return " " * (len(text) - len(text.lstrip(" ")))
        try:
            _l, _i, body, _r = self.fixed_format.split(line)
            return " " * (len(body) - len(body.lstrip(" ")))
        except Exception:  # noqa: BLE001
            return DEFAULT_INDENT

    @staticmethod
    def _is_comment(line: str) -> bool:
        text = str(line or "")
        if len(text) >= 7 and text[:6].strip().isdigit():
            return text[6] in COMMENT_INDICATORS
        return text.lstrip().startswith(COMMENT_INDICATORS)

    @staticmethod
    def _contains_lr_update_syntax(text: str) -> bool:
        for line in str(text or "").upper().splitlines():
            if LR_MODIFY_WHERE_PATTERN.match(line.strip()):
                return True
        return False

    def _log(self, key: str, **values) -> None:
        template = LRF_UPDATE_MESSAGES.get(key, "")
        if template:
            self.messages.append(template.format(**values))


__all__ = ["LrfUpdateExpander", "cobol_name"]

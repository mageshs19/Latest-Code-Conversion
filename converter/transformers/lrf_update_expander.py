# LOCATION: converter/transformers/lrf_update_expander.py
# ACTION: REPLACE ENTIRE FILE
"""Expands the UPDATE-side Logical Record Facility syntax into classic IDMS.

WHY THIS EXISTS
---------------
``LrfPathExpander`` teaches the converter the READ and DELETE logical-record
forms::

    OBTAIN FIRST <logical-record> WHERE <keyword>.  -> OBTAIN FIRST <rec> WITHIN <set>.
    ERASE        <logical-record> WHERE <keyword>.  -> ERASE <rec>.

The WRITE-side forms have the same shape but the converter never learned
them, so an update program written against a logical record kept its LRF
verbs all the way to the residual-IDMS checks::

    MODIFY <logical-record> WHERE <keyword>.   (SQL UPDATE)
    STORE  <logical-record> WHERE <keyword>.   (SQL INSERT)

CORRECTION 1 - THE PRE-CHECK READ RAW LINES
-------------------------------------------
``_contains_lr_update_syntax`` applied the anchored pattern to RAW source
lines. A fixed-format record is::

    000186     STORE VMBTL07-R01 WHERE ST-VMBEVEF.          01860000
    |----|     |------------ body, cols 8-72 -----|         |------|
    cols 1-6                                                cols 73-80

``^\\s*(MODIFY|STORE)`` cannot match ``000186...`` and ``$`` cannot match
with ``01860000`` trailing, so the gate returned False for EVERY mainframe
program and the whole pass silently no-opped. This is the same defect
already recorded against LrfPathExpander._contains_lrf_syntax. The check
now reduces each line to its LOGICAL BODY first, exactly as the main loop
already did.

CORRECTION 2 - "KEEP" DELETED THE STATEMENT
-------------------------------------------
``_keep`` emitted the audit marker as a comment AND the original statement
as a second comment, so a refused MODIFY / STORE was commented out rather
than left alone. A refusal must never remove executable code. The original
line is now re-emitted byte-for-byte beneath the marker.

CORRECTION 3 - COMMENT DETECTION ATE EXECUTABLE LINES
-----------------------------------------------------
The free-format fallback tested ``startswith(("*", "/", "D", "-"))``. The
D and - indicators are meaningful ONLY in column 7 of a fixed-format
record; applied to a stripped line they classify ``DISPLAY ...`` and
``-100`` as comments. Column 7 is now authoritative for fixed format, and
only ``*`` / ``/`` count in free format.

CORRECTION 4 - WHOLE-FILE LINE ENDINGS WERE REWRITTEN
-----------------------------------------------------
The emitter returned ``"\\n".join(output).rstrip() + "\\n"``, converting
CRLF to LF and dropping trailing blank lines across the ENTIRE file - a
diff far wider than the two lines actually touched, and enough to fail a
byte-identical regression gate. The dominant newline is preserved and the
trailing newline is reproduced only when the source had one.

CORRECTION 5 - UNMAPPED DIAGNOSTICS WERE DROPPED
------------------------------------------------
``_log`` looked the key up with ``.get(key, "")`` and returned silently
when the message was absent, so a diagnostic whose template was never
added produced NOTHING. An unmapped key is now reported as an unmapped
key, which is the difference between a visible gap and a lost finding.

CORRECTION 6 - A WRAPPED STATEMENT VANISHED
-------------------------------------------
``MODIFY <lr> WHERE <keyword> AND ...`` continued on the next line does
not match the single-line pattern, so it passed through unchanged and was
not even counted as skipped. It is now recognised as an update-verb line
the pass cannot handle, kept intact, and REPORTED.

NO-LRF CONTRACT
---------------
With no logical record metadata, or with metadata but no LRF update syntax
in the program, ``expand()`` returns the source text byte-for-byte. A
program that never used a logical record behaves exactly as before. The
three early exits return the ORIGINAL object, never a rejoined copy.

MODIFY vs STORE
---------------
MODIFY is the SQL UPDATE case. The element record to modify is the record
the path makes current with its last FIND / OBTAIN navigation command -
the only element the subschema parser captures for a MODIFY path-group -
so MODIFY is expanded whenever that record resolves and is mapped.

STORE is the SQL INSERT case. A STORE path-group usually seeds several
element records the subschema does not pin down, so guessing which one to
write is unsafe. STORE is expanded only for a single-element logical
record; otherwise it is kept, with a ``*DB2-KEEP:`` audit comment, for
manual review.

NAME FORM
---------
Generated names are COBOL form (UPPERCASE, hyphens). NameNormalizer is not
used here: normalize() yields the DB2 column form and would emit
VMBTL07_R01.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
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

# Independent kill switch for bisection. Falls back to the shared LRF
# switch so this module imports cleanly before the constant is added.
try:  # pragma: no cover - import-time fallback
    from rules.lrf_conversion_rules import ENABLE_LRF_UPDATE_EXPANSION
except ImportError:  # pragma: no cover
    ENABLE_LRF_UPDATE_EXPANSION = ENABLE_LRF_PATH_EXPANSION

PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"

# Valid column-7 indicators in a fixed-format record.
COMMENT_INDICATORS = ("*", "/", "D", "-")

# Indicators that mean "comment" in FREE format, where there is no
# column 7. D and - are deliberately absent: see CORRECTION 3.
FREE_FORMAT_COMMENT_PREFIXES = ("*", "/")

COMMENT_PREFIX_COLUMNS = "      "
DEFAULT_INDENT = "    "
SEQUENCE_AREA_WIDTH = 6
INDICATOR_COLUMN = 6  # zero-based index of column 7

VERB_MODIFY = "MODIFY"
VERB_STORE = "STORE"
UPDATE_VERBS = (VERB_MODIFY, VERB_STORE)
NAVIGATION_VERBS = ("FIND", "OBTAIN")
WHERE_TOKEN = "WHERE"

UNMAPPED_DIAGNOSTIC_TEMPLATE = (
    "LRF update expansion: unmapped diagnostic '{key}' {values}"
)
UNRENDERABLE_DIAGNOSTIC_TEMPLATE = (
    "LRF update expansion: diagnostic '{key}' could not be rendered ({error})."
)
UNTERMINATED_KEEP_TEMPLATE = (
    "DB2-KEEP: {verb} on a logical record continues past this line; "
    "the single-line form is the only one this pass expands."
)


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
        """Rewrite update-side LRF syntax. Byte-identical when nothing matches."""
        self.messages = []

        text = str(cobol_text or "")

        if not text.strip():
            return text

        if not (ENABLE_LRF_PATH_EXPANSION and ENABLE_LRF_UPDATE_EXPANSION):
            if self._contains_lr_update_syntax(text):
                self._log("disabled")
            return text

        if self.path_resolver is None or self._resolver_is_empty():
            if self._contains_lr_update_syntax(text):
                self._log("no_logical_records")
            return text

        if not self._contains_lr_update_syntax(text):
            return text

        newline = "\r\n" if "\r\n" in text else "\n"
        had_trailing_newline = text.endswith(("\n", "\r"))
        lines = text.splitlines()

        output: list[str] = []
        in_procedure = False
        expanded = 0
        skipped = 0

        for line in lines:
            logical = self._logical(line)

            if not in_procedure:
                output.append(line)
                if PROCEDURE_DIVISION_TOKEN in logical.upper():
                    in_procedure = True
                continue

            if self._is_comment(line) or not logical:
                output.append(line)
                continue

            match = LR_MODIFY_WHERE_PATTERN.match(logical)
            if match:
                rendered, ok = self._expand_update(line, match)
                output.extend(rendered)
                expanded += 1 if ok else 0
                skipped += 0 if ok else 1
                continue

            verb = self._unhandled_update_verb(logical)
            if verb:
                self._log("statement_unterminated", verb=verb)
                output.extend(
                    self._keep(
                        line, UNTERMINATED_KEEP_TEMPLATE.format(verb=verb)
                    )
                )
                skipped += 1
                continue

            output.append(line)

        if expanded or skipped:
            self._log("summary", expanded=expanded, skipped=skipped)
        else:
            # Nothing was touched: hand back the ORIGINAL object so no
            # newline or trailing-blank normalisation can leak into the diff.
            return text

        result = newline.join(output)
        if had_trailing_newline:
            result += newline
        return result

    # ------------------------------------------------------- expansion
    def _expand_update(self, line: str, match) -> tuple[list[str], bool]:
        verb = str(match.group("verb") or "").upper()
        lr_name = cobol_name(match.group("lr"))
        keyword = cobol_name(match.group("keyword"))

        path = self._lookup_path(keyword)
        if path is None:
            self._log("keyword_not_found", keyword=keyword)
            return (
                self._keep(
                    line, SKIPPED_NO_PATH_TEMPLATE.format(keyword=keyword)
                ),
                False,
            )

        if verb == VERB_STORE and self._store_is_ambiguous(path):
            self._log("store_ambiguous", keyword=keyword)
            return (
                self._keep(
                    line,
                    SKIPPED_STORE_AMBIGUOUS_TEMPLATE.format(keyword=keyword),
                ),
                False,
            )

        record = self._driving_record(path)
        if not record:
            self._log("no_record", keyword=keyword)
            return (
                self._keep(
                    line, SKIPPED_NO_RECORD_TEMPLATE.format(keyword=keyword)
                ),
                False,
            )

        if REQUIRE_MAPPED_DRIVING_RECORD and not self._record_is_mapped(record):
            self._log("record_unmapped", record=record, keyword=keyword)
            return (
                self._keep(
                    line, SKIPPED_UNMAPPED_TEMPLATE.format(record=record)
                ),
                False,
            )

        rendered = self._comment(
            line,
            EXPANDED_UPDATE_TEMPLATE.format(
                verb=verb, lr=lr_name, keyword=keyword, record=record
            ),
        )
        template = STORE_TEMPLATE if verb == VERB_STORE else MODIFY_TEMPLATE
        rendered.extend(
            self._statement(
                line,
                template.format(record=record),
                # match.string IS the logical line the pattern matched,
                # so the source terminator is available here.
                terminate=self._is_terminated(match.string),
            )
        )

        self._log(
            "expanded", verb=verb, lr=lr_name, keyword=keyword, record=record
        )
        return rendered, True

    # --------------------------------------------------- path analysis
    def _driving_record(self, path) -> str:
        """The element record the path makes current, in COBOL form.

        For a MODIFY / STORE path-group the record to write is the one the
        last FIND / OBTAIN navigation command establishes as current. The
        subschema parser does not retain the MODIFY / STORE verb line
        itself, so the navigation record is the reliable driving record.
        """
        record = ""
        for command in getattr(path, "commands", None) or []:
            verb = str(getattr(command, "verb", "") or "").upper()
            if verb in NAVIGATION_VERBS:
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

    def _resolver_is_empty(self) -> bool:
        try:
            return bool(self.path_resolver.is_empty())
        except Exception:  # noqa: BLE001
            return True

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
    def _statement(
        self,
        template_line: str,
        body: str,
        terminate: bool = True,
    ) -> list[str]:
        """Render one generated statement.

        ``terminate`` MIRRORS the source statement, for the same reason
        recorded in LrfPathExpander: a period closes the COBOL SENTENCE,
        so adding one to a statement that sits inside an inline block
        orphans the block's END- keyword and the program will not
        compile. Both current MODIFY / STORE forms are standalone and
        terminated, so this is a latent guard rather than a live fix.

        Defaults to True so any caller added later behaves as this method
        always did unless it opts in.
        """
        text = body.rstrip()
        if terminate and not text.endswith(STATEMENT_TERMINATOR):
            text = f"{text}{STATEMENT_TERMINATOR}"
        indent = self._body_indent(template_line)
        return self._emit(template_line, f"{indent}{text}", indicator=" ")
    
    def _comment(self, template_line: str, body: str) -> list[str]:
        """Comment body starts at column 8 - no indent, no leading star."""
        text = str(body or "").lstrip("*").strip()
        return self._emit(template_line, text, indicator="*")

    def _keep(self, line: str, marker: str) -> list[str]:
        """Audit marker, then the ORIGINAL statement, untouched.

        A refusal must never remove executable code. See CORRECTION 2.
        """
        rendered = self._comment(line, marker)
        rendered.append(line)
        return rendered

    def _emit(self, template_line: str, body: str, indicator: str) -> list[str]:
        if not self._is_fixed(template_line):
            if indicator == "*":
                return [f"{COMMENT_PREFIX_COLUMNS}*{body}"]
            return [body]

        try:
            left, _ind, _old, right = self.fixed_format.split(template_line)
            return self.fixed_format.emit(left, indicator, body, right)
        except Exception:  # noqa: BLE001
            return [template_line]

    @staticmethod
    def _is_terminated(text: str) -> bool:
        """True when the SOURCE statement ended in a period."""
        return str(text or "").rstrip().endswith(STATEMENT_TERMINATOR)
    # --------------------------------------------------------- helpers
    def _logical(self, line: str) -> str:
        """Columns 8-72 of a fixed record, or the stripped line."""
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

    def _is_comment(self, line: str) -> bool:
        """Column 7 decides in fixed format; only * and / in free format."""
        text = str(line or "")

        if self._is_fixed(text):
            return (
                len(text) > INDICATOR_COLUMN
                and text[INDICATOR_COLUMN] in COMMENT_INDICATORS
            )

        # Secondary guard: a record whose sequence area is blank or numeric
        # is still fixed format even when the service does not say so.
        if len(text) > INDICATOR_COLUMN:
            sequence = text[:SEQUENCE_AREA_WIDTH].strip()
            if (not sequence) or sequence.isdigit():
                if text[INDICATOR_COLUMN] in COMMENT_INDICATORS:
                    return True

        return text.lstrip().startswith(FREE_FORMAT_COMMENT_PREFIXES)

    def _contains_lr_update_syntax(self, text: str) -> bool:
        """True when any LOGICAL line carries update-side LRF syntax.

        Reads the logical body, never the raw record. See CORRECTION 1.
        """
        for raw_line in str(text or "").splitlines():
            if self._is_comment(raw_line):
                continue
            logical = self._logical(raw_line)
            if not logical:
                continue
            if LR_MODIFY_WHERE_PATTERN.match(logical):
                return True
            if self._unhandled_update_verb(logical):
                return True
        return False

    @staticmethod
    def _unhandled_update_verb(logical: str) -> str:
        """The verb of an update-side LR line the single-line pattern missed.

        Returns "" for anything that is not ``MODIFY``/``STORE`` followed by
        a ``WHERE``. No regex: the authoritative pattern lives in patterns/.
        """
        tokens = str(logical or "").upper().split()
        if len(tokens) < 3:
            return ""
        if tokens[0] not in UPDATE_VERBS:
            return ""
        if WHERE_TOKEN not in tokens[1:]:
            return ""
        return tokens[0]

    def _log(self, key: str, **values) -> None:
        """Record one diagnostic. An unmapped key is REPORTED, not dropped."""
        template = LRF_UPDATE_MESSAGES.get(key, "")

        if not template:
            rendered = " ".join(
                f"{name}={value}" for name, value in sorted(values.items())
            )
            self.messages.append(
                UNMAPPED_DIAGNOSTIC_TEMPLATE.format(key=key, values=rendered)
            )
            return

        try:
            self.messages.append(template.format(**values))
        except (KeyError, IndexError, ValueError) as error:
            self.messages.append(
                UNRENDERABLE_DIAGNOSTIC_TEMPLATE.format(key=key, error=error)
            )


__all__ = ["LrfUpdateExpander", "cobol_name"]
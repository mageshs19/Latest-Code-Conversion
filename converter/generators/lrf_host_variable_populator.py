# LOCATION: converter/generators/lrf_host_variable_populator.py
# ACTION: REPLACE ENTIRE FILE
"""Generates host-variable population code for LRF-expanded cursors.

WHAT THIS PASS DOES

An LRF-expanded cursor that declares a WHERE clause takes a parameter.
That parameter must be loaded into the DCLGEN host group BEFORE OPEN, or
the cursor filters on spaces or zeroes. This pass finds the LRF expansion
marker, reads the cursor's OWN predicate, and emits INITIALIZE plus MOVE
statements ahead of the PERFORM of the OPEN paragraph.

WHAT THIS PASS DELIBERATELY DOES NOT DO

It does not INVENT a predicate. A cursor with no WHERE clause takes no
parameter and there is nothing to load. That is a CORRECT outcome and it
is reported, not silently skipped. Turning a COBOL IF into a cursor
predicate is predicate pushdown: a different capability, a different
owner, and an open question with the COBOL team.

CORRECTION 1 - THE MARKER PATTERN WAS A PRIVATE COPY, AND IT WAS WRONG

This module defined LRF_EXPANSION_MARKER_PATTERN itself, anchored on the
comment indicator:

    r"\\*DB2:\\s+Expanded\\s+LRF\\s+"

The indicator occupies column 7, OUTSIDE the logical body (columns
8-72). Matched against a stripped body the anchor can never fire, so the
pass reported 'no_lrf_markers' on every program while a correct,
well-formed marker sat in the generated file.

The capture groups were also inverted. Against the real marker

    *DB2: Expanded LRF FIRST <logical-record> WHERE <keyword> -> <record>

the group named 'keyword' captured the LOGICAL RECORD name and the group
named 'parent' captured the PATH KEYWORD.

CORRECTION 2 - A PATH NEED NOT HAVE A PARENT

The private pattern REQUIRED a parent. A path keyword that resolves
WITHIN an AREA is an unqualified sweep: no parent record, no set. A
pattern demanding a parent can never serve a sweep path, which is the
shape every current program uses. Parent, set and area now come from the
parsed subschema, which knows the difference.

CORRECTION 3 - THE REPOSITORY LOOKUP HAD THE WRONG ARITY

LrfRepository.path_for_keyword takes ONE argument, the keyword. The
first fix called it with two and would have raised TypeError on the
first marker. The call is now arity-probed.

CORRECTION 4 - GENERATED LINES WERE NOT FIXED-FORMAT RECORDS

Emitted lines placed the comment indicator in column 1 and carried no
sequence areas, breaking the 80-column layout on every CHK-01 criterion.
Every generated line is now rendered as a proper record: sequence areas
borrowed from the line it precedes, indicator in column 7, body padded
to 65 columns, width-checked. A line that will not fit causes the WHOLE
block to be refused and reported - truncation produces an undefined data
name that does not compile.

CORRECTION 5 - ONE MESSAGE STYLE

The pass mixed opaque tokens ('host_group_not_found') with formatted
sentences. Every diagnostic now resolves through
rules/lrf_populator_rules.LRF_POPULATOR_MESSAGES by key.

Regex lives in patterns/cursor_spec/lrf_comment_patterns.py; constants
and diagnostics in rules/lrf_populator_rules.py. No program, paragraph,
record, table, DCLGEN, cursor or host-variable name is hardcoded here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.cursor_spec.lrf_comment_patterns import (
    LRF_CONTINUATION_RECORD_PATTERN,
    LRF_EXPANSION_PATTERN,
    LRF_EXPANSION_WRAPPED_PATTERN,
    LRF_CONTINUATION_ARROW_PATTERN,
    LRF_EXPANSION_WRAPPED_NO_ARROW_PATTERN,
)
from rules.lrf_populator_rules import (
    ALLOW_AREA_SWEEP_PATHS,
    ENABLE_LRF_HOST_POPULATION,
    ENFORCE_LRF_BODY_WIDTH,
    LRF_AREA_NAME_PREFIXES,
    LRF_BLANK_INDICATOR,
    LRF_BODY_WIDTH,
    LRF_COMMAND_RECORD_ATTRIBUTES,
    LRF_COMMAND_WITHIN_ATTRIBUTES,
    LRF_COMMENT_INDENT,
    LRF_COMMENT_INDICATOR,
    LRF_LEFT_SEQUENCE_WIDTH,
    LRF_PATH_COMMAND_ATTRIBUTES,
    LRF_POPULATOR_MESSAGES,
    LRF_RIGHT_SEQUENCE_WIDTH,
    LRF_STATEMENT_INDENT,
    REFUSE_ON_UNRESOLVED_PATH,
    LRF_CURSOR_BY_RECORD_METHODS,
    LRF_CURSOR_BY_TABLE_METHODS,
    LRF_TABLE_BY_RECORD_METHODS,
    LRF_HOST_GROUP_BY_TABLE_METHODS
)

# ---------------------------------------------------------------------
# The LRF marker format has ONE owner:
#     patterns/cursor_spec/lrf_comment_patterns.py
# Re-exported so existing importers keep working. Never re-assigned,
# never redefined here. See CORRECTION 1 above.
# ---------------------------------------------------------------------
LRF_EXPANSION_MARKER_PATTERN = LRF_EXPANSION_PATTERN

# Cheap literal probe. When a line clearly carries a marker but the
# shared pattern does not match it, say so loudly instead of skipping.
_MARKER_PROBE = "EXPANDED LRF"

# PERFORM <nnn>-OPEN-<cursor>.   Matched against a logical body.
PERFORM_OPEN_PATTERN = re.compile(
    r"^PERFORM\s+\d+-OPEN-(?P<cursor>[\w\-]+)\s*\.?$",
    re.IGNORECASE,
)

# DECLARE <cursor> CURSOR        Matched against a logical body.
CURSOR_DECLARE_TEMPLATE = r"\bDECLARE\s+{cursor}\s+CURSOR\b"

# Column reference on the left of a comparison inside a WHERE clause.
WHERE_COLUMN_PATTERN = re.compile(
    r"(?P<column>[A-Za-z][\w\-]*)\s*(?:<=|>=|<>|!=|[<>=])"
)

# Words that may stand to the left of an operator but are not columns.
_NON_COLUMN_WORDS = frozenset(
    {"AND", "OR", "NOT", "WHERE", "ON", "BY", "FETCH", "ONLY", "WITH"}
)

_DECLARE_SCAN_LIMIT = 200
_PERFORM_SCAN_LIMIT = 50
_CONTINUATION_SCAN_LIMIT = 3


# =====================================================================
# Value objects
# =====================================================================


@dataclass
class LrfPathFacts:
    """What the parsed subschema says about one LRF path keyword."""

    target_record: str = ""
    set_name: str = ""
    area_name: str = ""
    parent_record: str = ""
    container: str = ""
    resolved: bool = False
    source: str = "marker"  # "subschema" or "marker"

    @property
    def is_area_sweep(self) -> bool:
        return bool(self.area_name) and not self.set_name


@dataclass
class LrfExpansionMarker:
    """Metadata extracted from one LRF expansion comment."""

    mode: str = ""              # FIRST or NEXT
    logical_record: str = ""    # logical record named in the marker
    keyword: str = ""           # LRF path keyword
    parent_record: str = ""     # from the subschema; "" for a sweep
    target_record: str = ""     # record the cursor reads
    set_name: str = ""          # from the subschema; "" for a sweep
    area_name: str = ""         # from the subschema; "" for a join
    cursor_name: str = ""       # derived cursor name
    line_index: int = 0         # 0-based position of the marker

    @property
    def is_area_sweep(self) -> bool:
        return bool(self.area_name) and not self.set_name

    @property
    def record_name_display(self) -> str:
        """Target record in COBOL form, for diagnostics."""
        return str(self.target_record or "").upper().replace("_", "-")


@dataclass
class LrfHostVariableInitSequence:
    """Generated initialisation code for one LRF cursor."""

    cursor_name: str = ""
    host_group_name: str = ""
    initialization_lines: list[str] = field(default_factory=list)


# =====================================================================
# Populator
# =====================================================================


class LrfHostVariablePopulator:
    """Injects host-variable population code ahead of an LRF cursor OPEN."""

# FILE: converter/generators/lrf_host_variable_populator.py
# ACTION: REPLACE the __init__ method of LrfHostVariablePopulator.
#         It sits immediately above augment_procedure_division (line 257).

    def __init__(
        self,
        host_variable_resolver=None,
        relationship_resolver=None,
        name_normalizer=None,
        cursor_name_resolver=None,
        table_name_resolver=None, 
        lrf_path_resolver=None,
        lrf_repository=None,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.host_variable_resolver = host_variable_resolver
        self.relationship_resolver = relationship_resolver
        self.name_normalizer = name_normalizer
        self.cursor_name_resolver = cursor_name_resolver
        self.table_name_resolver = table_name_resolver  

        # LrfPathResolver is the permanent owner of path-keyword
        # resolution. lrf_repository is TRANSITIONAL and is deleted once
        # _path_facts consumes LrfAccessPlan.
        self.lrf_path_resolver = lrf_path_resolver
        self.lrf_repository = lrf_repository

        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []
        self._repository_reported = False
    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def augment_procedure_division(
        self,
        cobol_text: str,
    ) -> tuple[str, list[str]]:
        """Scan the program for LRF markers and inject host population.

        Returns (modified_cobol, messages). The text is returned
        unchanged whenever nothing can be generated safely.
        """
        self.messages = []
        self._repository_reported = False
        text = str(cobol_text or "")

        if not ENABLE_LRF_HOST_POPULATION:
            self._log("disabled")
            return text, self.messages

        if not text:
            self._log("empty_program")
            return text, self.messages

        # split/join on "\n" so a CRLF file round-trips byte for byte.
        lines = text.split("\n")

        markers = self._extract_lrf_markers(lines)
        if not markers:
            return text, self.messages

        injection_points: dict[int, list[str]] = {}
        injected_cursors = 0
        injected_lines = 0

        for marker in markers:
            perform_index = self._find_perform_open_after(marker, lines)
            if perform_index is None:
                self._log(
                    "perform_open_not_found",
                    cursor=marker.cursor_name,
                )
                continue

            sequence = self._build_init_sequence(
                marker, lines, lines[perform_index]
            )
            if sequence is None or not sequence.initialization_lines:
                continue

            injection_points.setdefault(perform_index, []).extend(
                sequence.initialization_lines
            )
            injected_cursors += 1
            injected_lines += len(sequence.initialization_lines)

            self._log(
                "injection_planned",
                cursor=marker.cursor_name,
                count=len(sequence.initialization_lines),
            )

        if not injection_points:
            return text, self.messages

        modified = self._inject_code(lines, injection_points)

        self._log(
            "injection_summary",
            cursors=injected_cursors,
            lines=injected_lines,
        )

        return "\n".join(modified), self.messages

    # ------------------------------------------------------------------
    # Private: fixed-format access
    # ------------------------------------------------------------------

    def _logical_body(self, line: str) -> str:
        """Columns 8-72 of a fixed-format record, indicator removed.

        Accepts a raw 80-column record OR an already-stripped body, so
        the pass is correct wherever it is wired. The shared marker
        patterns match a BODY and never anchor on the indicator column.
        """
        try:
            body = self.fixed_format.logical(line)
            if body:
                return str(body)
        except Exception:  # noqa: BLE001 - one odd line must not abort
            pass

        text = str(line or "").rstrip("\r\n")
        if len(text) >= 72 and text[:6].strip().isdigit():
            return text[7:72]
        return text

    def _sequence_areas(self, template: str) -> tuple[str, str]:
        """(left, right) sequence areas borrowed from a template line.

        FinalSequenceResequencerService rewrites columns 1-6 and 73-80
        afterwards, so borrowed numbers are placeholders.
        """
        try:
            parsed = self.fixed_format.parse_line(template)
            if parsed and parsed.get("is_fixed_format"):
                return (
                    str(parsed.get("left_sequence", "")),
                    str(parsed.get("right_sequence", "")),
                )
        except Exception:  # noqa: BLE001
            pass

        text = str(template or "").rstrip("\r\n")
        left = text[:6] if len(text) >= 6 and text[:6].isdigit() else ""
        right = text[72:80] if len(text) >= 80 else ""
        return left, right

    def _render(
        self,
        body: str,
        indicator: str,
        template: str,
    ) -> Optional[str]:
        """Build one 80-column record, or None when the body will not fit.

        Layout: left(6) + indicator(1) + body(65) + right(8) = 80.
        """
        clean = str(body or "").rstrip()
        if ENFORCE_LRF_BODY_WIDTH and len(clean) > LRF_BODY_WIDTH:
            return None

        left, right = self._sequence_areas(template)
        left = left.ljust(LRF_LEFT_SEQUENCE_WIDTH)[:LRF_LEFT_SEQUENCE_WIDTH]
        right = right.ljust(LRF_RIGHT_SEQUENCE_WIDTH)[
            :LRF_RIGHT_SEQUENCE_WIDTH
        ]
        mark = (indicator or LRF_BLANK_INDICATOR)[:1]

        return f"{left}{mark}{clean.ljust(LRF_BODY_WIDTH)}{right}"

    # ------------------------------------------------------------------
    # Private: subschema path resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _first_attribute(obj, names) -> str:
        for name in names:
            value = getattr(obj, name, None)
            if value:
                return str(value).strip()
        return ""

    def _path_commands(self, path) -> list:
        for name in LRF_PATH_COMMAND_ATTRIBUTES:
            commands = getattr(path, name, None)
            if commands:
                return list(commands)
        return []

    def _lookup_path(self, logical_record: str, keyword: str):
        """Call the repository, probing its arity.

        LrfRepository.path_for_keyword takes ONE argument. A local build
        may take two. Probe rather than assume - the wrong arity raises
        TypeError on the first marker.
        """
        repository = getattr(self, "lrf_repository", None)
        if repository is None:
            repository = getattr(
                getattr(self, "lrf_path_resolver", None),
                "lrf_repository",
                None,
            )

        finder = getattr(repository, "path_for_keyword", None)
        if finder is None:
            if not self._repository_reported:
                self._log("no_lrf_repository")
                self._repository_reported = True
            return None

        try:
            return finder(keyword)
        except TypeError:
            pass

        try:
            return finder(logical_record, keyword)
        except Exception as error:  # noqa: BLE001
            self._log(
                "path_lookup_failed",
                keyword=keyword,
                reason=type(error).__name__,
            )
            return None

    def _path_facts(
        self,
        logical_record: str,
        keyword: str,
        fallback_record: str,
    ) -> LrfPathFacts:
        """Resolve a path keyword against the parsed subschema.

        The marker supplies the target record reliably; everything else
        belongs to the subschema and is never inferred from the comment.
        """
        path = self._lookup_path(logical_record, keyword)
        if path is None:
            return LrfPathFacts(
                target_record=fallback_record,
                resolved=False,
                source="marker",
            )

        commands = self._path_commands(path)
        if not commands:
            self._log("path_fields_unknown", keyword=keyword)
            return LrfPathFacts(
                target_record=fallback_record,
                resolved=False,
                source="marker",
            )

        # The LAST navigation command names the record the cursor reads.
        # Any EARLIER command names the parent it navigates from.
        last = commands[-1]
        target = self._first_attribute(last, LRF_COMMAND_RECORD_ATTRIBUTES)
        container = self._first_attribute(last, LRF_COMMAND_WITHIN_ATTRIBUTES)

        parent = ""
        if len(commands) > 1:
            parent = self._first_attribute(
                commands[0], LRF_COMMAND_RECORD_ATTRIBUTES
            )

        if not target and not container:
            self._log("path_fields_unknown", keyword=keyword)
            return LrfPathFacts(
                target_record=fallback_record,
                resolved=False,
                source="marker",
            )

        target = target or fallback_record
        upper = container.upper()
        is_area = any(
            upper.startswith(prefix) for prefix in LRF_AREA_NAME_PREFIXES
        )

        return LrfPathFacts(
            target_record=target,
            set_name="" if is_area else container,
            area_name=container if is_area else "",
            parent_record="" if is_area else parent,
            container=container,
            resolved=True,
            source="subschema",
        )

    # ------------------------------------------------------------------
    # Private: LRF marker extraction
    # ------------------------------------------------------------------

    def _continuation_record(self, lines: list[str], index: int) -> str:
        """Record name opening the body after a wrapped marker."""
        limit = min(index + 1 + _CONTINUATION_SCAN_LIMIT, len(lines))
        for offset in range(index + 1, limit):
            body = self._logical_body(lines[offset]).strip()
            if not body:
                continue
            match = LRF_CONTINUATION_ARROW_PATTERN.match(body)
            if match:
                return match.group("record")

            match = LRF_CONTINUATION_RECORD_PATTERN.match(body)
            if match:
                return match.group("record")
            break
        return ""

    def _extract_lrf_markers(
        self,
        lines: list[str],
    ) -> list[LrfExpansionMarker]:
        """Find every LRF expansion marker and bind it to a cursor.

        Every outcome is reported. A marker that cannot be resolved is
        REFUSED and named, never skipped in silence.
        """
        markers: list[LrfExpansionMarker] = []
        examined = 0
        refused = 0

        for index, line in enumerate(lines):
            body = self._logical_body(line)
            if not body.strip():
                continue

            match = LRF_EXPANSION_PATTERN.search(body)
            marker_record = ""

            if match is not None:
                marker_record = match.group("record")
            else:
                match = LRF_EXPANSION_WRAPPED_PATTERN.search(body)
                if match is None:
                    # Second legal wrap point: the arrow opens line 2.
                    match = LRF_EXPANSION_WRAPPED_NO_ARROW_PATTERN.search(
                        body
                    )
                if match is None:
                    if _MARKER_PROBE in body.upper():
                        self._log("marker_unreadable", line=index + 1)
                    continue

                marker_record = self._continuation_record(lines, index)
                if not marker_record:
                    refused += 1
                    self._log("continuation_missing", line=index + 1)
                    continue

            examined += 1
            logical_record = str(match.group("subschema"))
            keyword = str(match.group("sweep"))

            facts = self._path_facts(logical_record, keyword, marker_record)

            if not facts.resolved and REFUSE_ON_UNRESOLVED_PATH:
                refused += 1
                self._log(
                    "path_unresolved",
                    keyword=keyword,
                    record=logical_record,
                )
                continue

            if facts.set_name:
                self._log(
                    "set_resolved",
                    keyword=keyword,
                    record=facts.target_record,
                    set_name=facts.set_name,
                    parent=facts.parent_record or "none",
                )
            elif facts.area_name:
                if not ALLOW_AREA_SWEEP_PATHS:
                    refused += 1
                    continue
                self._log(
                    "area_sweep",
                    keyword=keyword,
                    area=facts.area_name,
                )
            elif facts.container:
                self._log(
                    "container_unclassified",
                    keyword=keyword,
                    record=facts.target_record,
                    container=facts.container,
                )

            cursor_name = self._cursor_name_for_record(
                facts.target_record, index
            )
            if not cursor_name:
                refused += 1
                continue

            markers.append(
                LrfExpansionMarker(
                    mode=str(match.group("mode")).upper(),
                    logical_record=logical_record.upper(),
                    keyword=keyword.upper(),
                    parent_record=facts.parent_record,
                    target_record=facts.target_record,
                    set_name=facts.set_name,
                    area_name=facts.area_name,
                    cursor_name=cursor_name,
                    line_index=index,
                )
            )

        if not examined:
            self._log("no_markers")
        else:
            self._log(
                "scan_summary",
                examined=examined,
                bound=len(markers),
                refused=refused,
            )

        return markers

    # ------------------------------------------------------------------
    # Private: initialisation code generation
    # ------------------------------------------------------------------

    def _build_init_sequence(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
        template: str,
    ) -> Optional[LrfHostVariableInitSequence]:
        """Generate the INITIALIZE and MOVE block for one cursor."""
        if not self.host_variable_resolver:
            self._log("no_host_variable_resolver")
            return None

        host_group = self._host_group_for_marker(marker)
        if not host_group:
            self._log("host_group_not_found", cursor=marker.cursor_name)
            return None

        key_columns = self._predicate_columns(marker, lines)
        if key_columns is None:
            return None

        if not key_columns:
            # A cursor with no predicate takes no parameter. Correct, and
            # reported. Creating a predicate is predicate pushdown and is
            # NOT this pass's job.
            self._log("no_predicate", cursor=marker.cursor_name)
            return None

        if not self._record_is_declared(marker.parent_record, lines):
            self._log(
                "parent_not_declared",
                cursor=marker.cursor_name,
                record=marker.parent_record,
            )
            return None

        bodies: list[str] = [
            f"{LRF_COMMENT_INDENT}LRF host variables for cursor "
            f"{marker.cursor_name}",
            f"{LRF_STATEMENT_INDENT}INITIALIZE {host_group}.",
        ]
        indicators: list[str] = [
            LRF_COMMENT_INDICATOR,
            LRF_BLANK_INDICATOR,
        ]

        moves = 0
        for column in key_columns:
            host_field = self._normalize_host_field(column)
            bodies.append(
                f"{LRF_STATEMENT_INDENT}MOVE {host_field} OF "
                f"{marker.parent_record}"
            )
            indicators.append(LRF_BLANK_INDICATOR)
            bodies.append(
                f"{LRF_STATEMENT_INDENT}  TO {host_field} OF {host_group}."
            )
            indicators.append(LRF_BLANK_INDICATOR)
            moves += 1

        rendered: list[str] = []
        for body, indicator in zip(bodies, indicators):
            line = self._render(body, indicator, template)
            if line is None:
                self._log(
                    "geometry_refused",
                    cursor=marker.cursor_name,
                    width=len(body),
                    limit=LRF_BODY_WIDTH,
                    body=body[:40],
                )
                return None
            rendered.append(line)

        self._log(
            "populated",
            cursor=marker.cursor_name,
            group=host_group,
            moves=moves,
        )

        return LrfHostVariableInitSequence(
            cursor_name=marker.cursor_name,
            host_group_name=host_group,
            initialization_lines=rendered,
        )

    def _host_group_for_marker(self, marker: LrfExpansionMarker) -> str:
        """DCLGEN host group for the cursor's table.

        HostVariableResolver answers on a TABLE (group_for_table), never
        on a cursor name. The record must therefore be mapped first -
        the same record -> table route _cursor_name_for_record uses.
        """
        table = self._try_resolver(
            self.table_name_resolver,
            LRF_TABLE_BY_RECORD_METHODS,
            marker.target_record,
        )
        if not table:
            return ""

        return self._try_resolver(
            self.host_variable_resolver,
            LRF_HOST_GROUP_BY_TABLE_METHODS,
            table,
        )

    def _record_is_declared(self, record: str, lines: list[str]) -> bool:
        """True when the converted program still declares this record.

        The converter replaces IDMS record layouts with DCLGEN groups.
        A MOVE whose SOURCE is a record that no longer exists does not
        compile, so the parent must be verified before any MOVE is
        generated.
        """
        target = str(record or "").strip().upper()
        if not target:
            return False

        pattern = re.compile(rf"^\d\d\s+{re.escape(target)}\b", re.IGNORECASE)
        for line in lines:
            if pattern.match(self._logical_body(line).strip()):
                return True
        return False

    def _predicate_columns(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
    ) -> Optional[list[str]]:
        """Column names in the cursor's own WHERE clause, in order.

        Returns None when the DECLARE cannot be found at all, and an
        empty list when the cursor simply declares no predicate.
        """
        declare_index = self._find_cursor_declare(marker.cursor_name, lines)
        if declare_index is None:
            self._log(
                "cursor_declare_not_found",
                cursor=marker.cursor_name,
            )
            return None

        assembled = self._assemble_declare(declare_index, lines)
        upper = assembled.upper()
        position = upper.find(" WHERE ")
        if position < 0:
            return []

        where_clause = assembled[position + len(" WHERE "):]

        ordered: list[str] = []
        seen: set[str] = set()
        for match in WHERE_COLUMN_PATTERN.finditer(where_clause):
            column = match.group("column")
            key = column.upper()
            if key in _NON_COLUMN_WORDS or key in seen:
                continue
            seen.add(key)
            ordered.append(column)

        return ordered

    def _find_cursor_declare(
        self,
        cursor_name: str,
        lines: list[str],
    ) -> Optional[int]:
        """Line index of the DECLARE statement for this cursor."""
        pattern = re.compile(
            CURSOR_DECLARE_TEMPLATE.format(cursor=re.escape(cursor_name)),
            re.IGNORECASE,
        )
        for index, line in enumerate(lines):
            if pattern.search(self._logical_body(line)):
                return index
        return None

    def _assemble_declare(
        self,
        start_index: int,
        lines: list[str],
    ) -> str:
        """Join the DECLARE statement from its logical bodies."""
        parts: list[str] = []
        limit = min(start_index + _DECLARE_SCAN_LIMIT, len(lines))

        for index in range(start_index, limit):
            body = self._logical_body(lines[index]).strip()
            if not body:
                continue
            parts.append(body)
            if body.upper().endswith("END-EXEC") or body.endswith("."):
                break

        return " " + " ".join(parts) + " "

    # ------------------------------------------------------------------
    # Private: PERFORM OPEN location
    # ------------------------------------------------------------------

# FILE: converter/generators/lrf_host_variable_populator.py
# ACTION: The previous block ended mid-line at
#             limit = min(start + _PERFOR
#         DELETE that partial line, then paste everything below as the
#         remainder of the file. Nothing after this point exists yet.

    # ------------------------------------------------------------------
    # Private: PERFORM OPEN location
    # ------------------------------------------------------------------

    def _find_perform_open_after(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
    ) -> Optional[int]:
        """Index of 'PERFORM <nnn>-OPEN-<cursor>.' for this marker.

        A cursor is OPENed exactly once, normally in the mainline, which
        commonly sits BEFORE the OBTAIN that produced the marker. The
        first version searched forward only and therefore never found
        it. The whole program is scanned; a PERFORM that precedes the
        marker is accepted and REPORTED.
        """
        wanted = str(marker.cursor_name or "").strip().upper()
        if not wanted:
            return None

        matches: list[int] = []
        for index, line in enumerate(lines):
            body = self._logical_body(line).strip()
            if not body:
                continue
            match = PERFORM_OPEN_PATTERN.match(body)
            if match is None:
                continue
            if match.group("cursor").strip().upper() == wanted:
                matches.append(index)

        if not matches:
            return None

        after = [index for index in matches if index > marker.line_index]
        if after:
            return after[0]

        self._log(
            "perform_open_before_marker",
            cursor=marker.cursor_name,
            line=matches[0] + 1,
        )
        return matches[0]
    # ------------------------------------------------------------------
    # Private: code injection
    # ------------------------------------------------------------------

    @staticmethod
    def _inject_code(
        lines: list[str],
        injection_points: dict[int, list[str]],
    ) -> list[str]:
        """Insert generated records before each PERFORM OPEN line.

        Processed in DESCENDING index order so an earlier insertion can
        never shift a later target index.
        """
        result = list(lines)

        for index in sorted(injection_points.keys(), reverse=True):
            block = injection_points[index]
            if not block:
                continue
            result[index:index] = list(block)

        return result

    # ------------------------------------------------------------------
    # Private: name resolution
    # ------------------------------------------------------------------

    def _try_resolver(self, resolver, method_names, argument: str) -> str:
        """First method that answers wins. A missing name is not an error."""
        if resolver is None or not argument:
            return ""
        for name in method_names:
            finder = getattr(resolver, name, None)
            if finder is None:
                continue
            try:
                value = finder(argument)
            except Exception:  # noqa: BLE001
                continue
            text = str(value or "").strip()
            if text:
                return text
        return ""

    def _cursor_name_for_record(
        self,
        record_name: str,
        line_index: int,
    ) -> str:
        """Generated cursor name for an IDMS record, or "".

        Three routes, in order of authority. CursorNameResolver names a
        cursor from a TABLE, so a record must be mapped first - that is
        why table_name_resolver is required here and was previously
        accepted by setup and discarded.
        """
        record = str(record_name or "").strip()
        if not record:
            return ""

        # A missing resolver and a record with no cursor are different
        # facts. Reporting both as "no generated cursor" is how the
        # table_name_resolver discard stayed invisible.
        if self.cursor_name_resolver is None and self.table_name_resolver is None:
            self._log(
                "cursor_lookup_failed",
                record=record,
                reason="no cursor or table resolver was supplied",
                line=line_index + 1,
            )
            return ""

        cursor = self._try_resolver(
            self.cursor_name_resolver, LRF_CURSOR_BY_RECORD_METHODS, record
        )
        if cursor:
            return cursor

        table = self._try_resolver(
            self.table_name_resolver, LRF_TABLE_BY_RECORD_METHODS, record
        )
        if table:
            cursor = self._try_resolver(
                self.cursor_name_resolver, LRF_CURSOR_BY_TABLE_METHODS, table
            )
            if cursor:
                return cursor

        cursor = self._try_resolver(
            self.host_variable_resolver, LRF_CURSOR_BY_RECORD_METHODS, record
        )
        if cursor:
            return cursor

        self._log("no_cursor_for_record", record=record, line=line_index + 1)
        return ""
    
    def _normalize_host_field(self, field_name: str) -> str:
        """COBOL form of a DB2 column name.

        DB2 columns use underscores, COBOL data names use hyphens. The
        injected NameNormalizer is preferred when one was supplied, so
        the site convention stays in one place.
        """
        text = str(field_name or "").strip()
        if not text:
            return ""

        normalizer = self.name_normalizer
        if normalizer is not None:
            converter = getattr(normalizer, "to_cobol_name", None)
            if converter is not None:
                try:
                    converted = str(converter(text) or "").strip()
                    if converted:
                        return converted.upper()
                except Exception:  # noqa: BLE001
                    pass

        return text.upper().replace("_", "-")

    # ------------------------------------------------------------------
    # Private: diagnostics
    # ------------------------------------------------------------------

    def _log(self, key: str, **values) -> None:
        """Append one diagnostic sentence.

        ONE message style. Every key resolves through
        rules/lrf_populator_rules.LRF_POPULATOR_MESSAGES. An unknown key
        or a bad placeholder is still reported rather than discarded -
        losing a diagnostic is worse than printing an ugly one.
        """
        name = str(key or "").strip()
        template = LRF_POPULATOR_MESSAGES.get(name, "")

        if not template:
            detail = " ".join(f"{k}={v}" for k, v in sorted(values.items()))
            self.messages.append(
                f"LRF populator: unmapped diagnostic '{name}' {detail}".rstrip()
            )
            return

        try:
            self.messages.append(template.format(**values))
        except (KeyError, IndexError, ValueError):
            detail = " ".join(f"{k}={v}" for k, v in sorted(values.items()))
            self.messages.append(f"{template} [{detail}]".rstrip())


__all__ = [
    "LRF_EXPANSION_MARKER_PATTERN",
    "LrfExpansionMarker",
    "LrfHostVariableInitSequence",
    "LrfHostVariablePopulator",
    "LrfPathFacts",
]
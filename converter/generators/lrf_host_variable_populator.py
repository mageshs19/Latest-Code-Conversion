# LOCATION: converter/generators/lrf_host_variable_populator.py
# ACTION: CREATE NEW FILE
"""Generates host variable population code for LRF-expanded cursors.

PROBLEM
-------
When LRF path expansion converts "OBTAIN WHERE <keyword>" to classic IDMS,
the transformer loses the data flow context. The cursor is opened with empty
host variables, so WHERE clauses filter incorrectly.

Example from VM7BD200:
  *DB2: Expanded LRF FIRST VMBTL03-R01 WHERE SWEEP-VMBFAS -> VMBFAS
    PERFORM 710-OPEN-DZBFASC1.

The VMBFAS cursor's WHERE clause references parent archive dates, but
DCLDZBFASTV host variables are never populated.

SOLUTION
--------
This module:
1. Scans generated COBOL for "*DB2: Expanded LRF" markers
2. Extracts LRF metadata (keyword, parent record, target record)
3. Generates MOVE statements to populate host variables from parent record
4. Inserts code before PERFORM OPEN-<cursor>

GENERATED CODE PATTERN
----------------------
For cursor DZBFASC1 with parent VMBFAS:

    INITIALIZE DCLDZBFASTV.
    MOVE DA-ARCH-YMD OF VMDZ270I-REC TO DA-CCYYMMDD.
    MOVE CORR DA-CCYYMMDD-R    TO DA-DD-MM-CCYY.
    MOVE DA-DD-MM-CCYY         TO WS-DA-ARCH-YMD.
    MOVE WS-DA-ARCH-YMD        TO DA-CPTAFS-479BFAS OF DCLDZBFASTV.
    MOVE WS-DA-ARCH-YMD        TO DA-CRFMAS-479BFAS OF DCLDZBFASTV.
    PERFORM 710-OPEN-DZBFASC1.

MAPPING DATA FLOW
-----------------
Host variable population needs to bridge IDMS parent record data to
DB2 host group fields. This requires:

1. Parent record field names (from LRF metadata)
2. Host group structure (from DCLGEN)
3. Data mapping (which parent fields -> which host fields)

Current implementation reconstructs the data flow from:
- LRF expansion comment markers
- Relationship metadata in path resolver
- DCLGEN-derived host variable structure
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Match: *DB2: Expanded LRF <mode> <keyword> WHERE <parent> -> <record>
LRF_EXPANSION_MARKER_PATTERN = re.compile(
    r"\*DB2:\s+Expanded\s+LRF\s+"
    r"(?P<mode>FIRST|NEXT)\s+"
    r"(?P<keyword>[\w\-]+)\s+"
    r"WHERE\s+"
    r"(?P<parent>[\w\-]+)\s+"
    r"->\s+"
    r"(?P<record>[\w\-]+)",
    re.IGNORECASE,
)

# Match: PERFORM nnn-OPEN-<cursor>
PERFORM_OPEN_PATTERN = re.compile(
    r"^\s*PERFORM\s+\d+-OPEN-(?P<cursor>[\w\-]+)\s*\.",
    re.IGNORECASE | re.MULTILINE,
)

# Match: MOVE ... TO <field> OF <group>.
MOVE_STATEMENT_PATTERN = re.compile(
    r"^\s*MOVE\s+.+\s+TO\s+(?P<field>[\w\-]+)\s+OF\s+(?P<group>[\w\-]+)\s*\.",
    re.IGNORECASE,
)


@dataclass
class LrfExpansionMarker:
    """Metadata extracted from an LRF expansion comment."""

    mode: str  # FIRST or NEXT
    keyword: str  # LRF path keyword
    parent_record: str  # Parent record name (COBOL form)
    target_record: str  # Target record name (COBOL form)
    cursor_name: str  # Derived cursor name (from mapping)
    line_index: int  # Line number in source (0-based)

    @property
    def record_name_display(self) -> str:
        """COBOL form for display."""
        return self.parent_record.upper().replace("_", "-")


@dataclass
class LrfHostVariableInitSequence:
    """Generated host variable initialization code for one LRF cursor."""

    cursor_name: str
    host_group_name: str  # e.g., DCLDZBFASTV
    initialization_lines: list[str]  # Generated COBOL lines


class LrfHostVariablePopulator:
    """Generates and injects host variable population code for LRF cursors."""

    def __init__(
        self,
        host_variable_resolver=None,
        relationship_resolver=None,
        name_normalizer=None,
    ) -> None:
        self.host_variable_resolver = host_variable_resolver
        self.relationship_resolver = relationship_resolver
        self.name_normalizer = name_normalizer
        self.messages: list[str] = []

    def augment_procedure_division(
        self,
        cobol_text: str,
    ) -> tuple[str, list[str]]:
        """Scan COBOL for LRF markers and inject host variable population.

        Returns (modified_cobol, messages).
        """
        self.messages = []
        text = str(cobol_text or "")

        if not text:
            return text, self.messages

        lines = text.split("\n")

        # Step 1: Find all LRF expansion markers and their line positions
        lrf_markers = self._extract_lrf_markers(lines)

        if not lrf_markers:
            self._log("no_lrf_markers")
            return text, self.messages

        # Step 2: For each marker, find the corresponding PERFORM OPEN
        # and generate initialization code
        injection_points: dict[int, list[str]] = {}  # line_index -> code_lines

        for marker in lrf_markers:
            init_code = self._generate_initialization_code(marker, lines)
            if not init_code:
                continue

            # Find the PERFORM OPEN line following this marker
            perform_line = self._find_perform_open_after(marker, lines)
            if perform_line is None:
                self._log(
                    "perform_open_not_found",
                    cursor=marker.cursor_name,
                    keyword=marker.keyword,
                )
                continue

            # Insert initialization code before PERFORM OPEN
            if perform_line not in injection_points:
                injection_points[perform_line] = []

            injection_points[perform_line].extend(init_code)
            self._log(
                "injection_planned",
                cursor=marker.cursor_name,
                line_index=perform_line,
                code_lines=len(init_code),
            )

        # Step 3: Inject the code into the lines
        modified_lines = self._inject_code(lines, injection_points)

        return "\n".join(modified_lines), self.messages

    # ============================================================
    # Private: LRF marker extraction
    # ============================================================

    def _extract_lrf_markers(
        self,
        lines: list[str],
    ) -> list[LrfExpansionMarker]:
        """Find all LRF expansion markers in the source."""
        markers: list[LrfExpansionMarker] = []

        for index, line in enumerate(lines):
            match = LRF_EXPANSION_MARKER_PATTERN.search(line)
            if not match:
                continue

            cursor_name = self._cursor_name_for_record(
                match.group("record")
            )
            if not cursor_name:
                continue

            marker = LrfExpansionMarker(
                mode=match.group("mode").upper(),
                keyword=match.group("keyword"),
                parent_record=match.group("parent"),
                target_record=match.group("record"),
                cursor_name=cursor_name,
                line_index=index,
            )
            markers.append(marker)

        return markers

    # ============================================================
    # Private: Initialization code generation
    # ============================================================

    def _generate_initialization_code(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
    ) -> Optional[list[str]]:
        """Generate MOVE statements for host variable population.

        For now, generate a template structure that downstream code can fill.
        """
        if not self.host_variable_resolver:
            self._log("no_host_variable_resolver")
            return None

        # Get host group for this cursor
        host_group = self.host_variable_resolver.host_group_for_cursor(
            marker.cursor_name
        )
        if not host_group:
            self._log(
                "host_group_not_found",
                cursor=marker.cursor_name,
            )
            return None

        code: list[str] = []

        # INITIALIZE host group
        code.append(f"        INITIALIZE {host_group}.")

        # Add comment marking this as LRF-generated initialization
        code.append(
            f"*       Host variables for LRF cursor {marker.cursor_name}"
        )
        code.append(
            f"*       Parent: {marker.parent_record} Keyword: {marker.keyword}"
        )

        # For each key field in the cursor's WHERE clause, generate MOVE
        # This is a placeholder; actual data flow analysis would happen here
        key_fields = self._extract_where_key_fields(marker, lines)
        for field_name, _field_type in key_fields:
            # Generate: MOVE <parent>.<field> TO <host>.<field>
            host_field = self._normalize_host_field(field_name)
            code.append(
                f"        MOVE {field_name} OF {marker.parent_record} "
                f"TO {host_field} OF {host_group}."
            )

        return code if len(code) > 3 else None

    def _extract_where_key_fields(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
    ) -> list[tuple[str, str]]:
        """Extract the key fields referenced in the cursor's WHERE clause.

        Scans the cursor DECLARE CURSOR statement to find WHERE clause
        references and extract the column names.
        """
        # Find the DECLARE CURSOR statement for this cursor
        cursor_declare_start = self._find_cursor_declare(
            marker.cursor_name, lines
        )
        if cursor_declare_start is None:
            return []

        # Extract WHERE clause from the declaration
        where_fields = self._extract_where_columns_from_declare(
            cursor_declare_start, lines
        )

        return [(field, "key") for field in where_fields]

    def _find_cursor_declare(
        self,
        cursor_name: str,
        lines: list[str],
    ) -> Optional[int]:
        """Find line index of DECLARE CURSOR statement for this cursor."""
        pattern = re.compile(
            rf"DECLARE\s+{re.escape(cursor_name)}\s+CURSOR",
            re.IGNORECASE,
        )

        for index, line in enumerate(lines):
            if pattern.search(line):
                return index

        return None

    def _extract_where_columns_from_declare(
        self,
        start_index: int,
        lines: list[str],
    ) -> list[str]:
        """Extract column names from WHERE clause in DECLARE CURSOR.

        Parses FROM start_index until finding WHERE, then extracts
        column references until the statement ends.
        """
        columns: list[str] = []

        # Assemble the full declaration (may span multiple lines)
        assembled = ""
        for index in range(start_index, min(start_index + 100, len(lines))):
            line = lines[index].strip()
            assembled += " " + line
            if line.endswith("."):
                break

        # Find WHERE clause
        where_upper = assembled.upper()
        where_pos = where_upper.find(" WHERE ")
        if where_pos < 0:
            return columns

        where_clause = assembled[where_pos + 7:]

        # Extract column names (words that come before comparison operators)
        # Pattern: COLUMN_NAME < :HOST.FIELD
        col_pattern = re.compile(
            r"(\w+)\s*[<>=]",
            re.IGNORECASE,
        )

        for match in col_pattern.finditer(where_clause):
            col_name = match.group(1)
            # Filter out keywords and operators
            if col_name.upper() not in ("AND", "OR", "NOT"):
                columns.append(col_name)

        return list(set(columns))  # Remove duplicates

    # ============================================================
    # Private: PERFORM OPEN location finding
    # ============================================================

    def _find_perform_open_after(
        self,
        marker: LrfExpansionMarker,
        lines: list[str],
    ) -> Optional[int]:
        """Find the line index of 'PERFORM nnn-OPEN-<cursor>' after marker.

        Searches forward from marker line until finding a PERFORM OPEN
        for the same cursor.
        """
        search_from = marker.line_index + 1
        search_limit = min(search_from + 50, len(lines))  # Reasonable distance

        cursor_pattern = re.compile(
            rf"PERFORM\s+\d+-OPEN-{re.escape(marker.cursor_name)}\s*\.",
            re.IGNORECASE,
        )

        for index in range(search_from, search_limit):
            if cursor_pattern.search(lines[index]):
                return index

        return None

    # ============================================================
    # Private: Code injection
    # ============================================================

    def _inject_code(
        self,
        lines: list[str],
        injection_points: dict[int, list[str]],
    ) -> list[str]:
        """Insert initialization code before PERFORM OPEN statements.

        Handles line insertion in reverse order to preserve indices.
        """
        result = lines[:]

        # Sort in reverse order so insertions don't shift indices
        for perform_line_index in sorted(injection_points.keys(), reverse=True):
            code_lines = injection_points[perform_line_index]
            # Insert before the PERFORM line
            for code_line in reversed(code_lines):
                result.insert(perform_line_index, code_line)

        return result

    # ============================================================
    # Private: Name resolution and normalization
    # ============================================================

    def _cursor_name_for_record(self, record_name: str) -> Optional[str]:
        """Map IDMS record name to DB2 cursor name."""
        if not self.host_variable_resolver:
            return None

        # Try to resolve via host_variable_resolver
        try:
            cursor = self.host_variable_resolver.cursor_name_for_record(
                record_name
            )
            return cursor
        except Exception:  # noqa: BLE001
            return None

    @staticmethod
    def _normalize_host_field(field_name: str) -> str:
        """Normalize field name for host variable reference."""
        # Remove IDMS suffixes, convert to DB2 form
        return field_name.upper().replace("_", "-")

    # ============================================================
    # Private: Logging
    # ============================================================

    def _log(self, message_code: str, **kwargs) -> None:
        """Log a diagnostic message."""
        msg = f"[LRF-POPULATOR] {message_code}"
        for key, value in kwargs.items():
            msg += f" {key}={value}"
        self.messages.append(msg)

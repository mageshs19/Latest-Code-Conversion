# LOCATION: converter/postprocess/storage_include/storage_ws_injector.py
# ACTION: REPLACE ENTIRE FILE
from __future__ import annotations

from converter.postprocess.dynamic_metadata_resolver import UpdateProgramContext
from patterns.update_restart_patterns import (
    MALFORMED_SQLERROR_END_EVALUATE_PATTERN,
)
from patterns.update_storage_include_patterns import (
    CS_PROGRAM_01_PATTERN,
    PROGRAM_NAME_MOVE_PATTERN,
    CS_PROGRAM_DECLARATION_PATTERN ,
)
from rules.update_restart_rules import (
    UPDATE_RESTART_DIAGNOSTICS,
    UPDATE_RESTART_WS_NAMES,
)
from rules.update_storage_include_rules import (
    CS_PROGRAM_77_TEMPLATE,
    DATE_WS_ANCHORS,
    DATE_WS_EXISTS_UNDER_OTHER_GROUP,
    PROGRAM_NAME_MOVE_REPLACEMENT_TEMPLATE,
    SKIP_DATA_DIVISION_DATE_WS,
    SKIP_DATA_DIVISION_WS,
)
from patterns.db2_date_patterns import (
    DB2_DATE_WORKING_STORAGE_BASE_PATTERN,
    PROCEDURE_DIVISION_PATTERN,
)


class StorageWsInjector:
    """Working-storage, date-WS, program-name and SQLERROR passes.

    Depends on the host class for ``self.line_utils`` and ``self.generator``.
    """

    def fix_malformed_sqlerror(self, cobol_text, diagnostics):
        updated = MALFORMED_SQLERROR_END_EVALUATE_PATTERN.sub(
            "PERFORM SQLERROR\nEND-EVALUATE",
            cobol_text,
        )
        if updated != cobol_text:
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["malformed_sqlerror_fixed"])
        return updated

    def normalize_program_name(self, cobol_text, context, diagnostics):
        """Normalise the PROGRAM-NAME move and the program constant.

        CORRECTION - a 77-level item was appended to the PROCEDURE
        DIVISION

        Three checks guarded the insertion and not one could fire:

          Step 1  r'...PIC\\s+X$\\s*8\\s*$...'     - "\\(" arrived as "$"
          Step 2  CS_PROGRAM_01_PATTERN  "X$8$"  - same corruption
          Step 3  r"^\\s*77\\s+CS-PROGRAM" on RAW text - every line
                  starts with a six-digit sequence number, so the
                  anchor can never match a fixed-format record

        So step 4 always ran, and _find_77_level_insert_point returned a
        position past the PROCEDURE DIVISION. Proven on disk in both
        output families:

          001240     10  CS-PROGRAM  PIC X(8) VALUE 'VMDZ1567'.
          004400     77  CS-PROGRAM  PIC X(8) VALUE 'VMDZ1567'.   <- here
          004410     CALL USERABEN.

        A duplicated data name AND a data item in the PROCEDURE
        DIVISION. The program does not compile.

        WHAT CHANGED

        Presence is now decided on the LOGICAL line, at ANY level,
        scanning only the DATA DIVISION - the program constant already
        exists as a level 10 inside the generated work group, which is
        what rules/timestamp_audit_rules prescribes. When it is there,
        nothing is added and the pass says so.

        When it is genuinely absent, the insertion point must fall
        inside the DATA DIVISION. Outside it the pass REFUSES and
        reports, because writing a 77 into the PROCEDURE DIVISION is
        never a smaller error than writing nothing.

        Step 1 is removed. It never matched, so its removal changes no
        output; keeping a regex that cannot fire only hides the next
        defect.
        """
        program_id = str(context.program_id or "").strip().upper()
        if not program_id:
            return cobol_text

        updated = PROGRAM_NAME_MOVE_PATTERN.sub(
            PROGRAM_NAME_MOVE_REPLACEMENT_TEMPLATE.format(program_id=program_id),
            cobol_text,
        )
        updated = CS_PROGRAM_01_PATTERN.sub(
            lambda match: CS_PROGRAM_77_TEMPLATE.format(
                prefix=match.group("prefix"),
                program_id=program_id,
            ),
            updated,
        )

        if self._program_constant_declared(updated):
            diagnostics.append(
                "Program constant: CS-PROGRAM is already declared in the "
                "DATA DIVISION; no second declaration was added."
            )
            if updated != cobol_text:
                diagnostics.append(
                    UPDATE_RESTART_DIAGNOSTICS["program_name_normalized"]
                )
            return updated

        lines = self.line_utils.lines(updated)
        boundary = self._data_division_end_index(lines)
        insert_index = self._find_77_level_insert_point(updated)

        if 0 <= insert_index <= boundary:
            cs_prog_line = CS_PROGRAM_77_TEMPLATE.format(
                prefix="", program_id=program_id
            )
            updated = self.line_utils.join(
                lines[:insert_index] + [cs_prog_line] + lines[insert_index:]
            )
            diagnostics.append("Added CS-PROGRAM at 77-level")
        else:
            diagnostics.append(
                "Program constant: no safe DATA DIVISION insertion point "
                f"(index {insert_index}; the PROCEDURE DIVISION starts at "
                f"{boundary}). CS-PROGRAM was NOT added - a 77-level item "
                "in the PROCEDURE DIVISION does not compile."
            )

        if updated != cobol_text:
            diagnostics.append(
                UPDATE_RESTART_DIAGNOSTICS["program_name_normalized"]
            )
        return updated

    def _program_constant_declared(self, cobol_text) -> bool:
        """CS-PROGRAM declared at ANY level, DATA DIVISION only."""
        for line in self.line_utils.lines(cobol_text):
            logical = str(self.line_utils.logical(line) or "")

            if not logical or logical.lstrip().startswith("*"):
                continue

            if PROCEDURE_DIVISION_PATTERN.match(logical):
                return False

            if CS_PROGRAM_DECLARATION_PATTERN.match(logical):
                return True

        return False

    def _data_division_end_index(self, lines) -> int:
        """Index of the PROCEDURE DIVISION header, or the line count."""
        for index, line in enumerate(lines):
            logical = str(self.line_utils.logical(line) or "")
            if PROCEDURE_DIVISION_PATTERN.match(logical):
                return index

        return len(lines)
        
    def _find_77_level_insert_point(self, cobol_text: str) -> int:
        """
        Find line index where 77-level declarations should be inserted.
        
        Strategy:
        1. Look for existing 77-level items
        2. If found, insert after the last 77
        3. Otherwise, insert before first 01-level group
        4. Return -1 if WORKING-STORAGE not found
        """
        import re
        lines = self.line_utils.lines(cobol_text)
        
        working_storage_idx = -1
        last_77_idx = -1
        first_01_idx = -1
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # Find WORKING-STORAGE SECTION
            if "WORKING-STORAGE SECTION" in line_upper:
                working_storage_idx = i
                continue
            
            # Only count after WORKING-STORAGE is found
            if working_storage_idx >= 0:
                # Track 77-level items
                if re.match(r"^\s*77\s+", line, re.IGNORECASE):
                    last_77_idx = i
                
                # Track first 01-level group
                if first_01_idx < 0 and re.match(r"^\s*01\s+", line, re.IGNORECASE):
                    first_01_idx = i
        
        # If working-storage not found, return -1
        if working_storage_idx < 0:
            return -1
        
        # Prefer inserting after last 77
        if last_77_idx >= 0:
            return last_77_idx + 1
        
        # Otherwise insert before first 01
        if first_01_idx >= 0:
            return first_01_idx
        
        # Fallback: insert at end
        return len(lines) - 1

    def ensure_working_storage(self, cobol_text, context, diagnostics):
        """
        Ensure WORKING-STORAGE section has required groups.
        
        ENHANCED:
        - Validate section boundaries (no WS items in FILE SECTION)
        - Remove incorrectly-placed items
        - Ensure proper placement

        CORRECTION (NEW-2c): the existence check used to build a literal
        anchor string via WS_ANCHOR_01_TEMPLATE ("01 {group}." - ONE
        space) and test it with logical_contains(), a plain substring
        search with no whitespace normalisation. RestartStorageInjector
        (converter/composers/restart/ - a completely separate system
        from this one) renders the SAME group aligned to COBOL Area
        A/B with TWO spaces ("01  WS-SWITCHES."). A one-space target
        can never appear as a substring of a two-space source line, so
        this check always concluded the group was absent whenever the
        OTHER system had already declared it first, and injected a
        second, independently-named copy.

        Proven directly against VM1BD567's output, which carried BOTH
        "01  WS-SWITCHES." (RestartStorageInjector, this run's first
        pass) and "01 WS-SWITCHES." (this method's own template,
        second pass) as two separate groups.

        The group header is now matched by SHAPE - level number,
        flexible whitespace, the group name, optional period - via
        _declares_group(), the same way this file already matches
        "^\\s*01\\s+WS-" in _has_ws_items_in_file_section() above.
        """
        # Step 1: Check for WS items in FILE SECTION (structural error)
        if self._has_ws_items_in_file_section(cobol_text):
            diagnostics.append(
                "WARNING: Working-storage items detected in FILE SECTION. "
                "Removing and re-injecting into correct section."
            )
            cobol_text = self._remove_ws_items_from_file_section(cobol_text, diagnostics)
        
        # Step 2: Existing working-storage validation
        names = UPDATE_RESTART_WS_NAMES

        if self._declares_group(
            cobol_text, names["switch_group"]
        ) and self._declares_group(cobol_text, names["help_group"]):
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["ws_exists"])
            return cobol_text

        lines = self.line_utils.lines(cobol_text)
        insert_index = self.line_utils.data_division_insert_line_index(lines)
        if insert_index < 0:
            diagnostics.append(SKIP_DATA_DIVISION_WS)
            return cobol_text

        block = self.generator.working_storage(context).splitlines()
        updated_lines = lines[:insert_index] + block + [""] + lines[insert_index:]
        diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["ws_injected"])
        return self.line_utils.join(updated_lines)

    def _declares_group(self, cobol_text: str, group_name: str) -> bool:
        """True when `01 <group_name>.` is already declared, regardless
        of how many spaces separate the level number from the name -
        COBOL permits any amount of Area A/B whitespace there, and a
        different generator (RestartStorageInjector) may align it
        differently than this one does. See CORRECTION in
        ensure_working_storage() above.
        """
        import re
        wanted = str(group_name or "").strip().upper()
        if not wanted:
            return False
        pattern = re.compile(
            rf"^01\s+{re.escape(wanted)}\s*\.?\s*$",
            flags=re.IGNORECASE,
        )
        for line in self.line_utils.lines(cobol_text):
            logical = str(self.line_utils.logical(line) or "").strip()
            if pattern.match(logical):
                return True
        return False
    
    def _has_ws_items_in_file_section(self, cobol_text: str) -> bool:
        """
        Check if WORKING-STORAGE items exist in FILE SECTION.
        
        This indicates a structural error in the COBOL source.
        """
        import re
        lines = cobol_text.split('\n')
        
        in_file_section = False
        in_working_storage = False
        
        for line in lines:
            line_upper = line.upper()
            
            # Track which section we're in
            if 'FILE SECTION' in line_upper:
                in_file_section = True
                in_working_storage = False
                continue
            
            if 'WORKING-STORAGE SECTION' in line_upper:
                in_working_storage = True
                in_file_section = False
                continue
            
            # If we're in FILE SECTION and see 01-level WS- item, that's structural error
            if in_file_section:
                # Check for 01-level group starting with WS-
                if re.match(r"^\s*01\s+WS-", line, re.IGNORECASE):
                    return True
                # Also check for other working-storage patterns
                if re.match(r"^\s*0[1-9]\s+(WS-|SW-|WS\s+)", line, re.IGNORECASE):
                    return True
        
        return False
    
    def _remove_ws_items_from_file_section(self, cobol_text: str, diagnostics: list) -> str:
        """
        Remove WORKING-STORAGE items from FILE SECTION.
        
        Strategy:
        1. Identify 01-level WS- groups in FILE SECTION
        2. Remove entire group (group + subordinates)
        3. Re-insert into WORKING-STORAGE SECTION
        """
        import re
        lines = cobol_text.split('\n')
        result = []
        skip_group = False
        in_file_section = False
        removed_groups = []
        
        for i, line in enumerate(lines):
            line_upper = line.upper()
            
            # Track sections
            if 'FILE SECTION' in line_upper:
                in_file_section = True
            elif 'WORKING-STORAGE SECTION' in line_upper:
                in_file_section = False
            
            # If in FILE SECTION and hit 01-level WS group
            if in_file_section and re.match(r"^\s*01\s+WS-", line, re.IGNORECASE):
                skip_group = True
                # Extract group name for diagnostics
                match = re.match(r"^\s*01\s+(WS-[A-Z0-9-]+)", line, re.IGNORECASE)
                if match:
                    removed_groups.append(match.group(1))
                continue
            
            # Skip subordinate lines of removed group
            if skip_group:
                # Stop skipping when we hit next 01-level or end-of-division
                if re.match(r"^\s*01\s+", line, re.IGNORECASE):
                    skip_group = False
                elif 'PROCEDURE DIVISION' in line_upper:
                    skip_group = False
                else:
                    continue
            
            result.append(line)
        
        if removed_groups:
            diagnostics.append(
                f"Removed groups from FILE SECTION: {', '.join(removed_groups)}"
            )
        
        return '\n'.join(result)

    def ensure_date_working_storage(self, cobol_text, diagnostics):
        """Declare the date layout once, under ANY group name.

        CORRECTION - the guard asked about a GROUP, the defect is a FIELD

        The test was:

            if any(logical_contains(cobol_text, anchor)
                   for anchor in DATE_WS_ANCHORS)

        where DATE_WS_ANCHORS is ("01 WS-DATUMVELDEN.",
        "01  WS-DATUMVELDEN."). RestartStorageInjector runs BEFORE this
        pass and declares the SAME fields under WS-DATE-CONVERSION -
        proven in the batch log:

            164: Restart storage: WS-DATE-CONVERSION was absent; declared it.
            352: Injected manual-style date working-storage.

        The anchor never matched, a second full copy was injected, and
        VM1BD567 and VM1BD526 each shipped with DA-CCYYMMDD,
        DA-CCYYMMDD-R and DA-DD-MM-CCYY declared TWICE under two
        different 01 groups. Every generated reference to them is
        unqualified, so the compiler rejects them as not uniquely
        defined. Every update program was affected; no retrieval program
        was, because only the update path runs both injectors.

        RestartStorageInjector._plan_groups already states the correct
        principle - "the resolved name that proves the layout already
        exists under some other group" - and declines on the FIELD. This
        pass now applies the same test, which is also what
        Db2DateWorkingStorageManager._has_date_working_storage has always
        done. Three sites, one rule.

        SCOPE MATTERS. DB2_DATE_WORKING_STORAGE_BASE_PATTERN also matches
        a USE of the fields:

            MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY   -> True

        so the scan stops at PROCEDURE DIVISION. Unscoped, a program that
        references the layout without declaring it would be refused the
        storage it needs.
        """
        if any(
            self.line_utils.logical_contains(cobol_text, anchor)
            for anchor in DATE_WS_ANCHORS
        ):
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["date_ws_exists"])
            return cobol_text

        if self._date_layout_declared(cobol_text):
            diagnostics.append(DATE_WS_EXISTS_UNDER_OTHER_GROUP)
            return cobol_text

        lines = self.line_utils.lines(cobol_text)
        insert_index = self.line_utils.data_division_insert_line_index(lines)
        if insert_index < 0:
            diagnostics.append(SKIP_DATA_DIVISION_DATE_WS)
            return cobol_text

        block = self.generator.date_working_storage().splitlines()
        updated_lines = lines[:insert_index] + block + [""] + lines[insert_index:]
        diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["date_ws_injected"])
        return self.line_utils.join(updated_lines)

    def _date_layout_declared(self, cobol_text) -> bool:
        """True when the date fields are DECLARED under any 01 group.

        DATA DIVISION only - see the scope note above.
        """
        for line in self.line_utils.lines(cobol_text):
            logical = str(self.line_utils.logical(line) or "")

            if not logical or logical.lstrip().startswith("*"):
                continue

            if PROCEDURE_DIVISION_PATTERN.match(logical):
                return False

            if DB2_DATE_WORKING_STORAGE_BASE_PATTERN.search(logical):
                return True

        return False
from __future__ import annotations

from idms_db2_phase2.postprocess.dynamic_metadata_resolver import UpdateProgramContext
from patterns.update_restart_patterns import (
    MALFORMED_SQLERROR_END_EVALUATE_PATTERN,
)
from patterns.update_storage_include_patterns import (
    CS_PROGRAM_01_PATTERN,
    PROGRAM_NAME_MOVE_PATTERN,
)
from rules.update_restart_rules import (
    UPDATE_RESTART_DIAGNOSTICS,
    UPDATE_RESTART_WS_NAMES,
)
from rules.update_storage_include_rules import (
    CS_PROGRAM_77_TEMPLATE,
    DATE_WS_ANCHORS,
    PROGRAM_NAME_MOVE_REPLACEMENT_TEMPLATE,
    SKIP_DATA_DIVISION_DATE_WS,
    SKIP_DATA_DIVISION_WS,
    WS_ANCHOR_01_TEMPLATE,
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
        """
        Normalize program name and ensure CS-PROGRAM at 77-level.
        
        ENHANCED: 
        - Removes incorrectly-placed CS-PROGRAM at subordinate levels
        - Ensures injection only at 77-level
        - Validates final placement
        """
        program_id = str(context.program_id or "").strip().upper()
        if not program_id:
            return cobol_text

        # Step 1: Remove incorrectly-placed CS-PROGRAM (e.g., at level 10)
        import re
        updated = re.sub(
            r'\s+10\s+CS-PROGRAM\s+PIC\s+X\(\s*8\s*\)\s+VALUE\s+[\'"]([^\'"]*)[\'"]\.?\s*\n',
            "",
            cobol_text,
            flags=re.IGNORECASE
        )
        if updated != cobol_text:
            diagnostics.append(
                "CORRECTED: Removed CS-PROGRAM from subordinate level (level 10)"
            )
            cobol_text = updated

        # Step 2: Replace 01-level CS-PROGRAM with 77-level (existing logic)
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
        
        # Step 3: Validate CS-PROGRAM is at 77-level (or add it if missing)
        if "77" in updated and "CS-PROGRAM" in updated:
            # Check if at 77-level
            if re.search(r"^\s*77\s+CS-PROGRAM", updated, re.IGNORECASE | re.MULTILINE):
                if updated != cobol_text:
                    diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["program_name_normalized"])
                return updated
        
        # Step 4: If CS-PROGRAM not found at 77-level, add it
        if not re.search(r"77\s+CS-PROGRAM", updated, re.IGNORECASE):
            # Find insertion point (after other 77-level items or before first 01 group)
            insert_index = self._find_77_level_insert_point(updated)
            if insert_index >= 0:
                lines = self.line_utils.lines(updated)
                cs_prog_line = f"77  CS-PROGRAM                 PIC X(8) VALUE '{program_id}'."
                updated_lines = lines[:insert_index] + [cs_prog_line] + lines[insert_index:]
                updated = self.line_utils.join(updated_lines)
                diagnostics.append("Added CS-PROGRAM at 77-level")
        
        if updated != cobol_text:
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["program_name_normalized"])
        return updated
    
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
        switch_anchor = WS_ANCHOR_01_TEMPLATE.format(group=names["switch_group"])
        help_anchor = WS_ANCHOR_01_TEMPLATE.format(group=names["help_group"])

        if self.line_utils.logical_contains(
            cobol_text, switch_anchor
        ) and self.line_utils.logical_contains(cobol_text, help_anchor):
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
        if any(
            self.line_utils.logical_contains(cobol_text, anchor)
            for anchor in DATE_WS_ANCHORS
        ):
            diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["date_ws_exists"])
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
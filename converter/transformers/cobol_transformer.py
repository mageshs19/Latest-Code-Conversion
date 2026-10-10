# LOCATION: converter/transformers/cobol_transformer.py
# ACTION: REPLACE ENTIRE FILE
"""Converts IDMS COBOL statements to DB2-compatible COBOL.

Responsibilities are delegated to focused helper classes while keeping the
existing public API unchanged.

CORRECTION 1 - the IDMS-ABORT paragraph BODY survived its header
-----------------------------------------------------------------
The source carries

    EINDE-PROGRAMMA-EXIT.
        EXIT.
    /
    IDMS-ABORT.                     <- header
        CLOSE FORM.                 <- body
        COPY IDMS IDMS-STATUS.      <- body

Only the header was removed. CLOSE FORM was left stranded after a
paragraph EXIT, and StructuralSafetyComposer then correctly commented it
as unreachable:

    *DB2-KEEP: statement follows a paragraph EXIT and is unreachable.
    *DB2-KEEP CLOSE FORM.

The safety pass was right; the removal was incomplete. The manual
reference deletes the whole paragraph. Skipping now runs to the next
paragraph header, section header or division boundary, so no business
line can be swallowed, and a blast-radius cap reverts to normal
processing if the boundary is never found.

CORRECTION 2 - PROGRAM-NAME disagreed with PROGRAM-ID
------------------------------------------------------
PROGRAM-ID was rewritten to the derived DB2 id while

    MOVE 'VM7BD200' TO PROGRAM-NAME.

kept the source id, so the job log and every abend message named a
program that no longer exists. The manual reference carries
MOVE 'VMDZ7200' TO PROGRAM-NAME.

ProgramNameSyncService already performs this rewrite safely - it reads
the FINAL PROGRAM-ID out of the converted text and touches only a
MOVE literal TO PROGRAM-NAME. It was simply never called. It runs as the
last pass, AFTER fix_program_id_period, so the id it reads is final.
"""

from __future__ import annotations

import re

from converter.domain.models import IdmsOperation
from converter.parsers.cobol_parser import CobolParser
from converter.services.program_name_sync_service import (
    ProgramNameSyncService,
)
from converter.transformers.cobol_identification_transformer import (
    CobolIdentificationTransformer,
)
from converter.transformers.cobol_program_id_transformer import (
    CobolProgramIdTransformer,
)
from converter.transformers.cobol_transformed_line_merger import (
    CobolTransformedLineMerger,
)
from converter.transformers.cobol_transformer_line_utils import (
    CobolTransformerLineUtils,
)
from converter.transformers.idms_residual_cleanup import IdmsResidualCleanup
from converter.transformers.idms_statement_transformer import (
    IdmsStatementTransformer,
)
from patterns.cobol_patterns import DIVISION_PATTERN
from patterns.db2_patterns import SQL_ERROR_PARAGRAPH_PATTERN
from patterns.final_feedback_fix_patterns import (
    DIVISION_SECTION_HEADER_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
)
from rules.cobol_statement_rules import NON_PARAGRAPH_SINGLE_WORDS
from rules.cobol_transformer_rules import (
    DB2_COMPILER_OPTION_LINE,
    DEFAULT_SQL_ERROR_PARAGRAPH,
)

# Blast-radius cap for the orphan IDMS-ABORT body skip. A paragraph body
# that long means the boundary test has lost sync, so normal processing
# resumes rather than deleting the rest of the program.
IDMS_ABORT_BODY_LINE_LIMIT = 20


class CobolTransformer:
    """Converts IDMS COBOL statements to DB2-compatible COBOL."""

    def __init__(
        self,
        idms_statement_transformer: IdmsStatementTransformer,
    ) -> None:
        self.idms_statement_transformer = idms_statement_transformer
        self.parser = CobolParser()

        self.line_utils = CobolTransformerLineUtils()
        self.program_id_transformer = CobolProgramIdTransformer(
            line_utils=self.line_utils,
        )
        self.identification_transformer = CobolIdentificationTransformer(
            line_utils=self.line_utils,
        )
        self.program_name_sync = ProgramNameSyncService()
        self.residual_cleanup = IdmsResidualCleanup()
        self.line_merger = CobolTransformedLineMerger(
            line_utils=self.line_utils,
        )
        self._in_working_storage = False

    # =================================================================
    # Public entry point
    # =================================================================
    def transform(
        self,
        cobol_text: str,
        target_program_id: str = "",
    ) -> tuple[str, list[str], list[IdmsOperation]]:
        operations = self.parser.analyze(cobol_text)

        validation_messages: list[str] = []
        output_lines: list[str] = []
        current_division = ""
        sql_error_paragraph = self._detect_sql_error_paragraph(cobol_text)
        
        # Reset state for this transformation
        self._in_working_storage = False

        skip_idms_abort_body = False
        idms_abort_skipped = 0

        for raw_line in str(cobol_text or "").splitlines():
            line = raw_line.rstrip()
            logical = self.line_utils.logical_line(line)
            logical_stripped = logical.strip()

            # ---- Orphan IDMS-ABORT body.
            #
            # The header has already been replaced by a comment. Every
            # line up to the next paragraph, section or division header
            # belongs to that paragraph and goes with it.
            if skip_idms_abort_body:
                if self._ends_idms_abort_body(logical_stripped):
                    skip_idms_abort_body = False
                    idms_abort_skipped = 0
                    # fall through: this line starts the NEXT block
                elif idms_abort_skipped >= IDMS_ABORT_BODY_LINE_LIMIT:
                    skip_idms_abort_body = False
                    idms_abort_skipped = 0
                    validation_messages.append(
                        "Residual cleanup: orphan IDMS-ABORT body exceeded "
                        f"{IDMS_ABORT_BODY_LINE_LIMIT} lines; the remaining "
                        "lines were kept."
                    )
                    # fall through: keep this line
                else:
                    idms_abort_skipped += 1
                    continue

            if not logical_stripped:
                output_lines.append(line)
                continue

            if self._is_cbl_line(logical_stripped):
                output_lines.append(
                    self.line_utils.replace_logical_body(
                        original_line=line,
                        replacement_body=DB2_COMPILER_OPTION_LINE,
                    )
                )
                continue

            if self.residual_cleanup.is_idms_abort_paragraph(logical_stripped):
                output_lines.append(
                    "* DB2: Removed orphan IDMS-ABORT paragraph."
                )
                skip_idms_abort_body = True
                idms_abort_skipped = 0
                continue

            program_id_line = self.program_id_transformer.program_id_replacement(
                original_line=line,
                logical_line=logical_stripped,
                target_program_id=target_program_id,
            )

            if program_id_line is not None:
                output_lines.append(program_id_line)
                continue

            author_line = self.identification_transformer.author_replacement(
                original_line=line,
                logical_line=logical_stripped,
            )

            if author_line is not None:
                output_lines.append(author_line)
                continue

            date_written_line = self.identification_transformer.date_written_replacement(
                original_line=line,
                logical_line=logical_stripped,
            )

            if date_written_line is not None:
                output_lines.append(date_written_line)
                continue

            division_match = DIVISION_PATTERN.match(logical_stripped)

            if division_match:
                current_division = division_match.group(1).upper()
                self._in_working_storage = False
                output_lines.append(line)
                continue

            # Track WORKING-STORAGE section entry. IDMS declarative lines
            # such as "IDMS-RECORDS WITHIN WORKING-STORAGE SECTION." must not
            # be captured here; they fall through to the residual cleanup.
            if (
                "WORKING-STORAGE" in logical_stripped.upper()
                and "SECTION" in logical_stripped.upper()
                and not self.residual_cleanup.is_idms_declarative_or_control(
                    logical_stripped
                )
            ):
                self._in_working_storage = True
                output_lines.append(line)
                continue
            
            # Track section changes within a division. IDMS control/schema
            # sections are left for the residual cleanup below to remove.
            if (
                "SECTION" in logical_stripped.upper()
                and "WORKING-STORAGE" not in logical_stripped.upper()
                and not self.residual_cleanup.is_idms_declarative_or_control(
                    logical_stripped
                )
            ):
                self._in_working_storage = False
                output_lines.append(line)
                continue

            # Apply COMP-3 and FILLER cleaning to WORKING-STORAGE data declarations
            if self._in_working_storage and "PIC" in logical_stripped and any(
                marker in logical_stripped for marker in ["COMP-3", "COMP-2", "COMP-1", "COMPUTATIONAL", "FILLER", "PACKED"]
            ):
                cleaned_line = self._clean_data_declaration_line(line)
                if cleaned_line is not None:  # Only append if not removed
                    output_lines.append(cleaned_line)
                continue

            if self.residual_cleanup.is_idms_declarative_or_control(logical_stripped):
                output_lines.extend(
                    self.residual_cleanup.removed_declarative_lines(
                        logical_stripped
                    )
                )
                continue

            if self.residual_cleanup.is_idms_executable_cleanup(logical_stripped):
                output_lines.extend(
                    self.residual_cleanup.removed_executable_lines(
                        logical_line=logical_stripped,
                        current_division=current_division,
                    )
                )
                continue

            transformed_lines, _opened_set = (
                self.idms_statement_transformer.transform_line(
                    line=logical_stripped,
                    current_division=current_division,
                    sql_error_paragraph=sql_error_paragraph,
                )
            )

            if self.line_merger.transformer_changed_line(
                original_logical=logical_stripped,
                transformed_lines=transformed_lines,
            ):
                output_lines.extend(
                    self.line_merger.merge_transformed_lines_with_original_style(
                        original_line=line,
                        original_logical=logical_stripped,
                        transformed_lines=transformed_lines,
                    )
                )
            else:
                output_lines.append(line)

        converted_text = "\n".join(output_lines).rstrip() + "\n"

        converted_text = self.program_id_transformer.fix_program_id_period(
            text=converted_text,
            target_program_id=target_program_id,
        )

        # PROGRAM-NAME must agree with the FINAL PROGRAM-ID, so this runs
        # last. Safe by construction: ProgramNameSyncService reads the id
        # out of the converted text and rewrites only a
        # MOVE literal TO PROGRAM-NAME.
        converted_text = self.program_name_sync.sync(converted_text)

        return converted_text, validation_messages, operations

    # =================================================================
    # Helpers
    # =================================================================
    def _ends_idms_abort_body(
        self,
        logical_line: str,
    ) -> bool:
        """True when this line starts something that is NOT the body.

        A paragraph header, a section header or a division boundary ends
        the orphaned block. EXIT. is NOT a boundary - it is a single
        word ending in a period that looks like a header but belongs to
        the removed paragraph, which is why NON_PARAGRAPH_SINGLE_WORDS
        is consulted.
        """
        text = str(logical_line or "").strip()
        if not text:
            return False

        if DIVISION_PATTERN.match(text):
            return True

        if DIVISION_SECTION_HEADER_PATTERN.match(text.upper()):
            return True

        match = PARAGRAPH_HEADER_PATTERN.match(text.upper())
        if not match:
            return False

        word = text.rstrip(". ").upper()
        return bool(word) and word not in NON_PARAGRAPH_SINGLE_WORDS

    def _is_cbl_line(
        self,
        logical_line: str,
    ) -> bool:
        return str(logical_line or "").strip().upper().startswith("CBL ")

    def _detect_sql_error_paragraph(
        self,
        cobol_text: str,
    ) -> str:
        match = SQL_ERROR_PARAGRAPH_PATTERN.search(str(cobol_text or ""))

        if not match:
            return DEFAULT_SQL_ERROR_PARAGRAPH

        return match.group(1).upper()

    def _clean_data_declaration_line(
        self,
        line: str,
    ) -> str | None:
        """Remove COMP-3 and FILLER fields from data declarations in WORKING-STORAGE.
        
        Removes:
        - Binary encoding: COMP-3, COMP-2, COMP-1, COMPUTATIONAL variants, PACKED-DECIMAL
        - FILLER field declarations
        
        Adds:
        - VALUE ZEROES to numeric PIC clauses without existing VALUE
        
        Returns:
        - None if line should be skipped (e.g., FILLER)
        - Modified line if changes made
        - Original line if no changes needed
        """
        logical = self.line_utils.logical_line(line)
        logical_stripped = logical.strip()
        
        # Don't process non-data lines
        if not logical_stripped:
            return line
        
        # Skip comments
        if logical_stripped.startswith("*"):
            return line
        
        # Skip FILLER declarations entirely - return None to exclude from output
        if any(marker in logical for marker in ["FILLER", "filler"]):
            return None
        
        # Remove binary encoding clauses
        modified_logical = logical
        binary_patterns = [
            " COMP-3", " COMP-2", " COMP-1",
            " COMPUTATIONAL-3", " COMPUTATIONAL-2", " COMPUTATIONAL-1", 
            " COMP-3.", " COMP-2.", " COMP-1.",
            " COMPUTATIONAL-3.", " COMPUTATIONAL-2.", " COMPUTATIONAL-1.",
            " PACKED-DECIMAL", " PACKED-DECIMAL."
        ]
        
        for pattern in binary_patterns:
            modified_logical = modified_logical.replace(pattern, "")
        
        # Drop the sign on plain integer record-key fields (PIC S9(n) -> PIC 9(n)).
        # Signed decimal fields (PIC S9(x)V99, e.g. money) keep their sign.
        if "V" not in modified_logical.upper():
            modified_logical = re.sub(
                r"(PIC\s+)S9", r"\g<1>9", modified_logical
            )
        
        # Add VALUE ZEROES to numeric fields
        if "PIC" in modified_logical and "VALUE" not in modified_logical:
            # Check if it's a numeric PIC
            if any(pic in modified_logical.upper() for pic in ["PIC 9", "PIC S9"]):
                # Find the PIC clause and add VALUE ZEROES after it
                if "." in modified_logical:
                    # Has period - insert before it
                    modified_logical = modified_logical.replace(
                        ".",
                        " VALUE ZEROES."
                    )
                else:
                    # No period - add VALUE ZEROES at end
                    modified_logical = modified_logical.rstrip() + " VALUE ZEROES"
        
        # If something changed, apply it to the original line's structure
        if modified_logical != logical:
            result = self.line_utils.replace_logical_body(
                original_line=line,
                replacement_body=modified_logical.strip()
            )
            return result
        
        return line


__all__ = [
    "CobolTransformer",
]
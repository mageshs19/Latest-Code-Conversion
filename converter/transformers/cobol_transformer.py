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

The same id survived in a SECOND place, measured on VMDZ7200 line 442:

    DISPLAY 'VM7BD200: ** DATE ARCHIVAGE NOT OK **'

A MOVE rewrite cannot reach a DISPLAY literal, so the abend message -
the one line an operator reads when the job fails - still named the
source program. sync() now also derives any VM<site>?BD<tail> token
found INSIDE a quoted literal, delegating the transform to
NameDerivationResolver, the single owner of that rule. The derived name
is always the same length as the source name, so no literal can grow
and no line can overflow column 72.

CORRECTION 3 - a second copy of Converter 4 was pasted into this class
-----------------------------------------------------------------------
A ``_convert_status_abort_perform`` method was added at the end of
CobolTransformer. It referenced six names this module does not own:

    IDMS_STATUS_PERFORM_PATTERN   not imported here
    IDMS_ABORT_PERFORM_PATTERN    not imported here
    text / statement / division   local variables that were never bound
    self._remove                  a method of IdmsStatementTransformer

The real Converter 4 lives in the idms_statement package, alongside the
BIND / READY / CONNECT / DISCONNECT / FIND CURRENT converters and the
``_remove`` and ``_division`` helpers it depends on. CobolTransformer
reaches it the way it reaches every other IDMS converter - through

    self.idms_statement_transformer.transform_line(...)

Two copies of one converter is the same defect class as a constant
declared twice: editing the dead copy changes nothing and reads like a
tooling fault. There is now ONE owner of PERFORM IDMS-STATUS /
IDMS-ABORT / IDMS-STOP removal, and it is not this file.

CORRECTION 4 - two passes ran SILENTLY
----------------------------------------
``IdmsResidualCleanup.removed_field_lines`` and
``ProgramNameSyncService.sync`` were both wired into this method, but
neither collector was reset and neither was drained. Two consequences:

  - a removal, a rename or a refusal was invisible in the run log,
    which is precisely what CHK-29.05 ("LR-STATUS replacement should be
    documented") reports as a failure, and

  - ONE instance of each helper is built in __init__ and reused for
    every program, so in a batch run the second program inherited the
    first program's messages and the log named fields and ids that the
    second program never contained.

``reset()`` is called for both with the other per-transformation state,
and ``messages`` is drained into ``validation_messages`` - the residual
cleanup immediately after the line loop, the name sync immediately
after it runs. That is the same contract every composer in the pipeline
already honours.

CORRECTION 5 - THE STATEMENT TRANSFORMER WAS NEVER RESET OR DRAINED
--------------------------------------------------------------------
``IdmsStatementTransformer.reset()`` carries this instruction::

    MUST be called once per program by CobolTransformer.transform(),
    before the first transform_line(). Without it a batch run carries
    one program's diagnostics and unmapped records into the next.

CORRECTION 4 added exactly that call for ``residual_cleanup`` and
``program_name_sync`` - and not for the statement transformer, which is
the component the instruction names. One instance is built in
ConversionComponentFactory and reused for every program in the folder,
so across a six-program run ``unmapped_records`` and ``messages``
accumulated from the first program to the last. A record that had no
DB2 target in program 1 was still listed as unmapped while program 6
was converting.

Its ``messages`` were never drained either, so every
``_keep_and_comment_unmapped`` refusal - the diagnostic that explains
why an IDMS access was left as a comment instead of becoming SQL - went
nowhere. That is the same defect as CORRECTION 4, in the same method,
on the one collaborator CORRECTION 4 missed.

BLAST RADIUS, STATED PLAINLY: draining ``messages`` only lengthens the
run log and cannot change generated COBOL. Calling ``reset()`` CAN:
programs 2..n no longer inherit earlier unmapped records, so a record
that was being commented purely because an earlier program could not
map it will stop being commented. Diff every program against the frozen
baseline after applying this.

CORRECTION 6 - NO SEAM FOR BLOCK-LEVEL ANALYSIS
------------------------------------------------
``IdmsStatementTransformer`` converts ONE LINE at a time and receives
only (line, division, sql_error_paragraph). It therefore cannot tell an
LR WALK from an LR BOUNDED SEARCH, because that is a property of the
enclosing PERFORM UNTIL, and it mapped every OBTAIN FIRST / NEXT to a
cursor unconditionally.

This method is the only place that holds the whole expanded program AND
the transformer instance, so it is the correct seam. An optional
``lr_access_analyser`` collaborator is read ONCE per program, before the
line loop, and its result is published onto the transformer in the same
shape ``unmapped_records`` already uses.

The collaborator defaults to None, so a build that does not supply one
behaves exactly as before - the transformer sees an empty mapping and
every OBTAIN keeps the cursor path.

DO NOT WIRE AN ANALYSER UNTIL THE LOOP-REMOVAL PASS EXISTS. When a
record is classified as a bounded search the in-loop OBTAIN NEXT becomes
a comment, which leaves the program's own PERFORM UNTIL with an empty
body and an unchanging condition - an infinite loop at run time.
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

# DIVISION_PATTERN is imported from cobol_patterns, NOT from
# final_feedback_fix_patterns. Both modules declare a name spelled that
# way; only the cobol_patterns form carries the capture group that
# `division_match.group(1)` below depends on. Do not "tidy" this import.
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

# Attribute the bounded-search mapping is published under. The reading
# end declares the same name; keeping it in one place is what stops the
# producer and the consumer drifting apart.
BOUNDED_SEARCH_ATTRIBUTE = "bounded_search_records"

ANALYSER_FAILED_TEMPLATE = (
    "LR access analysis: skipped, every OBTAIN keeps the cursor path. "
    "Reason: {reason}"
)
ANALYSER_RESULT_TEMPLATE = (
    "LR access analysis: {count} record(s) classified as a bounded "
    "search ({records})."
)


class CobolTransformer:
    """Converts IDMS COBOL statements to DB2-compatible COBOL."""

    def __init__(
        self,
        idms_statement_transformer: IdmsStatementTransformer,
        lr_access_analyser=None,
    ) -> None:
        self.idms_statement_transformer = idms_statement_transformer

        # Optional. None -> no bounded-search classification is made and
        # the statement transformer behaves exactly as before.
        # See CORRECTION 6.
        self.lr_access_analyser = lr_access_analyser

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
        compiler_option_seen = False
        current_division = ""
        sql_error_paragraph = self._detect_sql_error_paragraph(cobol_text)

        # ---- Per-transformation state.
        #
        # residual_cleanup, program_name_sync and the statement
        # transformer are built ONCE and reused for every program, so
        # their collectors must be emptied here. Without this a batch run
        # reports program 1's removals, renames and unmapped records
        # against program 2. See CORRECTION 4 and CORRECTION 5.
        self._in_working_storage = False
        self.residual_cleanup.reset()
        self.program_name_sync.reset()
        self._reset_statement_transformer()

        # ---- Block-level classification, once, before the line loop.
        self._publish_bounded_search_records(
            cobol_text=cobol_text,
            validation_messages=validation_messages,
        )

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
                compiler_option_seen = True
                validation_messages.append(
                    f"Compiler option: replaced '{logical_stripped}' with "
                    f"{DB2_COMPILER_OPTION_LINE}."
                )
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

            # Apply COMP-3 and FILLER cleaning to WORKING-STORAGE data
            # declarations.
            if self._in_working_storage and "PIC" in logical_stripped and any(
                marker in logical_stripped
                for marker in [
                    "COMP-3",
                    "COMP-2",
                    "COMP-1",
                    "COMPUTATIONAL",
                    "FILLER",
                    "PACKED",
                ]
            ):
                cleaned_line = self._clean_data_declaration_line(line)
                if cleaned_line is not None:  # Only append if not removed
                    output_lines.append(cleaned_line)
                continue

            if self.residual_cleanup.is_idms_declarative_or_control(
                logical_stripped
            ):
                output_lines.extend(
                    self.residual_cleanup.removed_declarative_lines(
                        logical_stripped
                    )
                )
                continue

            if self.residual_cleanup.is_idms_executable_cleanup(
                logical_stripped
            ):
                output_lines.extend(
                    self.residual_cleanup.removed_executable_lines(
                        logical_line=logical_stripped,
                        current_division=current_division,
                    )
                )
                continue

            # Orphaned copybook-field references. COPY_IDMS_PATTERN
            # removed the member that declared LR-STATUS / ERROR-STATUS
            # / DML-SEQUENCE; this catches what that deletion orphans.
            # Its diagnostics are drained after the loop - CORRECTION 4.
            if self.residual_cleanup.references_removed_field(
                logical_stripped
            ):
                output_lines.extend(
                    self.residual_cleanup.removed_field_lines(
                        logical_stripped
                    )
                )
                continue

            # Every IDMS statement converter - including Converter 4,
            # which removes PERFORM IDMS-STATUS / IDMS-ABORT / IDMS-STOP -
            # is reached through this one call. See CORRECTION 3.
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

        # ---- Drain the cleanup diagnostics.
        #
        # Drained here, AFTER the loop, because every removal and every
        # refusal must reach the run log. A pass that silently deletes
        # generated output cannot be reviewed. See CORRECTION 4 and
        # CORRECTION 5.
        validation_messages.extend(self.residual_cleanup.messages)
        validation_messages.extend(
            list(getattr(self.idms_statement_transformer, "messages", []) or [])
        )

        if not compiler_option_seen:
            self._ensure_compiler_option(output_lines, validation_messages)

        converted_text = "\n".join(output_lines).rstrip() + "\n"

        converted_text = self.program_id_transformer.fix_program_id_period(
            text=converted_text,
            target_program_id=target_program_id,
        )

        # PROGRAM-NAME must agree with the FINAL PROGRAM-ID, so this runs
        # last. Safe by construction: ProgramNameSyncService reads the id
        # out of the converted text, rewrites only a
        # MOVE literal TO PROGRAM-NAME, and derives any VM..BD.. id found
        # INSIDE a quoted literal. The derived name is the same length as
        # the source name, so the fixed-format geometry is untouched and
        # no resequencing is needed. See CORRECTION 2.
        converted_text = self.program_name_sync.sync(converted_text)
        validation_messages.extend(self.program_name_sync.messages)

        return converted_text, validation_messages, operations

    # =================================================================
    # Per-program collaborator state
    # =================================================================
    def _reset_statement_transformer(self) -> None:
        """Clear the statement transformer's per-program state.

        Tolerates a transformer without reset() so a stub or an older
        build still runs; the attributes it owns are cleared directly in
        that case rather than left to accumulate. See CORRECTION 5.
        """
        transformer = self.idms_statement_transformer

        reset = getattr(transformer, "reset", None)
        if callable(reset):
            reset()
            return

        if hasattr(transformer, "messages"):
            transformer.messages = []
        if hasattr(transformer, "unmapped_records"):
            transformer.unmapped_records = set()

    def _publish_bounded_search_records(
        self,
        *,
        cobol_text: str,
        validation_messages: list[str],
    ) -> None:
        """Classify LR accesses once, then hand the result to the line pass.

        Always leaves the attribute DEFINED, so the reading end never has
        to distinguish "no analyser" from "analyser found nothing" by the
        absence of an attribute. Never raises: a failed classification
        falls back to the cursor path for every record and says so.
        See CORRECTION 6.
        """
        transformer = self.idms_statement_transformer
        setattr(transformer, BOUNDED_SEARCH_ATTRIBUTE, {})

        if self.lr_access_analyser is None:
            return

        try:
            found = self.lr_access_analyser.bounded_searches(cobol_text)
        except Exception as exc:  # noqa: BLE001
            validation_messages.append(
                ANALYSER_FAILED_TEMPLATE.format(reason=exc)
            )
            return

        records = dict(found or {})
        setattr(transformer, BOUNDED_SEARCH_ATTRIBUTE, records)

        validation_messages.extend(
            list(getattr(self.lr_access_analyser, "messages", []) or [])
        )

        if records:
            validation_messages.append(
                ANALYSER_RESULT_TEMPLATE.format(
                    count=len(records),
                    records=", ".join(sorted(records)),
                )
            )

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

    def _ensure_compiler_option(
        self,
        output_lines: list[str],
        validation_messages: list[str],
    ) -> None:
        """Insert the DB2 compiler option when the source carried none.

        CBL is a compiler directive and must precede IDENTIFICATION
        DIVISION, so the line is inserted immediately above it.

        The inserted line clones the sequence-area geometry of the
        IDENTIFICATION DIVISION line it sits above, exactly as every
        other insertion pass does. FinalSequenceResequencerService
        renumbers columns 1-6 and 73-80 afterwards, so the clone only
        has to be well-formed, not finally numbered.

        Never raises: a program with no IDENTIFICATION DIVISION is
        already broken for other reasons, and is reported rather than
        silently patched.
        """
        for index, line in enumerate(output_lines):
            logical = self.line_utils.logical_line(line).strip().upper()

            if not logical.startswith("IDENTIFICATION DIVISION"):
                continue

            output_lines.insert(
                index,
                self.line_utils.replace_logical_body(
                    original_line=line,
                    replacement_body=DB2_COMPILER_OPTION_LINE,
                ),
            )
            validation_messages.append(
                "Compiler option: source carried no CBL line; inserted "
                f"{DB2_COMPILER_OPTION_LINE} before IDENTIFICATION DIVISION."
            )
            return

        validation_messages.append(
            "Compiler option: no IDENTIFICATION DIVISION found, so "
            f"{DB2_COMPILER_OPTION_LINE} was not inserted."
        )

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
        """Remove COMP-3 and FILLER fields from WORKING-STORAGE entries.

        Removes:
        - Binary encoding: COMP-3, COMP-2, COMP-1, COMPUTATIONAL variants,
          PACKED-DECIMAL
        - FILLER field declarations

        Adds:
        - VALUE ZEROES to numeric PIC clauses without an existing VALUE

        Returns:
        - None if the line should be skipped (e.g. FILLER)
        - Modified line if changes were made
        - Original line if no change was needed
        """
        logical = self.line_utils.logical_line(line)
        logical_stripped = logical.strip()

        # Don't process non-data lines
        if not logical_stripped:
            return line

        # Skip comments
        if logical_stripped.startswith("*"):
            return line

        # Skip FILLER declarations entirely - None excludes from output
        if any(marker in logical for marker in ["FILLER", "filler"]):
            return None

        # Remove binary encoding clauses
        modified_logical = logical
        binary_patterns = [
            " COMP-3", " COMP-2", " COMP-1",
            " COMPUTATIONAL-3", " COMPUTATIONAL-2", " COMPUTATIONAL-1",
            " COMP-3.", " COMP-2.", " COMP-1.",
            " COMPUTATIONAL-3.", " COMPUTATIONAL-2.", " COMPUTATIONAL-1.",
            " PACKED-DECIMAL", " PACKED-DECIMAL.",
        ]

        for pattern in binary_patterns:
            modified_logical = modified_logical.replace(pattern, "")

        # Drop the sign on plain integer record-key fields
        # (PIC S9(n) -> PIC 9(n)). Signed decimal fields (PIC S9(x)V99,
        # e.g. money) keep their sign.
        if "V" not in modified_logical.upper():
            modified_logical = re.sub(
                r"(PIC\s+)S9", r"\g<1>9", modified_logical
            )

        # Add VALUE ZEROES to numeric fields
        if "PIC" in modified_logical and "VALUE" not in modified_logical:
            # Check if it's a numeric PIC
            if any(
                pic in modified_logical.upper()
                for pic in ["PIC 9", "PIC S9"]
            ):
                # Find the PIC clause and add VALUE ZEROES after it
                if "." in modified_logical:
                    # Has period - insert before it
                    modified_logical = modified_logical.replace(
                        ".",
                        " VALUE ZEROES.",
                    )
                else:
                    # No period - add VALUE ZEROES at end
                    modified_logical = (
                        modified_logical.rstrip() + " VALUE ZEROES"
                    )

        # If something changed, apply it to the original line's structure
        if modified_logical != logical:
            return self.line_utils.replace_logical_body(
                original_line=line,
                replacement_body=modified_logical.strip(),
            )

        return line


__all__ = [
    "CobolTransformer",
]
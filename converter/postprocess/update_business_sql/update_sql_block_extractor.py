# LOCATION: converter/postprocess/update_business_sql/update_sql_block_extractor.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

from patterns.update_business_sql_patterns import (
    CONTINUE_PATTERN,
    CONVERTED_MODIFY_COMMENT_PATTERN,
    DCL_HOST_GROUP_PATTERN,
    END_EVALUATE_PATTERN,
    END_EXEC_PATTERN,
    EVALUATE_SQLCODE_PATTERN,
    EXEC_SQL_START_PATTERN,
    EXEC_SQL_UPDATE_PATTERN,
    PARAGRAPH_HEADER_PATTERN,
    SQL_LOCATION_UPDATE_PATTERN,
    WHEN_ZERO_PATTERN,
)
from rules.update_business_sql_rules import (
    ADD_UPDATE_COUNTER_TEMPLATE,
    COMMIT_CHECK_IF_TEMPLATE,
    COMMIT_CHECK_PERFORM_TEMPLATE,
    END_IF_STATEMENT,
    FINAL_PERIOD_LINE,
    INITIALIZE_DCL_GROUP_TEMPLATE,
    NESTED_INDENT,
    PERFORM_TEMPLATE,
    SQL_ERROR_PARAGRAPH_NAMES,
    SQL_ERROR_ROUTINE_MARKER,
    TOKEN_STAR,
    DCLGEN_GROUP_PREFIX,
    DCLGEN_GROUP_SUFFIXES,
    ENABLE_STRUCTURAL_UPDATE_DETECTION,
    UPDATE_VERB_LOOKAHEAD,
)
from rules.update_restart_rules import (
    RESTART_PARAGRAPH_NAMES,
    UPDATE_COMMIT_THRESHOLD,
    UPDATE_RESTART_DIAGNOSTICS,
    UPDATE_RESTART_WS_NAMES,
)

SENTENCE_TERMINATOR = "."


class UpdateSqlBlockExtractor:
    """Detects and extracts the inline generated UPDATE SQL block.

    Update-postprocess only. Depends on the host class for line rendering
    (_active_line_like / _logical / _is_comment_line), name helpers
    (_update_paragraph_name / _paragraph_exists / _strip_existing_final_period /
    _normalize_update_paragraph_lines), and the shared line_utils.
    Owns no regex and no column geometry; all patterns/constants are external.

    CORRECTION 1 - the INITIALIZE idempotency check could never match
    -----------------------------------------------------------------
    The wanted text was rebuilt by SLICING a token:

        target = f"{TOKEN_INITIALIZE_DCL[:-3]} {dcl_group}".strip()

    "INITIALIZE DCL"[:-3] is "INITIALIZE " - carrying its own trailing
    space - so the f-string produced

        "INITIALIZE  DCLDZBFARTV"      <- two spaces

    No rendered COBOL line can equal that. The check answered "not
    present" on every pass, and a second run appended a second
    INITIALIZE to the same paragraph.

    The wanted text is now rendered from INITIALIZE_DCL_GROUP_TEMPLATE,
    the same template that WRITES the line. A detector derived from its
    own writer cannot drift from it. TOKEN_INITIALIZE_DCL is no longer
    referenced and has been dropped from the import list.

    CORRECTION 2 - the comparison was whitespace-sensitive
    -------------------------------------------------------
    Both sides are now whitespace-normalised, so a program that already
    carries a double-spaced INITIALIZE written by the defect above is
    still recognised as having one. Without this the fix would leave
    existing output permanently duplicated.

    CORRECTION 3 - placement refusals were silent
    ----------------------------------------------
    Four paths returned the lines unchanged and said nothing:

      - the extracted paragraph already exists
      - no DCLGEN host group was resolved
      - the process paragraph could not be located after extraction
      - the paragraph carries no executable line to insert before

    The middle two have a DATA consequence: without the INITIALIZE,
    every column the SET list does not assign keeps the previous row's
    value. A pass that declines to place it must say so.

    CORRECTION 4 - the span measured a STATEMENT and spliced a SENTENCE
    -------------------------------------------------------------------
    _find_sqlcode_evaluate_end returned `index + 1` at END-EVALUATE.
    END-EVALUATE closes the SCOPE; the period that closes the SENTENCE
    is a separate line, and the blank run after it separated this
    sentence from its neighbour. Both belonged to the text being
    extracted, and both were left behind:

        PERFORM 1100-UPDATE-DZBFAR.
        <- replacement ends here
        .                       <- orphan terminator
                                <- blank run, one longer on every run
        IF WS-TELLER > 99

    An orphan terminator is an empty sentence, and the blank run grew
    because each writer added its own separator on top of the one the
    previous writer never removed. The region now ends where the
    SENTENCE ends, and the replacement emits exactly ONE separator, so
    running twice measures the same region and writes the same lines.
    Idempotent by construction, not by a cleanup scan.

    CORRECTION 5 - two authors of the per-record commit cadence
    ------------------------------------------------------------
    Measured on VMDZ1567: VERWERKING carried TWO identical commit tests.
    The restart family writes one from PROCESS_TAIL_TEMPLATE and this
    pass writes another from COMMIT_CHECK_IF_TEMPLATE, and this pass
    runs LAST, so the restart injector could not clean up after it.

    The restart family OWNS the commit cadence when it is present -
    exactly as it owns the restart paragraphs. This pass keeps the
    PERFORM of the extracted paragraph, which is its own, and stands
    down from the commit block on the evidence that the cadence already
    exists.
    """

    #
    # Extraction
    #
    def _extract_inline_update_block(
        self, *, lines, process_paragraph, block_info, diagnostics
    ):
        block_start, block_end, record_name, dcl_group = block_info
        update_paragraph = self._update_paragraph_name(record_name)

        if self._paragraph_exists(lines, update_paragraph):
            diagnostics.append(
                f"Business update SQL: {update_paragraph} already exists; "
                "the inline block was left where it is."
            )
            return lines

        extracted_block = self._replace_update_success_continue(
            extracted_block=lines[block_start:block_end]
        )
        replacement = self._replacement_in_process(
            reference_line=lines[block_start],
            update_paragraph=update_paragraph,
            restart_owns_commit=self._restart_owns_commit(lines),
            diagnostics=diagnostics,
        )
        updated_lines = lines[:block_start] + replacement + lines[block_end:]
        process_range = self.line_utils.find_paragraph_range(
            updated_lines, process_paragraph
        )
        if process_range:
            p_start, p_end = process_range
            updated_lines = self._ensure_initialize_dcl_group(
                lines=updated_lines,
                start=p_start,
                end=p_end,
                dcl_group=dcl_group,
                diagnostics=diagnostics,
            )
        else:
            diagnostics.append(
                f"Business update SQL: {process_paragraph} could not be "
                "located after extraction; no INITIALIZE was placed. Any "
                "column the SET list does not assign will keep the "
                "previous row's value."
            )

        update_paragraph_lines = self._build_update_paragraph(
            paragraph_name=update_paragraph, extracted_block=extracted_block
        )
        insert_index = self._update_paragraph_insert_index(updated_lines)
        updated_lines = (
            updated_lines[:insert_index]
            + [""]
            + update_paragraph_lines
            + [""]
            + updated_lines[insert_index:]
        )
        diagnostics.append(UPDATE_RESTART_DIAGNOSTICS["business_update_extracted"])
        return updated_lines

    def _find_inline_update_block(
        self, *, lines, start, end, diagnostics=None, paragraph=""
    ):
        """Locate the inline business UPDATE block, or refuse and say so.

        THREE ANCHORS, IN ORDER OF RELIABILITY

            1. the generated marker comment   *DB2: Converted MODIFY for x
            2. the SQL-LOCATION literal       MOVE 'UPDATE-x' TO SQL-LOCATION
            3. the block STRUCTURE            EXEC SQL / UPDATE / END-EXEC /
                                              EVALUATE SQLCODE / END-EVALUATE

        CORRECTION - detection depended on a deletable comment.

        Anchors 1 and 2 are optional cosmetics. VMDZ1526 carried three
        SQL-LOCATION lines and was extracted; VMDZ1567 carried neither
        anchor, so its UPDATE stayed inline in VERWERKING, never reached
        _replace_update_success_continue, never received ADD 1 TO, and
        therefore produced no end-of-run total. One missing comment cost
        three features.

        Anchor 3 reads the shape _find_sqlcode_evaluate_end already
        recognises, so no new vocabulary is introduced.

        CORRECTION - the refusal was silent.

        The bare `return None` meant a program whose UPDATE was left
        inline looked identical to a program that had none. Every exit
        now reports.
        """
        for index in range(start + 1, end):
            logical = self._logical(lines[index])
            comment_match = CONVERTED_MODIFY_COMMENT_PATTERN.match(logical)
            location_match = SQL_LOCATION_UPDATE_PATTERN.match(logical)
            if not comment_match and not location_match:
                continue

            record_name = ""
            if comment_match:
                record_name = str(comment_match.group("record") or "").strip().upper()
            if not record_name and location_match:
                record_name = str(location_match.group("record") or "").strip().upper()
            if not record_name:
                continue

            block_start = index
            if location_match and index > start + 1:
                previous_logical = self._logical(lines[index - 1])
                if CONVERTED_MODIFY_COMMENT_PATTERN.match(previous_logical):
                    block_start = index - 1

            block_end = self._find_sqlcode_evaluate_end(
                lines=lines, start=index, limit=end
            )
            if block_end <= index:
                continue

            dcl_group = self._find_dcl_group(lines=lines[block_start:block_end])
            return block_start, block_end, record_name, dcl_group

        found = self._find_update_block_by_structure(
            lines=lines, start=start, end=end
        )
        if found:
            block_start, block_end, record_name, dcl_group = found
            self._say(
                diagnostics, "business_update_structural", paragraph=paragraph
            )
            return block_start, block_end, record_name, dcl_group

        self._say(diagnostics, "business_update_not_found", paragraph=paragraph)
        return None

    def _find_update_block_by_structure(self, *, lines, start, end):
        """The UPDATE block read from its own shape. No comment needed."""
        if not ENABLE_STRUCTURAL_UPDATE_DETECTION:
            return None

        for index in range(start + 1, end):
            if not EXEC_SQL_START_PATTERN.match(self._logical(lines[index])):
                continue
            if not self._opens_an_update(lines=lines, index=index, end=end):
                continue

            block_end = self._find_sqlcode_evaluate_end(
                lines=lines, start=index, limit=end
            )
            if block_end <= index:
                continue

            dcl_group = self._find_dcl_group(lines=lines[index:block_end])
            record_name = self._record_from_group(dcl_group)
            if not record_name:
                continue

            return index, block_end, record_name, dcl_group

        return None

    def _opens_an_update(self, *, lines, index, end):
        """True when this EXEC SQL begins an UPDATE statement."""
        limit = min(index + 1 + UPDATE_VERB_LOOKAHEAD, end)
        for position in range(index + 1, limit):
            logical = self._logical(lines[position])
            if EXEC_SQL_UPDATE_PATTERN.match(logical):
                return True
            if END_EXEC_PATTERN.match(logical):
                return False
        return False

    @staticmethod
    def _record_from_group(dcl_group):
        """DCLDZBFARTV -> DZBFAR. Derived, never invented.

        Used only when no IDMS record name survives anywhere in the
        program. The paragraph is then named from the DB2 group, which
        is a faithful name for what the paragraph actually updates.
        """
        name = str(dcl_group or "").strip().upper()
        if not name.startswith(DCLGEN_GROUP_PREFIX):
            return ""
        name = name[len(DCLGEN_GROUP_PREFIX):]
        for suffix in DCLGEN_GROUP_SUFFIXES:
            if name.endswith(suffix) and len(name) > len(suffix):
                return name[: -len(suffix)]
        return name

    @staticmethod
    def _say(diagnostics, key, **values):
        """Report, or stay silent only because no collector was given."""
        if diagnostics is None:
            return
        template = UPDATE_RESTART_DIAGNOSTICS.get(key, "")
        if not template:
            diagnostics.append(f"Update SQL: {key} {values}")
            return
        try:
            diagnostics.append(template.format(**values))
        except (IndexError, KeyError):
            diagnostics.append(template)

    #
    # Span measurement
    #
    def _find_sqlcode_evaluate_end(self, *, lines, start, limit):
        seen_exec_sql = seen_update = seen_end_exec = seen_evaluate = False

        for index in range(start, limit):
            logical = self._logical(lines[index])
            if EXEC_SQL_START_PATTERN.match(logical):
                seen_exec_sql = True
                continue
            if seen_exec_sql and EXEC_SQL_UPDATE_PATTERN.match(logical):
                seen_update = True
                continue
            if seen_update and END_EXEC_PATTERN.match(logical):
                seen_end_exec = True
                continue
            if seen_end_exec and EVALUATE_SQLCODE_PATTERN.match(logical):
                seen_evaluate = True
                continue
            if seen_evaluate and END_EVALUATE_PATTERN.match(logical):
                return self._sentence_end(lines=lines, index=index, limit=limit)

        return -1

    def _sentence_end(self, *, lines, index, limit):
        """End of the SENTENCE that closed at `index`. See CORRECTION 4.

        END-EVALUATE closes the SCOPE. The period that closes the
        SENTENCE stands on its own line, and the blank run after it
        separated this sentence from its neighbour. Both belong to the
        text being extracted.

        Conservative by design: only a line whose WHOLE logical body is
        the terminator is consumed, and the walk stops at the first
        comment or executable line, so no statement and no decision
        record can be swallowed.
        """
        cursor = min(index + 1, limit)

        while cursor < limit:
            if self._is_comment_line(lines[cursor]):
                break
            body = " ".join(str(self._logical(lines[cursor]) or "").split())
            if not body:
                break
            if body == SENTENCE_TERMINATOR:
                cursor += 1
            break

        while cursor < limit:
            if self._is_comment_line(lines[cursor]):
                break
            if str(self._logical(lines[cursor]) or "").strip():
                break
            cursor += 1

        return cursor

    #
    # Rendering
    #
    def _replacement_in_process(
        self,
        *,
        reference_line,
        update_paragraph,
        restart_owns_commit: bool = False,
        diagnostics=None,
    ):
        """The call site that replaces the extracted inline UPDATE.

        Ends with exactly ONE separator. The span it replaces now
        absorbs the sentence terminator AND the blank run that followed
        it (CORRECTION 4), so this method is the single owner of the gap
        between the call site and whatever comes next. One owner, one
        blank, no drift on a second run.

        `restart_owns_commit` defaults to False so a program WITHOUT
        restart control is unaffected and still receives its commit
        cadence from here (CORRECTION 5).
        """
        names = UPDATE_RESTART_WS_NAMES

        output = [
            self._active_line_like(
                reference_line=reference_line,
                body=PERFORM_TEMPLATE.format(paragraph=update_paragraph),
            ),
        ]

        if restart_owns_commit:
            self._say(diagnostics, "commit_owned_by_restart")
            output.append("")
            return output

        output.extend(
            [
                "",
                self._active_line_like(
                    reference_line=reference_line,
                    body=COMMIT_CHECK_IF_TEMPLATE.format(
                        counter=names["commit_counter"],
                        threshold=UPDATE_COMMIT_THRESHOLD,
                    ),
                ),
                self._active_line_like(
                    reference_line=reference_line,
                    body=COMMIT_CHECK_PERFORM_TEMPLATE.format(
                        indent=NESTED_INDENT,
                        commit_paragraph=RESTART_PARAGRAPH_NAMES["commit"],
                    ),
                ),
                self._active_line_like(
                    reference_line=reference_line, body=END_IF_STATEMENT
                ),
                "",
            ]
        )
        return output

    def _restart_owns_commit(self, lines) -> bool:
        """True when the restart family already performs the commit paragraph.

        EVIDENCE, NOT A FLAG

        No new vocabulary and no new guess: the commit paragraph name is
        already imported here, and the restart tail performs it inside the
        business paragraph. If that PERFORM exists anywhere in the program,
        the cadence exists and a second one is a duplicate.

        READ THROUGH THE HOST'S LINE READER

        `self.line_utils.logical` does not strip the fixed-format sequence
        area, so an exact comparison measured

            "002310        PERFORM 800-PROCESS-COMMIT        02310000"

        against "PERFORM 800-PROCESS-COMMIT" and never matched. The host's
        _logical() is the sequence-aware reader this module uses everywhere
        else, and the body is whitespace-collapsed before the test, so
        neither column geometry nor indentation can hide the evidence.
        """
        commit = str(RESTART_PARAGRAPH_NAMES.get("commit", "") or "").upper()
        if not commit:
            return False

        target = f"PERFORM {commit}"

        for line in lines or []:
            if self._is_comment_line(line):
                continue

            logical = " ".join(str(self._logical(line) or "").upper().split())
            if not logical:
                continue

            if target in logical:
                return True

        return False

    def _build_update_paragraph(self, *, paragraph_name, extracted_block):
        cleaned_block = self._strip_existing_final_period(extracted_block)
        output = [f"{paragraph_name}.", ""]
        output.extend(cleaned_block)
        output.append(FINAL_PERIOD_LINE)
        return self._normalize_update_paragraph_lines(output)

    def _replace_update_success_continue(self, *, extracted_block):
        names = UPDATE_RESTART_WS_NAMES
        output: list[str] = []
        index = 0

        while index < len(extracted_block):
            line = extracted_block[index]
            logical = self._logical(line)

            if WHEN_ZERO_PATTERN.match(logical):
                output.append(line)
                if index + 1 < len(extracted_block):
                    next_logical = self._logical(extracted_block[index + 1])
                    if CONTINUE_PATTERN.match(next_logical):
                        output.append(
                            self._active_line_like(
                                reference_line=extracted_block[index + 1],
                                body=ADD_UPDATE_COUNTER_TEMPLATE.format(
                                    counter=names["update_counter"]
                                ),
                            )
                        )
                        index += 2
                        continue
                index += 1
                continue

            output.append(line)
            index += 1

        return output

    #
    # INITIALIZE placement
    #
    def _ensure_initialize_dcl_group(
        self, *, lines, start, end, dcl_group, diagnostics=None
    ):
        notes = diagnostics if diagnostics is not None else []

        if not dcl_group:
            notes.append(
                "Business update SQL: no DCLGEN host group was resolved for "
                "the extracted UPDATE; no INITIALIZE was placed. Any column "
                "the SET list does not assign will keep the previous row's "
                "value."
            )
            return lines

        wanted = self._initialize_key(
            INITIALIZE_DCL_GROUP_TEMPLATE.format(group=dcl_group)
        )

        for index in range(start, end):
            if self._initialize_key(self._logical(lines[index])) == wanted:
                notes.append(
                    f"Business update SQL: INITIALIZE {dcl_group} is already "
                    "present; no second statement added."
                )
                return lines

        insert_index = self._first_executable_line_index(
            lines=lines, start=start, end=end
        )
        if insert_index < 0:
            notes.append(
                "Business update SQL: the process paragraph carries no "
                f"executable line; INITIALIZE {dcl_group} was not placed."
            )
            return lines

        initialize_line = self._active_line_like(
            reference_line=lines[insert_index],
            body=INITIALIZE_DCL_GROUP_TEMPLATE.format(group=dcl_group),
        )
        notes.append(
            f"Business update SQL: placed INITIALIZE {dcl_group} as the "
            "first statement of the process paragraph."
        )
        return lines[:insert_index] + [initialize_line, ""] + lines[insert_index:]

    @staticmethod
    def _initialize_key(text):
        """Whitespace- and terminator-insensitive comparison key.

        Collapsing runs of blanks is what lets this recognise an
        "INITIALIZE  <group>" written by the double-space defect, so a
        program converted before the fix is repaired rather than given a
        second statement.
        """
        collapsed = " ".join(str(text or "").split())
        return collapsed.upper().rstrip(SENTENCE_TERMINATOR).strip()

    def _first_executable_line_index(self, *, lines, start, end):
        for index in range(start + 1, end):
            line = lines[index]
            logical = self._logical(line).strip()
            if not logical or self._is_comment_line(line):
                continue
            if logical.startswith(TOKEN_STAR):
                continue
            if PARAGRAPH_HEADER_PATTERN.match(logical):
                continue
            return index
        return -1

    #
    # Placement of the generated paragraph
    #
    def _update_paragraph_insert_index(self, lines):
        sqlerror_index = self._find_sqlerror_routine_index(lines)
        if sqlerror_index >= 0:
            return sqlerror_index

        restart_abend_range = self.line_utils.find_paragraph_range(
            lines, RESTART_PARAGRAPH_NAMES["abend"]
        )
        if restart_abend_range:
            return restart_abend_range[1]

        return len(lines)

    def _find_sqlerror_routine_index(self, lines):
        for index, line in enumerate(lines):
            logical = self._logical(line).upper().rstrip(SENTENCE_TERMINATOR)
            if logical in set(SQL_ERROR_PARAGRAPH_NAMES):
                return index
            if SQL_ERROR_ROUTINE_MARKER in logical:
                return index
        return -1

    def _find_dcl_group(self, lines):
        for line in lines:
            logical = self._logical(line)
            for match in DCL_HOST_GROUP_PATTERN.finditer(logical):
                group = str(match.group(0) or "").strip().upper()
                if group:
                    return group
        return ""


__all__ = ["UpdateSqlBlockExtractor"]
# LOCATION: converter/transformers/lrf_path_expander.py
# ACTION: REPLACE ENTIRE FILE
"""Expands LRF syntax into the classic IDMS syntax the converter knows.

NO-LRF CONTRACT
---------------
With no logical record metadata, or with metadata but no LRF syntax in the
program, expand() returns the source text byte-for-byte. The converter
therefore behaves exactly as it did before LRF support existed.

NAME FORM
---------
Generated names are COBOL form (UPPERCASE, hyphens). NameNormalizer is not
used here: normalize() yields DB2 column form and would emit VMBTL03_R01.

COMMENT FORM
------------
A generated comment line carries '*' in the indicator column and its
marker starts immediately at column 8, so the output reads

      *DB2: Expanded LRF ...
      *DB2-KEEP: ...

which matches the marker text declared in rules/.

LR-STATUS CLASSIFICATION
------------------------
Three classes and NO DEFAULT. See _status_token for the three defects a
default produced. An unrecognised literal is left exactly as written so
the surviving LR-STATUS is reported rather than silently mistranslated.

A condition this module cannot rewrite SAFELY is also left unchanged -
see the abbreviated combined relation guard in _rewrite_lr_status. A
half-rewritten condition compiles to nonsense; an untouched one is a
finding a reviewer can act on.

CORRECTION 1 - A PERIOD WAS APPENDED TO EVERY GENERATED STATEMENT
------------------------------------------------------------------
``_statement`` ended every emitted line with STATEMENT_TERMINATOR
unconditionally. That is right for a statement that stands alone and
WRONG for one inside an inline block. VM4BD310 carries::

    PERFORM UNTIL LR-STATUS = 'NO-MORE-VMBEVEF'
               OR CT-EVENT OF VMBEVEF = '0092'
       OBTAIN NEXT VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF      <- no period
    END-PERFORM.

and the expansion produced::

    PERFORM UNTIL DB-END-OF-SET
               OR CT-EVENT OF VMBEVEF = '0092'
      *DB2: Expanded LRF NEXT ...
       OBTAIN NEXT VMBEVEF WITHIN VMBEFF-VMBEVEF.               <- period ADDED
    END-PERFORM.

A period closes the COBOL SENTENCE. The ``END-PERFORM`` on the next line
then has no ``PERFORM`` to close and the program does not compile. The
generated statement now MIRRORS the source statement's termination.

CORRECTION 2 - A KEYED PARENT WAS DROPPED, SILENTLY  [BLOCKER 1]
------------------------------------------------------------------
``LrfAccessStep.is_renderable`` requires BOTH a record and a ``within``,
and parent selection filters on it. A SET or AREA access has a
``within``. A CALC access does not::

    OBTAIN FIRST VMBEFF WHERE CALCKEY EQ KY-EFFECT OF VMBEFF OF LR
    IF VMBEFF-VMBEVEF IS EMPTY
    OBTAIN EACH VMBEVEF WITHIN VMBEFF-VMBEVEF

So for ALL-VMBEVEF-BY-VMBEFF only the second step survived the filter,
``plan.parent`` stayed None, the parent branch below never fired, no
``parent_emitted`` message was logged, and VMDZ4310 shipped with NO read
of DZBEFFTV at all - while twelve of its output fields are moved out of
DCLDZBEFFTV, a group nothing populates.

THE GUARD IS NOT THE DEFECT. Rendering ``FIND FIRST VMBEFF WITHIN ''``
produces COBOL that does not compile. The MODEL had no vocabulary for a
keyed access. ``LrfPathResolver`` now supplies ``plan.calc_parent``, and
``_render_parent`` renders it as ``OBTAIN CALC <record>``.

CORRECTION 2a - THE DOWNSTREAM CLAIM IN THIS DOCSTRING WAS FALSE
-----------------------------------------------------------------
This file used to assert that
``IdmsStatementTransformer._convert_obtain_calc`` "already turns
OBTAIN CALC into a singleton SELECT". It does NOT, and that wrong
assumption cost a full debugging cycle. Measured, that converter emits::

    *DB2: Removed OBTAIN CALC SELECT for {record}.
    *DB2: Direct UPDATE will use mapped composite key WHERE clause.
    CONTINUE.

which is the UPDATE semantic - correct for a direct
``UPDATE ... WHERE <composite key>``, and wrong for a retrieval program
where the OBTAIN CALC is the ONLY population of the DCLGEN group. It is
registered in ``_plain_converters`` with no program-kind discrimination
because ``_hand_off_program_kind`` has exactly one call site and the
statement transformer is not it.

So the statement this module emits was correct and was then DELETED
downstream: the removal comment is consumed by
``REMOVED_OBTAIN_CALC_PATTERN`` and the orphaned ``CONTINUE`` by
``_maybe_skip_redundant_continue``, leaving no trace at all.

That is fixed in the transformer, not here. This module's contract is
unchanged: emit correct classic IDMS and publish what it emitted.

CORRECTION 3 - FOUR DIAGNOSTICS PRODUCED NOTHING
--------------------------------------------------
``_log`` resolved a missing template with ``.get(key, "")`` and returned.
``status_refused_abbreviated`` and ``statement_unterminated`` were never
declared in LRF_EXPANSION_MESSAGES - ``refused_abbreviated`` lives in
LR_STATUS_TOKEN_MESSAGES, a DIFFERENT catalogue owned by the replacer -
so both counters incremented and reported nothing. The keys are declared
now, and an unmapped key is REPORTED as an unmapped key. That is the
difference between a visible gap and a lost finding, and it is the same
correction already made to LrfUpdateExpander.

CORRECTION 4 - A REFUSED WRAPPED STATEMENT LOST ITS CONTINUATION LINES
------------------------------------------------------------------------
``_expand_obtain_multiline`` absorbed every continuation line into
``pending_consumed``, and on refusal ``_keep`` commented only the FIRST
physical line. Every other line of the statement was DELETED from the
output with no comment and no diagnostic. A refusal must leave the whole
source statement behind, so the span is kept.

CORRECTION 5 - COMMENTS INSIDE A WRAPPED STATEMENT WERE DELETED
-----------------------------------------------------------------
The same scan skipped comment lines when assembling the text but still
marked them consumed. They are now carried and re-emitted after the
rendered block.

CORRECTION 6 - THE CONTINUATION SCAN WAS UNBOUNDED
----------------------------------------------------
``while STATEMENT_TERMINATOR not in assembled`` ran to end-of-file on a
statement missing its period, absorbing - and therefore deleting - the
rest of the program. It is capped at MULTILINE_WHERE_SCAN_LIMIT, and a
runaway is kept intact and REPORTED. The test is also now
``_is_terminated`` (ends with a period) rather than ``'.' in text``,
which stopped at the first interior period.

CORRECTION 7 - A REFUSAL WAS SILENT AND MISLABELLED
-----------------------------------------------------
The "no readable keyword" path in ``_expand_obtain_multiline`` logged
nothing and formatted the LOGICAL RECORD name into a template slot
named ``{keyword}``, so the one diagnostic a reviewer would search for
named the wrong thing. It reports ``keyword_unreadable`` with the LR
name in a slot called ``lr``.

CORRECTION 8 - WHAT THIS PASS GENERATED IS NOW PUBLISHED
----------------------------------------------------------
``calc_parent_records`` carries every record for which this pass emitted
an ``OBTAIN CALC``. The downstream converter needs to tell an
LRF-GENERATED keyed read from a hand-written one - VMBWCEF in VM4BD302
is hand-written and must keep its current behaviour - and adjacency to
the marker comment is not a safe test.

A marker sitting immediately above the statement is true at the point
the transformer runs and stops being true the moment any pass reorders
or re-wraps it. A published set is order-independent, survives the
shared statement joiner work, and mirrors
``IdmsStatementTransformer.unmapped_records``, a pattern that class
already uses. Nothing reads it yet; wiring it is a separate, separately
measured change.

DEFERRED, DELIBERATELY
----------------------
``_is_comment`` free-format fallback and ``_contains_lrf_syntax`` raw-line
matching are both members of the physical-line defect family. They are
retired by the shared statement joiner, as a separately measured change,
and are left here with their defects documented so the keyed-parent work
can be measured alone.
"""

from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from patterns.lrf_program_patterns import (
    BARE_OF_LR_PATTERN,
    LR_ERASE_WHERE_PATTERN,
    LR_OBTAIN_WHERE_PATTERN,
    LR_OBTAIN_WHERE_PREFIX_PATTERN,
    LR_STATUS_ABBREVIATED_PATTERN,
    LR_STATUS_CONDITION_PATTERN,
    LR_STATUS_TOKEN_PATTERN,
    OF_LR_SUFFIX_PATTERN,
)
from rules.lrf_conversion_rules import (
    ENABLE_LRF_PATH_EXPANSION,
    END_OF_SET_LITERAL_FRAGMENTS,
    END_OF_SET_TOKEN,
    EXPANDED_CALC_PARENT_TEMPLATE,
    EXPANDED_FILTER_TEMPLATE,
    EXPANDED_OBTAIN_TEMPLATE,
    EXPANDED_PARENT_TEMPLATE,
    FIND_FIRST_TEMPLATE,
    FOUND_LITERAL_FRAGMENTS,
    FOUND_NEGATION_FRAGMENTS,
    LRF_EXPANSION_MESSAGES,
    MULTILINE_WHERE_SCAN_LIMIT,
    NEGATION_FRAGMENTS,
    NOT_FOUND_LITERAL_FRAGMENTS,
    OBTAIN_CALC_TEMPLATE,
    OBTAIN_FIRST_TEMPLATE,
    OBTAIN_NEXT_TEMPLATE,
    RECORD_FOUND_TOKEN,
    RECORD_NOT_FOUND_TOKEN,
    REQUIRE_MAPPED_DRIVING_RECORD,
    SKIPPED_CALC_PARENT_TEMPLATE,
    SKIPPED_NO_KEYWORD_TEMPLATE,
    SKIPPED_NO_PATH_TEMPLATE,
    SKIPPED_NO_RECORD_TEMPLATE,
    SKIPPED_UNMAPPED_TEMPLATE,
    STATEMENT_TERMINATOR,
    UNMAPPED_DIAGNOSTIC_TEMPLATE,
    UNRENDERABLE_DIAGNOSTIC_TEMPLATE,
)

PROCEDURE_DIVISION_TOKEN = "PROCEDURE DIVISION"
COMMENT_INDICATORS = ("*", "/", "D", "-")
COMMENT_PREFIX_COLUMNS = "      "
MODE_NEXT = "NEXT"
DEFAULT_INDENT = "    "


def cobol_name(value: str) -> str:
    """UPPERCASE COBOL/IDMS form: hyphens, never underscores."""
    return str(value or "").strip().upper().replace("_", "-")


class LrfPathExpander:
    """Rewrites LRF program syntax into classic IDMS syntax."""

    def __init__(
        self,
        *,
        path_resolver=None,
        fixed_format: FixedFormatLineService | None = None,
    ) -> None:
        self.path_resolver = path_resolver
        self.fixed_format = fixed_format or FixedFormatLineService()
        self.messages: list[str] = []

        # COBOL-form records for which this pass emitted an OBTAIN CALC
        # parent access. PUBLISHED, not inferred - see CORRECTION 8.
        # Read by the pipeline and handed to the statement transformer
        # so a hand-written OBTAIN CALC keeps its existing behaviour.
        self.calc_parent_records: set[str] = set()

    # ---------------------------------------------------------- public
    def expand(self, cobol_text: str) -> str:
        self.messages = []
        self.calc_parent_records = set()

        text = str(cobol_text or "")
        if not text.strip() or not ENABLE_LRF_PATH_EXPANSION:
            return text

        if self.path_resolver is None or self.path_resolver.is_empty():
            if self._contains_lrf_syntax(text):
                self._log("no_logical_records")
            return text

        if not self._contains_lrf_syntax(text):
            return text

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")

        output: list[str] = []
        in_procedure = False
        expanded = 0
        skipped = 0
        status_rewrites = 0
        status_refusals = 0
        qualifier_strips = 0
        unterminated = 0
        # Source line indices already absorbed as continuation lines of a
        # multi-line OBTAIN ... WHERE statement. Every absorbed line is
        # either rendered, kept, or re-emitted as a carried comment -
        # none is dropped. See CORRECTION 4 and CORRECTION 5.
        pending_consumed: set[int] = set()

        for index, line in enumerate(lines):
            if index in pending_consumed:
                continue

            logical = self._logical(line)
            upper = logical.upper()

            if PROCEDURE_DIVISION_TOKEN in upper:
                in_procedure = True
                output.append(line)
                continue

            if not in_procedure or self._is_comment(line) or not logical:
                output.append(line)
                continue

            obtain = LR_OBTAIN_WHERE_PATTERN.match(logical)
            if obtain:
                rendered, ok = self._expand_obtain(line, obtain)
                output.extend(rendered)
                expanded += 1 if ok else 0
                skipped += 0 if ok else 1
                unterminated += 0 if self._is_terminated(logical) else 1
                continue

            prefix = LR_OBTAIN_WHERE_PREFIX_PATTERN.match(logical)
            if prefix:
                consumed, rendered, ok, closed = (
                    self._expand_obtain_multiline(
                        lines=lines,
                        start_index=index,
                        first_logical=logical,
                        prefix=prefix,
                    )
                )
                output.extend(rendered)
                expanded += 1 if ok else 0
                skipped += 0 if ok else 1
                unterminated += 0 if closed else 1
                for offset in range(1, consumed):
                    pending_consumed.add(index + offset)
                continue

            erase = LR_ERASE_WHERE_PATTERN.match(logical)
            if erase:
                rendered, ok = self._expand_erase(line, erase)
                output.extend(rendered)
                expanded += 1 if ok else 0
                skipped += 0 if ok else 1
                unterminated += 0 if self._is_terminated(logical) else 1
                continue

            # Counted HERE, not inside _rewrite_lr_status, so that method
            # keeps its (text, hits) signature and stays a pure function.
            # A refusal with no diagnostic is indistinguishable from a
            # line the pass never looked at.
            if LR_STATUS_ABBREVIATED_PATTERN.search(logical):
                status_refusals += 1

            new_logical, hits = self._rewrite_lr_status(logical)
            status_rewrites += hits

            new_logical, strips = self._strip_of_lr(new_logical)
            qualifier_strips += strips

            if new_logical != logical:
                output.append(self._replace_body(line, new_logical))
            else:
                output.append(line)

        # ---- diagnostics, flushed once, in a fixed order -------------
        if status_rewrites:
            self._log("status_rewritten", count=status_rewrites)
        if status_refusals:
            self._log("status_refused_abbreviated", count=status_refusals)
        if qualifier_strips:
            self._log("qualifier_stripped", count=qualifier_strips)
        if unterminated:
            self._log("statement_unterminated", count=unterminated)
        if expanded or skipped:
            self._log("summary", expanded=expanded, skipped=skipped)

        if not (expanded or skipped or status_rewrites or qualifier_strips):
            # Nothing moved. Return the ORIGINAL object, never a rejoined
            # copy - a rejoin normalises line endings and a trailing
            # newline, which is a byte change the NO-LRF contract forbids.
            return text

        return "\n".join(output).rstrip() + "\n"

    # ------------------------------------------------------- expansion
    def _expand_obtain(self, line: str, match) -> tuple[list[str], bool]:
        mode = str(match.group("mode") or "").upper()
        lr_name = cobol_name(match.group("lr"))
        keyword = cobol_name(match.group("keyword"))

        # match.string IS the logical line the pattern was matched
        # against, so the source terminator is available here without
        # changing the caller.
        terminated = self._is_terminated(match.string)

        return self._render_obtain(
            line=line,
            mode=mode,
            lr_name=lr_name,
            keyword=keyword,
            extra_conditions="",
            terminated=terminated,
        )

    def _expand_obtain_multiline(
        self,
        *,
        lines: list[str],
        start_index: int,
        first_logical: str,
        prefix,
    ) -> tuple[int, list[str], bool, bool]:
        """Expand an OBTAIN ... WHERE that spans more than one line.

        Returns (lines_consumed, rendered, ok, closed).

        ``lines_consumed`` counts the source lines the statement spans,
        so the caller can skip the continuation lines already absorbed.
        ``closed`` reports whether the assembled source statement ended
        in a period.

        CORRECTION 4 / 5 / 6 / 7 apply here. Every absorbed line is
        accounted for: it is either folded into the rendered statement,
        kept verbatim on refusal, or - for a comment - carried through
        and re-emitted after the rendered block. The scan is bounded,
        and a runaway refuses rather than eating the program.
        """
        mode = str(prefix.group("mode") or "").upper()
        lr_name = cobol_name(prefix.group("lr"))

        assembled = first_logical
        consumed = 1
        carried_comments: list[str] = []

        while not self._is_terminated(assembled):
            if consumed >= MULTILINE_WHERE_SCAN_LIMIT:
                # CORRECTION 6. Refuse, keep the whole span, and say so.
                self._log(
                    "statement_runaway",
                    line=start_index + 1,
                    limit=MULTILINE_WHERE_SCAN_LIMIT,
                )
                return (
                    consumed,
                    self._keep_span(
                        lines,
                        start_index,
                        consumed,
                        SKIPPED_NO_KEYWORD_TEMPLATE.format(lr=lr_name),
                    ),
                    False,
                    False,
                )

            nxt_index = start_index + consumed
            if nxt_index >= len(lines):
                break

            raw = lines[nxt_index]
            consumed += 1

            if self._is_comment(raw):
                # CORRECTION 5. A comment inside a wrapped statement is
                # authored text. It was absorbed and deleted.
                carried_comments.append(raw)
                continue

            nxt = self._logical(raw)
            if not nxt:
                continue

            assembled = f"{assembled} {nxt}".strip()

        closed = self._is_terminated(assembled)
        keyword, extra = self._split_where(assembled)

        if not keyword:
            # CORRECTION 7. This refusal logged nothing, and formatted
            # the LOGICAL RECORD name into a slot labelled 'keyword'.
            self._log("keyword_unreadable", lr=lr_name)
            rendered = self._keep_span(
                lines,
                start_index,
                consumed,
                SKIPPED_NO_KEYWORD_TEMPLATE.format(lr=lr_name),
            )
            rendered.extend(carried_comments)
            return consumed, rendered, False, closed

        rendered, ok = self._render_obtain(
            line=lines[start_index],
            mode=mode,
            lr_name=lr_name,
            keyword=cobol_name(keyword),
            extra_conditions=extra,
            terminated=closed,
            keep_span=(lines, start_index, consumed),
        )
        rendered.extend(carried_comments)
        return consumed, rendered, ok, closed

    @staticmethod
    def _split_where(assembled: str) -> tuple[str, str]:
        """Split 'OBTAIN <mode> <lr> WHERE <keyword> [AND <rest>].' into
        (keyword, extra_conditions). extra_conditions keeps the original
        text after the keyword, without the leading connector or the
        trailing period.
        """
        upper = assembled.upper()
        where_at = upper.find(" WHERE ")
        if where_at < 0:
            return "", ""

        clause = assembled[where_at + len(" WHERE "):].strip()
        clause = clause.rstrip().rstrip(STATEMENT_TERMINATOR).strip()

        parts = clause.split(None, 1)
        if not parts:
            return "", ""

        keyword = parts[0]
        rest = parts[1].strip() if len(parts) > 1 else ""

        # Drop a leading AND / OR connector left after the path keyword.
        for connector in ("AND ", "OR "):
            if rest.upper().startswith(connector):
                rest = rest[len(connector):].strip()
                break

        return keyword, rest

    def _render_obtain(
        self,
        *,
        line: str,
        mode: str,
        lr_name: str,
        keyword: str,
        extra_conditions: str,
        terminated: bool,
        keep_span: tuple | None = None,
    ) -> tuple[list[str], bool]:
        """Render one expanded access, or keep and comment the source.

        ``keep_span`` is (lines, start_index, consumed) for a statement
        that spans several physical lines. When a refusal fires, the
        WHOLE span is kept. Without it the continuation lines were
        deleted with no comment and no diagnostic - CORRECTION 4.
        """
        plan = self.path_resolver.plan_for_keyword(keyword)

        if plan is None:
            self._log("keyword_not_found", keyword=keyword)
            return self._refuse(
                line, keep_span,
                SKIPPED_NO_PATH_TEMPLATE.format(keyword=keyword),
            ), False

        if not plan.is_usable:
            self._log("keyword_not_found", keyword=keyword)
            return self._refuse(
                line, keep_span,
                SKIPPED_NO_RECORD_TEMPLATE.format(keyword=keyword),
            ), False

        record = plan.driving.record_name
        within = plan.driving.within_name

        if REQUIRE_MAPPED_DRIVING_RECORD and not (
            self._record_is_mapped(record)
        ):
            self._log("record_unmapped", record=record, keyword=keyword)
            return self._refuse(
                line, keep_span,
                SKIPPED_UNMAPPED_TEMPLATE.format(record=record),
            ), False

        rendered: list[str] = []
        rendered.extend(
            self._comment(line, EXPANDED_OBTAIN_TEMPLATE.format(
                mode=mode, lr=lr_name, keyword=keyword,
                record=record, within=within,
            ))
        )

        # Preserve extra WHERE conditions so they are never silently lost.
        if extra_conditions:
            rendered.extend(
                self._comment(line, EXPANDED_FILTER_TEMPLATE.format(
                    keyword=keyword, conditions=extra_conditions,
                ))
            )

        # A parent positions the set ONCE. On NEXT the set is already
        # positioned and re-reading the parent would restart the sweep.
        if mode != MODE_NEXT:
            rendered.extend(
                self._render_parent(
                    line=line,
                    plan=plan,
                    keyword=keyword,
                    terminated=terminated,
                )
            )

        template = (
            OBTAIN_NEXT_TEMPLATE if mode == MODE_NEXT
            else OBTAIN_FIRST_TEMPLATE
        )
        rendered.extend(
            self._statement(
                line,
                template.format(record=record, within=within),
                terminate=terminated,
            )
        )

        self._log(
            "expanded",
            mode=mode, lr=lr_name, keyword=keyword,
            record=record, within=within,
        )
        return rendered, True

    def _render_parent(
        self,
        *,
        line: str,
        plan,
        keyword: str,
        terminated: bool,
    ) -> list[str]:
        """Render the parent access that precedes the driving step.

        TWO SHAPES, because the subschema has two.

        A SET or AREA parent carries a container and renders as
        ``FIND FIRST <record> WITHIN <set>``.

        A CALC parent carries a KEY and no container. It renders as
        ``OBTAIN CALC <record>`` - never as a WITHIN access, which would
        emit ``WITHIN ''`` and not compile. That refusal is exactly what
        ``LrfAccessStep.is_renderable`` enforces, and it is correct; the
        gap was that the model had no second shape. See CORRECTION 2.

        The record is recorded in ``calc_parent_records`` so a
        downstream pass can tell an LRF-generated keyed read from a
        hand-written one. See CORRECTION 8.

        ``calc_parent`` is read with getattr so this module still loads,
        and simply renders no keyed parent, against a resolver that
        predates the field.
        """
        if plan.parent is not None:
            parent = plan.parent
            rendered = self._comment(
                line,
                EXPANDED_PARENT_TEMPLATE.format(
                    keyword=keyword, record=parent.record_name,
                ),
            )
            rendered.extend(
                self._statement(
                    line,
                    FIND_FIRST_TEMPLATE.format(
                        record=parent.record_name,
                        within=parent.within_name,
                    ),
                    terminate=terminated,
                )
            )
            self._log(
                "parent_emitted",
                record=parent.record_name,
                within=parent.within_name,
                keyword=keyword,
            )
            return rendered

        calc = getattr(plan, "calc_parent", None)
        if calc is None:
            return []

        record = str(getattr(calc, "record_name", "") or "").strip()
        if not record:
            return []

        if REQUIRE_MAPPED_DRIVING_RECORD and not (
            self._record_is_mapped(record)
        ):
            # Refuse LOUDLY. Emitting OBTAIN CALC for a record with no
            # Sheet Mapping entry pushes the failure one pass
            # downstream, where it resolves to an empty table and the
            # statement is commented out with no explanation of which
            # path wanted it.
            self._log("calc_parent_unmapped", record=record, keyword=keyword)
            return self._comment(
                line,
                SKIPPED_CALC_PARENT_TEMPLATE.format(
                    record=record, keyword=keyword,
                ),
            )

        rendered = self._comment(
            line,
            EXPANDED_CALC_PARENT_TEMPLATE.format(
                keyword=keyword, record=record,
            ),
        )
        rendered.extend(
            self._statement(
                line,
                OBTAIN_CALC_TEMPLATE.format(record=record),
                terminate=terminated,
            )
        )

        # PUBLISHED before the log line, so a future reader cannot
        # conclude from the message alone that the set was populated.
        self.calc_parent_records.add(cobol_name(record))
        self._log("calc_parent_emitted", record=record, keyword=keyword)
        return rendered

    def _expand_erase(self, line: str, match) -> tuple[list[str], bool]:
        keyword = cobol_name(match.group("keyword"))
        terminated = self._is_terminated(match.string)
        plan = self.path_resolver.plan_for_keyword(keyword)

        if plan is None or not plan.is_usable:
            self._log("keyword_not_found", keyword=keyword)
            return self._keep(
                line, SKIPPED_NO_PATH_TEMPLATE.format(keyword=keyword)
            ), False

        record = plan.driving.record_name

        if REQUIRE_MAPPED_DRIVING_RECORD and not (
            self._record_is_mapped(record)
        ):
            self._log("record_unmapped", record=record, keyword=keyword)
            return self._keep(
                line, SKIPPED_UNMAPPED_TEMPLATE.format(record=record)
            ), False

        rendered = self._comment(line, EXPANDED_OBTAIN_TEMPLATE.format(
            mode="ERASE", lr=plan.logical_record, keyword=keyword,
            record=record, within=plan.driving.within_name,
        ))
        rendered.extend(
            self._statement(line, f"ERASE {record}", terminate=terminated)
        )
        return rendered, True

    # ------------------------------------------------ status/qualifier
    @staticmethod
    def _status_token(literal: str) -> str | None:
        """The DB2 status token for an IDMS LR-STATUS literal, or None.

        CORRECTION A - the classifier had two classes and a DEFAULT.

            token = RECORD_NOT_FOUND_TOKEN
                    if "NOT-FND" in literal or "NOT-FOUND" in literal
                    else END_OF_SET_TOKEN

        'LR-FOUND' contains FOUND but not NOT-FOUND, so it fell to the
        else branch and was translated as end-of-set, which maps to
        SQLCODE = 100. The condition

            IF LR-STATUS NOT = 'LR-FOUND'   ->   abend when NOT found

        became

            IF NOT SQLCODE = 100            ->   abend when FOUND

        The program abends on every successful lookup and continues
        silently on every miss. It compiles, it runs, and it is wrong on
        every record.

        CORRECTION B - the negation guard sat on a POSITIVE class.

        'LR-NOT-OK' matches no NOT_FOUND fragment but does match the
        positive fragment '-OK', so it classified as SUCCESS - the same
        inversion by a different route. A HARD negation (NOT- / NON-)
        reaching the end-of-set class is REFUSED rather than guessed.

        CORRECTION C - the 'NO-' prefix, found in live output.

        VM4BD310 carried

            IF LR-STATUS = 'NO-VMBEVEF-FND'

        which matched the positive fragment '-FND' and shipped as
        SQLCODE = 0. It means NO VMBEVEF FOUND. Inverted again.

        'NO-' could not simply join NEGATION_FRAGMENTS, because the same
        subschemas return BOTH spellings:

            NO-VMBFAR-FND      not found
            NO-MORE-VMBFAR     end of set

        END_OF_SET is therefore tested BEFORE the FOUND class, so
        NO-MORE is classified first and never reaches the negation test.
        A negated FOUND spelling resolves to NOT FOUND - a known
        meaning, not an unknown literal, so it is translated.

        ORDER IS LOAD-BEARING:
            NOT_FOUND  first - FOUND is a substring of NOT-FOUND, and
                               FND is a substring of NOT-FND.
            END_OF_SET next  - claims NO-MORE before 'NO-' is read as
                               a negation.
            FOUND      last  - negated spellings resolve to NOT FOUND.

        An unrecognised literal returns None and the condition is LEFT
        UNCHANGED, so the surviving LR-STATUS is caught downstream by
        LR_STATUS_TOKEN_PATTERN rather than defaulted to a guess.

        KNOWN GAP - P5. The authority for these three classes is already
        parsed: LrfAccessPlan.end_of_set_literals and .not_found_literals
        are resolved from the subschema's ON-clause returns. This method
        ignores them and classifies by string fragment instead, which is
        why three distinct statuses collapse to two tokens - visible in
        VMDZ4310 at 002560, 002600 and 002740, where all three guards
        read IF SQLCODE = 100 against the same FETCH. Consuming the plan
        is a separate, separately measured change.
        """
        text = cobol_name(literal)
        if not text:
            return None

        if any(f in text for f in NOT_FOUND_LITERAL_FRAGMENTS):
            return RECORD_NOT_FOUND_TOKEN

        # END_OF_SET FIRST. 'NO-MORE-X' is end-of-set, not a negated
        # FOUND, and it shares the 'NO-' prefix with 'NO-X-FND'.
        if any(f in text for f in END_OF_SET_LITERAL_FRAGMENTS):
            if any(f in text for f in NEGATION_FRAGMENTS):
                return None
            return END_OF_SET_TOKEN

        if any(f in text for f in FOUND_LITERAL_FRAGMENTS):
            # A negated FOUND spelling is NOT FOUND - it is not unknown.
            # 'NO-VMBEVEF-FND' shipped as SQLCODE = 0 before this branch.
            if any(f in text for f in FOUND_NEGATION_FRAGMENTS):
                return RECORD_NOT_FOUND_TOKEN
            return RECORD_FOUND_TOKEN

        return None

    @staticmethod
    def _rewrite_lr_status(logical: str) -> tuple[str, int]:
        """Rewrite 'LR-STATUS <op> <literal>' to an IDMS status token.

        REFUSAL - abbreviated combined relation.

        VM1BD526 carried

            IF LR-STATUS = 'VMBEFF-NOT-FND' OR 'LR-ERROR'

        COBOL implies the subject and the operator on the second
        literal. LR_STATUS_CONDITION_PATTERN sees only the first, so a
        rewrite produced

            IF SQLCODE = 100 OR 'LR-ERROR'

        stranding a bare literal as a condition operand. The WHOLE
        condition is therefore left untouched. The caller counts the
        refusal and reports it; the surviving LR-STATUS is a finding, not
        a silent miss.

        hits counts RESOLVED rewrites only. An earlier version
        incremented before classifying, so refusals were reported as
        successful conversions in the run log.
        """
        hits = 0

        if LR_STATUS_ABBREVIATED_PATTERN.search(logical):
            return logical, 0

        def _replace(match) -> str:
            nonlocal hits

            operator = str(match.group("operator") or "").upper()
            token = LrfPathExpander._status_token(match.group("literal"))

            if token is None:
                return match.group(0)

            hits += 1
            return f"NOT {token}" if operator.startswith("NOT") else token

        return LR_STATUS_CONDITION_PATTERN.sub(_replace, logical), hits

    @staticmethod
    def _strip_of_lr(logical: str) -> tuple[str, int]:
        first, a = OF_LR_SUFFIX_PATTERN.subn(r"\g<head>", logical)
        second, b = BARE_OF_LR_PATTERN.subn("", first)
        return second, a + b

    # ---------------------------------------------------------- render
    def _statement(
        self,
        template_line: str,
        body: str,
        terminate: bool = True,
    ) -> list[str]:
        """Render one generated statement.

        ``terminate`` MIRRORS the source statement. A source OBTAIN that
        ended in a period produces one, so every standalone access is
        unchanged. A source OBTAIN inside an inline PERFORM ...
        END-PERFORM carried no period, and adding one closes the sentence
        and orphans the END-PERFORM. See CORRECTION 1.

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
        """Comment ONE source line out, behind its refusal marker."""
        rendered = self._comment(line, marker)
        rendered.extend(self._comment(line, self._logical(line)))
        return rendered

    def _keep_span(
        self,
        lines: list[str],
        start_index: int,
        consumed: int,
        marker: str,
    ) -> list[str]:
        """Comment a WHOLE multi-line statement out, behind its marker.

        CORRECTION 4. ``_keep`` commented only the first physical line,
        and the caller then marked every other line of the statement as
        already consumed - so they were deleted from the output with no
        comment, no marker and no diagnostic. A refusal must leave the
        entire source statement behind for the reviewer who has to
        expand it by hand.
        """
        anchor = lines[start_index]
        rendered = self._comment(anchor, marker)
        end = min(start_index + max(consumed, 1), len(lines))
        for index in range(start_index, end):
            body = self._logical(lines[index])
            if not body:
                continue
            rendered.extend(self._comment(lines[index], body))
        return rendered

    def _refuse(
        self,
        line: str,
        keep_span: tuple | None,
        marker: str,
    ) -> list[str]:
        """Keep the source behind a refusal marker, span-aware."""
        if keep_span is None:
            return self._keep(line, marker)
        lines, start_index, consumed = keep_span
        return self._keep_span(lines, start_index, consumed, marker)

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

    def _replace_body(self, line: str, new_body: str) -> str:
        indent = self._body_indent(line)
        text = f"{indent}{new_body.strip()}"
        if not self._is_fixed(line):
            return text
        return self.fixed_format.replace_body(line, text)

    # --------------------------------------------------------- helpers
    @staticmethod
    def _is_terminated(text: str) -> bool:
        """True when the SOURCE statement ended in a period.

        ENDS WITH, not CONTAINS. The continuation scan used
        ``STATEMENT_TERMINATOR not in assembled``, which stops at the
        first interior period and reads an open statement as closed.
        """
        return str(text or "").rstrip().endswith(STATEMENT_TERMINATOR)

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

    def _record_is_mapped(self, record_name: str) -> bool:
        """Sheet Mapping probe, tolerant of a resolver that lacks it.

        Every mapping gate in this module routes through here. Three of
        them used to call ``self.path_resolver.record_is_mapped``
        directly, so a resolver stub without that method raised
        AttributeError mid-conversion while this guarded helper sat
        unused beside them. An absent probe means "do not refuse",
        which is the behaviour that existed before the guard.
        """
        probe = getattr(self.path_resolver, "record_is_mapped", None)
        if probe is None:
            return True
        try:
            return bool(probe(record_name))
        except Exception:  # noqa: BLE001
            return True

    @staticmethod
    def _is_comment(line: str) -> bool:
        # DEFERRED DEFECT 1: the free-format fallback treats 'D' and '-'
        # as comment indicators on a STRIPPED line, so 'DISPLAY ...' on a
        # record with a blank sequence area is classified as a comment.
        # Column 7 is authoritative in fixed format only. Not changed
        # here so the keyed-parent correction can be measured alone; it
        # is retired by the shared statement joiner.
        text = str(line or "")
        if len(text) >= 7 and text[:6].strip().isdigit():
            return text[6] in COMMENT_INDICATORS
        return text.lstrip().startswith(COMMENT_INDICATORS)

    @staticmethod
    def _contains_lrf_syntax(text: str) -> bool:
        # DEFERRED DEFECT 2: the three pattern tests below run on RAW
        # lines, so the anchored OBTAIN / ERASE patterns cannot match a
        # fixed-format record. The gate only passes today because the two
        # substring tests above them fire first. A program carrying an
        # OBTAIN ... WHERE and no LR-STATUS and no ' OF LR' would no-op
        # silently. This is instance 1 of the physical-line defect
        # family; it is retired by the shared statement joiner, as a
        # separately measured change.
        upper = str(text or "").upper()
        if LR_STATUS_TOKEN_PATTERN.search(upper):
            return True
        if " OF LR" in upper:
            return True
        for line in upper.splitlines():
            if LR_OBTAIN_WHERE_PATTERN.match(line.strip()):
                return True
            if LR_OBTAIN_WHERE_PREFIX_PATTERN.match(line.strip()):
                return True
            if LR_ERASE_WHERE_PATTERN.match(line.strip()):
                return True
        return False

    def _log(self, key: str, **values) -> None:
        """Record one diagnostic, or record that it could not be recorded.

        CORRECTION 3. This used ``LRF_EXPANSION_MESSAGES.get(key, "")``
        and returned when the lookup failed, so a diagnostic whose
        template was never added produced NOTHING. Four keys were in
        that state - status_refused_abbreviated, statement_unterminated,
        statement_runaway and keyword_unreadable - and every one of them
        incremented a counter and printed nothing.

        An unmapped key is now reported AS an unmapped key, which is the
        difference between a visible gap and a lost finding, and is the
        same correction already made to LrfUpdateExpander.
        """
        template = LRF_EXPANSION_MESSAGES.get(key)

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


__all__ = ["LrfPathExpander", "cobol_name"]
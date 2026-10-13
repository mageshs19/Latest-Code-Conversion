from __future__ import annotations

from converter.services.fixed_format_line_service import (
    FixedFormatLineService,
)
from converter.services.update_cobol_final_cleanup_utils import (
    UpdateCobolFinalCleanupUtils,
)
from patterns.update_final_feedback_patterns import (
    EXEC_SQL_END_PATTERN,
    EXEC_SQL_START_PATTERN,
    MOVE_TO_DCL_OF_REFERENCE_PATTERN,
    SET_KEYWORD_PATTERN,
    SQL_SET_ASSIGNMENT_PATTERN,
    UPDATE_STATEMENT_PATTERN,
    WHERE_KEYWORD_PATTERN,
)
from rules.timestamp_audit_rules import UPDATE_AUDIT_COLUMN_PREFIXES
from rules.update_cobol_final_cleanup_rules import (
    AUDIT_SOURCE_BY_KIND,
    TIMESTAMP_AUDIT_PREFIXES,
    UPDATE_FINAL_LOOKBACK_DUPLICATE_LIMIT,
    USER_AUDIT_PREFIXES,
)

ASSIGNMENT_SEPARATOR = ","
SENTENCE_TERMINATOR = "."
WHERE_INFIX = " WHERE "


class UpdateAuditMoveInserter:
    """Inserts audit MOVE statements before a generated UPDATE SQL block.

    Only audit host variables that the UPDATE SET list actually assigns
    receive a move. A column the statement does not write is none of this
    pass's business.

    CORRECTION 1 - the first assignment was discarded
    --------------------------------------------------
    The SET scan read

        if SET_KEYWORD_PATTERN.match(logical):
            in_set = True
            continue

    so a line carrying BOTH the keyword and its first assignment -

        SET DA_INFSDGD_479BFAR = :DCLDZBFARTV.DA-INFSDGD-479BFAR

    which is the manual reference's own shape - was consumed whole and the
    assignment never parsed. If that first column was the audit column, the
    move was silently never generated.

    CORRECTION 2 - an assignment had to fit one physical line
    ---------------------------------------------------------
    SQL_SET_ASSIGNMENT_PATTERN was matched against each line in turn. A
    72-column wrap splits an assignment across two lines and neither half
    matches. The SET clause is now joined into ONE logical string and split
    on commas, so wrapping is irrelevant.

    CORRECTION 3 - the duplicate guard crossed paragraph boundaries
    ---------------------------------------------------------------
    has_recent_move_to_host scanned back UPDATE_FINAL_LOOKBACK_DUPLICATE_LIMIT
    lines regardless of structure. A MOVE to the same host in an unrelated
    paragraph 60 lines earlier suppressed the insert, and nothing was said.
    The walk now stops at the first sentence boundary above the block.

    The stop test also fires on CONTINUE. and END-EXEC., which are not
    paragraph headers. That is deliberate: stopping EARLY can only cause an
    extra MOVE, and a duplicate MOVE is harmless where a missing one writes
    uninitialised bytes into an audit column.

    CORRECTION 4 - every refusal was silent
    ----------------------------------------
    The class produced no diagnostics at all, so a run that inserted nothing
    read exactly like a run with nothing to insert. Every decision is now
    reported.
    """

    def __init__(
        self,
        *,
        fixed_format: FixedFormatLineService,
        utils: UpdateCobolFinalCleanupUtils,
    ) -> None:
        self.fixed_format = fixed_format
        self.utils = utils
        self.messages: list[str] = []

    #
    # Public surface
    #
    def insert_update_audit_moves(
        self,
        text: str,
    ) -> str:
        self.messages = []

        lines = text.splitlines()
        update_blocks = self.find_update_exec_sql_blocks(lines)

        if not update_blocks:
            self.messages.append(
                "Update audit moves: no generated UPDATE block found; "
                "nothing to insert."
            )
            return text.rstrip() + "\n"

        output = list(lines)
        inserted = 0

        for start, end in sorted(update_blocks, reverse=True):
            block = output[start : end + 1]
            audit_targets = self.audit_targets_from_update_block(block)

            if not audit_targets:
                self.messages.append(
                    f"Update audit moves: the UPDATE at line {start + 1} "
                    "assigns no audit column; nothing inserted."
                )
                continue

            reference_line = output[start]
            insert_lines: list[str] = []

            for group, host, audit_kind in audit_targets:
                if self.has_recent_move_to_host(
                    lines=output,
                    insert_index=start,
                    group=group,
                    host=host,
                ):
                    self.messages.append(
                        f"Update audit moves: {host} OF {group} is already "
                        "assigned in this sentence; no second move added."
                    )
                    continue

                source = self.source_for_audit_kind(audit_kind)

                if not source:
                    self.messages.append(
                        "Update audit moves: no source field is configured "
                        f"for audit kind '{audit_kind}'; {host} OF {group} "
                        "was left unassigned and the UPDATE will write "
                        "whatever the host variable happens to hold."
                    )
                    continue

                move_logical = f"MOVE {source} TO {host} OF {group}"
                insert_lines.append(
                    self.fixed_format.replace_body(
                        reference_line,
                        self.utils.body_with_existing_indent(
                            original_line=reference_line,
                            new_logical=move_logical,
                        ),
                    )
                )

            if not insert_lines:
                continue

            output[start:start] = insert_lines
            inserted += len(insert_lines)

        if inserted:
            self.messages.append(
                f"Update audit moves: inserted {inserted} audit host "
                "move(s) before the generated UPDATE."
            )

        return "\n".join(output).rstrip() + "\n"

    #
    # Block discovery
    #
    def find_update_exec_sql_blocks(
        self,
        lines: list[str],
    ) -> list[tuple[int, int]]:
        blocks: list[tuple[int, int]] = []
        in_exec_sql = False
        start = -1
        has_update = False

        for index, line in enumerate(lines):
            logical = self.fixed_format.logical(line)
            upper = logical.upper()

            if EXEC_SQL_START_PATTERN.match(logical):
                # One-line "EXEC SQL ... END-EXEC." (e.g. INCLUDE) must not
                # wedge the in_exec_sql flag open. If END-EXEC is on the same
                # line, this block opens and closes immediately and carries
                # no UPDATE, so skip it without entering multi-line mode.
                if "END-EXEC" in upper:
                    in_exec_sql = False
                    start = -1
                    has_update = False
                    continue
                in_exec_sql = True
                start = index
                has_update = False
                continue

            if in_exec_sql and UPDATE_STATEMENT_PATTERN.match(logical):
                has_update = True

            if in_exec_sql and EXEC_SQL_END_PATTERN.match(logical):
                if has_update:
                    blocks.append((start, index))
                in_exec_sql = False
                start = -1
                has_update = False

        return blocks

    #
    # SET clause
    #
    def audit_targets_from_update_block(
        self,
        block: list[str],
    ) -> list[tuple[str, str, str]]:
        region = self.set_clause_text(block)
        targets: list[tuple[str, str, str]] = []

        for segment in region.split(ASSIGNMENT_SEPARATOR):
            candidate = segment.strip()

            if not candidate:
                continue

            match = SQL_SET_ASSIGNMENT_PATTERN.match(candidate)

            if not match:
                continue

            column = str(match.group("column") or "").upper()
            group = str(match.group("group") or "").upper()
            host = str(match.group("host") or "").upper()

            audit_kind = self.audit_kind_for_column(column)

            if not audit_kind:
                continue

            targets.append((group, host, audit_kind))

        return self.unique_targets(targets)

    def set_clause_text(
        self,
        block: list[str],
    ) -> str:
        """Everything between SET and WHERE, as ONE logical string.

        Joining first is what makes a wrapped assignment parseable. The
        keyword is stripped from its own line rather than consuming it, so
        an assignment sharing the SET line survives.
        """
        parts: list[str] = []
        in_set = False

        for line in block:
            logical = self.fixed_format.logical(line)

            if not logical.strip():
                continue

            if not in_set:
                opener = SET_KEYWORD_PATTERN.match(logical)

                if not opener:
                    continue

                in_set = True
                remainder = logical[opener.end() :].strip()

                if remainder:
                    parts.append(remainder)

                continue

            if WHERE_KEYWORD_PATTERN.match(logical):
                break

            marker = logical.upper().find(WHERE_INFIX)

            if marker >= 0:
                head = logical[:marker].strip()

                if head:
                    parts.append(head)

                break

            parts.append(logical.strip())

        return " ".join(parts)

    #
    # Classification
    #
    def audit_kind_for_column(
        self,
        column: str,
    ) -> str:
        normalized = str(column or "").upper()

        if not self.has_update_audit_prefix(normalized):
            return ""

        if normalized.startswith(TIMESTAMP_AUDIT_PREFIXES):
            return "timestamp"

        if normalized.startswith(USER_AUDIT_PREFIXES):
            return "user"

        return ""

    def has_update_audit_prefix(
        self,
        column: str,
    ) -> bool:
        normalized = str(column or "").upper()

        return any(
            normalized.startswith(str(prefix or "").upper())
            for prefix in UPDATE_AUDIT_COLUMN_PREFIXES
        )

    def source_for_audit_kind(
        self,
        audit_kind: str,
    ) -> str:
        return AUDIT_SOURCE_BY_KIND.get(str(audit_kind or "").lower(), "")

    #
    # Duplicate suppression
    #
    def has_recent_move_to_host(
        self,
        *,
        lines: list[str],
        insert_index: int,
        group: str,
        host: str,
    ) -> bool:
        target_group = str(group or "").upper()
        target_host = str(host or "").upper()

        floor = max(0, insert_index - UPDATE_FINAL_LOOKBACK_DUPLICATE_LIMIT)

        for index in range(insert_index - 1, floor - 1, -1):
            logical = self.fixed_format.logical(lines[index])

            if not logical.strip():
                continue

            if self.is_sentence_boundary(logical):
                break

            match = MOVE_TO_DCL_OF_REFERENCE_PATTERN.match(logical)

            if not match:
                continue

            found_group = str(match.group("group") or "").upper()
            found_host = str(match.group("host") or "").upper()

            if found_group == target_group and found_host == target_host:
                return True

        return False

    @staticmethod
    def is_sentence_boundary(
        logical: str,
    ) -> bool:
        """A single word closed by a period: header or scope terminator."""
        text = str(logical or "").strip()

        if not text.endswith(SENTENCE_TERMINATOR):
            return False

        name = text[: -len(SENTENCE_TERMINATOR)].strip()

        return bool(name) and " " not in name

    #
    # Helpers
    #
    def unique_targets(
        self,
        values: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        output: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str, str]] = set()

        for group, host, audit_kind in values:
            key = (
                str(group or "").upper(),
                str(host or "").upper(),
                str(audit_kind or "").lower(),
            )

            if not key[0] or not key[1] or not key[2]:
                continue

            if key in seen:
                continue

            seen.add(key)
            output.append(key)

        return output


__all__ = ["UpdateAuditMoveInserter"]
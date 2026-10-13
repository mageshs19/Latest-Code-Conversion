# LOCATION: converter/composers/update_sql_cleanup/qualified_date_move_rewriter.py
# ACTION: CREATE NEW FILE
"""Applies the DB2 external-date block to QUALIFIED host moves.

WHY THIS PASS EXISTS

DateMoveBuilder was reachable only through BareMoveRewriter, whose
pattern (MOVE_TO_BARE_FIELD_PATTERN) anchors on end-of-line right after
the target. A move that is already qualified -

    MOVE <src> TO <host> OF <DCLGROUP>

- cannot match it, so a DATE column that arrived qualified was written
raw into the host variable. The host is DB2 external format
(DD.MM.CCYY); the source is CCYYMMDD. The WHERE predicate built on that
host then matches zero rows.

This pass owns exactly one concern: a MOVE whose target is a qualified
DCLGEN host backed by a DATE column must carry the conversion block.
Qualification itself stays owned by BareMoveRewriter.

CONTINUATION FORM

The qualifier is frequently pushed onto the next physical line by the
column-72 wrapper. One lookahead line is joined before matching;
anything further is left alone and reported.

IDEMPOTENCE

DateMoveBuilder._is_staging_field already collapses a re-run to a single
move, and an immediately preceding realign line is detected here, so the
pass may run twice without destroying the value.

No program, record, table, DCLGEN group or host variable name is
hardcoded.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer

REALIGN_MARKER = "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY"

MESSAGES = {
    "converted": (
        "Qualified date move: {host} OF {group} is DB2 column {column} "
        "(DATE); inserted the CCYYMMDD realignment block."
    ),
    "already": (
        "Qualified date move: {host} OF {group} already carries the "
        "realignment block."
    ),
    "unresolved": (
        "Qualified date move: {host} OF {group} resolves to no DCLGEN "
        "column; left unchanged."
    ),
    "none": (
        "Qualified date move: no qualified DATE host move was found "
        "({count} line(s) examined)."
    ),
}


class QualifiedDateMoveRewriter:
    """Inserts the date conversion block before a qualified host move."""

    def __init__(self, owner, date_builder) -> None:
        self.owner = owner
        self.date_builder = date_builder
        self.messages: list[str] = []

    # ------------------------------------------------------------------
    # entry point
    # ------------------------------------------------------------------
    def rewrite(self, text: str) -> str:
        self.messages = []
        source = str(text or "")
        if not source.strip():
            return source

        lines = source.splitlines()
        output: list[str] = []
        index = 0
        in_sql = False
        converted = 0

        while index < len(lines):
            line = lines[index]
            logical = self.owner._logical(line)

            if self.owner.EXEC_SQL_START_PATTERN.match(logical):
                in_sql = True
            elif self.owner.EXEC_SQL_END_PATTERN.match(logical):
                in_sql = False

            if in_sql or not logical.upper().startswith("MOVE "):
                output.append(line)
                index += 1
                continue

            match, consumed = self._match_qualified_move(lines, index)
            if match is None:
                output.append(line)
                index += 1
                continue

            block = self._block_for(match, line, output)
            if block is None:
                output.extend(lines[index:index + consumed])
                index += consumed
                continue

            output.extend(block)
            converted += 1
            index += consumed

        if converted == 0:
            self._note("none", count=len(lines))

        return "\n".join(output) + ("\n" if source.endswith("\n") else "")

    # ------------------------------------------------------------------
    # matching
    # ------------------------------------------------------------------
    def _match_qualified_move(self, lines: list[str], index: int):
        """Match on this line, then on this line joined with the next."""
        logical = self.owner._logical(lines[index])

        match = self.owner.MOVE_TO_DCL_HOST_PATTERN.match(logical)
        if match:
            return match, 1

        if index + 1 >= len(lines):
            return None, 1

        nxt = self.owner._logical(lines[index + 1])
        if not nxt.upper().startswith("OF DCL"):
            return None, 1

        joined = f"{logical.rstrip()} {nxt.strip()}"
        match = self.owner.MOVE_TO_DCL_HOST_PATTERN.match(joined)
        if match:
            return match, 2

        return None, 1

    # ------------------------------------------------------------------
    # rendering
    # ------------------------------------------------------------------
    def _block_for(self, match, line: str, emitted: list[str]):
        source_value = str(match.group("src")).strip()
        host = NameNormalizer.to_cobol(match.group("host"))
        group = NameNormalizer.normalize(match.group("group"))

        column = self._column_for(group, host)
        if not column:
            self._note("unresolved", host=host, group=group)
            return None

        if not self.date_builder.is_db2_date_column(column):
            return None

        if self._already_realigned(emitted):
            self._note("already", host=host, group=group)
            return None

        leading = self.owner._leading_spaces(line)
        host_key = f"{host} OF {group}"

        block = self.date_builder.date_ymd8_to_db2_external_move(
            source_value=source_value,
            host_key=host_key,
            leading=leading,
        )
        self._note("converted", host=host, group=group, column=column)
        return list(block)

    @staticmethod
    def _already_realigned(emitted: list[str]) -> bool:
        for previous in reversed(emitted[-3:]):
            if REALIGN_MARKER in " ".join(str(previous).upper().split()):
                return True
        return False

    # ------------------------------------------------------------------
    # DCLGEN lookup - group + host -> column, no table context needed
    # ------------------------------------------------------------------
    def _column_for(self, group: str, host: str) -> str:
        repository = getattr(self.owner, "dclgen_repository", None)
        if repository is None:
            return ""

        for table in repository.tables():
            if NameNormalizer.normalize(
                repository.group_for_table(table)
            ) != group:
                continue
            for column in repository.columns_for_table(table):
                current = NameNormalizer.to_cobol(
                    column.cobol_host_name or column.column_name
                )
                if current == host:
                    return NameNormalizer.normalize(column.column_name)
        return ""

    def _note(self, key: str, **values) -> None:
        try:
            self.messages.append(MESSAGES[key].format(**values))
        except (KeyError, IndexError):
            self.messages.append(f"{key} {values}")


__all__ = ["QualifiedDateMoveRewriter"]
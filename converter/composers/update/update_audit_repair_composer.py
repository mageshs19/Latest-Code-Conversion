# LOCATION: converter/composers/update/update_audit_repair_composer.py
# ACTION: CREATE NEW FILE
"""Put the update audit MOVEs back after the restart family rebuilt the
business paragraph.

THE DEFECT THIS PASS EXISTS FOR

Two generators contribute to an UPDATE program. The first inserts the
audit MOVEs into the business paragraph. The second classifies the
first's work as legacy restart residue, removes it, and rebuilds the
paragraph from a repaired span. The MOVEs go with it, the SET clause
still names the host variables, and DB2 is handed whatever the DCLGEN
group happened to contain. That is silent data corruption, not a
formatting defect, which is why the repair runs as its own pass rather
than as a reorder of the two generators.

IDEMPOTENT

A second run finds the MOVE already present in the paragraph and inserts
nothing. Running the whole pipeline twice produces identical text.

REFUSAL IS THE NORMAL CASE

A retrieval program, an UPDATE with no audit columns, or a program whose
source field is not declared all return the text unchanged WITH a
reason. Silence would be the defect.

NOTHING IS HARDCODED

Audit columns are matched by COLUMN PREFIX from rules/. Host variable
spelling and the DCLGEN group come from the SET clause the generator
already wrote. No program, paragraph, record, table or host variable
name appears in this file.
"""

from __future__ import annotations

import re

from rules.update_audit_repair_rules import (
    AUDIT_TIMESTAMP_COLUMN_PREFIXES,
    AUDIT_TIMESTAMP_SOURCE_FIELD,
    AUDIT_USERID_COLUMN_PREFIXES,
    AUDIT_USERID_SOURCE_FIELD,
    BLOCK_SCAN_LIMIT,
    BODY_END_INDEX,
    BODY_START_INDEX,
    CONTINUATION_INDENT,
    CONTINUATION_SPLIT_TOKEN,
    END_EXEC_TOKEN,
    ENFORCE_UPDATE_AUDIT_MOVES,
    EXEC_SQL_TOKEN,
    INDICATOR_INDEX,
    LINE_WIDTH,
    MESSAGES,
    MOVE_TEMPLATE,
    PARAGRAPH_SCAN_LIMIT,
    SEQUENCE_WIDTH,
    SET_KEYWORD,
    STATEMENT_INDENT,
    UPDATE_VERB,
)

# Regex lives with the pass that uses it; move to patterns/ if a second
# consumer appears.
HOST_REFERENCE_PATTERN = re.compile(
    r":\s*(?P<group>DCL[A-Z0-9-]+)\s*\.\s*(?P<host>[A-Z][A-Z0-9-]*)",
    flags=re.IGNORECASE,
)

COMMENT_INDICATORS = ("*", "/", "D")
UNKNOWN_PARAGRAPH = "(unnamed paragraph)"


class UpdateAuditRepairComposer:
    """Re-asserts the audit MOVEs in front of every business UPDATE."""

    def __init__(self, enabled: bool | None = None) -> None:
        self.enabled = (
            ENFORCE_UPDATE_AUDIT_MOVES if enabled is None else bool(enabled)
        )
        self.messages: list[str] = []

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------
    def apply(self, cobol_text: str) -> str:
        self.messages = []

        if not self.enabled:
            self._say("disabled")
            return cobol_text

        if not cobol_text:
            self._say("no_blocks")
            return cobol_text

        lines = cobol_text.splitlines()
        targets = self._targets(lines)

        if not targets:
            self._say("no_blocks")
            return cobol_text

        inserted = skipped = refused = 0

        # Reverse order: an insertion must not shift the index of a
        # target that has not been handled yet.
        for block_start, hosts in reversed(targets):
            paragraph_start = self._paragraph_start(lines, block_start)
            paragraph_name = self._paragraph_name(lines, paragraph_start)
            new_lines: list[str] = []

            for host, group in hosts:
                source = self._source_for(host)
                if source is None:
                    continue

                if self._already_moved(
                    lines, paragraph_start, block_start, host
                ):
                    self._say(
                        "already_present",
                        host=host,
                        paragraph=paragraph_name,
                    )
                    skipped += 1
                    continue

                if not self._declared(cobol_text, source):
                    self._say("no_source", field=source, host=host)
                    refused += 1
                    continue

                rendered = self._render(
                    anchor=lines[block_start],
                    source=source,
                    host=host,
                    group=group,
                )
                if len(rendered) > 1:
                    self._say("wrapped", host=host)

                new_lines.extend(rendered)
                self._say(
                    "inserted",
                    source=source,
                    host=host,
                    group=group,
                    paragraph=paragraph_name,
                )
                inserted += 1

            if new_lines:
                lines[block_start:block_start] = new_lines

        self._say(
            "summary",
            inserted=inserted,
            skipped=skipped,
            refused=refused,
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Target discovery
    # ------------------------------------------------------------------
    def _targets(self, lines: list[str]) -> list[tuple[int, list[tuple[str, str]]]]:
        """Every EXEC SQL UPDATE block that names at least one audit column."""
        found: list[tuple[int, list[tuple[str, str]]]] = []

        for index, line in enumerate(lines):
            if self._is_comment(line):
                continue
            if EXEC_SQL_TOKEN not in self._body(line).upper():
                continue

            end = self._block_end(lines, index)
            if end is None:
                continue

            block = " ".join(
                self._body(lines[i]) for i in range(index, end + 1)
            ).upper()

            if UPDATE_VERB not in block or SET_KEYWORD not in block:
                continue

            hosts = self._audit_hosts(block)
            if hosts:
                found.append((index, hosts))

        return found

    def _block_end(self, lines: list[str], start: int) -> int | None:
        limit = min(len(lines), start + BLOCK_SCAN_LIMIT)
        for index in range(start, limit):
            if self._is_comment(lines[index]):
                continue
            if END_EXEC_TOKEN in self._body(lines[index]).upper():
                return index
        return None

    def _audit_hosts(self, block: str) -> list[tuple[str, str]]:
        """Audit host variables in SET-clause order, de-duplicated."""
        hosts: list[tuple[str, str]] = []
        seen: set[str] = set()

        for match in HOST_REFERENCE_PATTERN.finditer(block):
            host = match.group("host").upper()
            group = match.group("group").upper()
            if host in seen:
                continue
            if self._source_for(host) is None:
                continue
            seen.add(host)
            hosts.append((host, group))

        return hosts

    @staticmethod
    def _source_for(host: str) -> str | None:
        """Map a host variable to its audit source field, or None."""
        column = host.upper().replace("-", "_")
        if column.startswith(tuple(AUDIT_TIMESTAMP_COLUMN_PREFIXES)):
            return AUDIT_TIMESTAMP_SOURCE_FIELD
        if column.startswith(tuple(AUDIT_USERID_COLUMN_PREFIXES)):
            return AUDIT_USERID_SOURCE_FIELD
        return None

    # ------------------------------------------------------------------
    
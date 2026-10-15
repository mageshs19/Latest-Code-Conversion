# LOCATION: converter/services/db2_date_sentinel_policy.py
# ACTION: CREATE NEW FILE
"""The single owner of the DB2 null-date sentinel decision.

ONE QUESTION, ONE ANSWER

    guard_lines(source, indent) -> list[str]

Returns the three guard lines, or an EMPTY LIST when the source value is
supplied by the JCL PARM and therefore cannot be ZERO or SPACES.

WHY A SERVICE AND NOT THREE COPIES

The guard was written out three times, in three packages, as a literal:

    converter/composers/update_sql_cleanup/date_move_builder.py   line 77
    converter/generators/sql/sql_date_move_builder.py             line 72
    converter/postprocess/update_date_host_converter.py           line 162

Three copies means a correction lands in one and the other two keep
shipping the old shape - which is exactly how this defect survived
review. All three now call this class, so the decision has one owner and
one test suite.

ORDER OF TESTS IS LOAD-BEARING
    1. policy disabled      -> no guard, reported
    2. DCLGEN-qualified     -> ALWAYS guarded; a DB2 column may be NULL
    3. PARM family          -> never guarded
    4. everything else      -> guarded, the safe default

Rule 2 is tested BEFORE rule 3 so a DCLGEN host that happens to carry a
PARM-shaped name can never lose its protection.

No program, record, table, DCLGEN group or host variable name is
hardcoded. Every name lives in rules/db2_date_sentinel_rules.py.
"""

from __future__ import annotations

from rules.db2_date_sentinel_rules import (
    DB2_DATE_SENTINEL_MESSAGES,
    DCLGEN_NAME_PREFIX,
    DCLGEN_QUALIFIER_TOKENS,
    ENFORCE_DB2_DATE_NULL_SENTINEL,
    PARM_DATE_SOURCE_NAMES,
    PARM_DATE_SOURCE_PREFIXES,
    PARM_DATE_SOURCE_SUFFIXES,
    SENTINEL_GUARD_BODY_INDENT,
    SENTINEL_GUARD_CLOSE,
    SENTINEL_GUARD_MOVE,
    SENTINEL_GUARD_OPEN,
)


class Db2DateSentinelPolicy:
    """Decides whether a date move needs the null-date guard."""

    def __init__(self, sentinel: str) -> None:
        self._sentinel = str(sentinel or "").strip()
        self.messages: list[str] = []

    # ------------------------------------------------------------------ #
    # Public surface
    # ------------------------------------------------------------------ #
    def guard_lines(self, source: str, indent: str = "") -> list[str]:
        """The guard, indented, or [] when the source cannot be unset."""
        name = self._normalize(source)

        if not ENFORCE_DB2_DATE_NULL_SENTINEL:
            self._say("policy_disabled")
            return []

        if self.is_dclgen_qualified(name):
            self._say("guard_emitted", source=name)
            return self._render(indent)

        if self.is_parm_sourced(name):
            self._say("guard_suppressed", source=name)
            return []

        self._say("guard_emitted", source=name)
        return self._render(indent)

    def is_parm_sourced(self, source: str) -> bool:
        """True when the value is supplied by the JCL PARM."""
        name = self._normalize(source)

        if not name:
            return False

        if name in PARM_DATE_SOURCE_NAMES:
            return True

        if name.endswith(PARM_DATE_SOURCE_SUFFIXES):
            return True

        return name.startswith(PARM_DATE_SOURCE_PREFIXES)

    def is_dclgen_qualified(self, source: str) -> bool:
        """True when the value is read from a DB2 column."""
        name = self._normalize(source)

        if not name:
            return False

        if name.startswith(DCLGEN_NAME_PREFIX):
            return True

        return any(token in name for token in DCLGEN_QUALIFIER_TOKENS)

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _render(self, indent: str) -> list[str]:
        pad = str(indent or "")
        body = f"{pad}{SENTINEL_GUARD_BODY_INDENT}"
        return [
            f"{pad}{SENTINEL_GUARD_OPEN}",
            f"{body}{SENTINEL_GUARD_MOVE.format(sentinel=self._sentinel)}",
            f"{pad}{SENTINEL_GUARD_CLOSE}",
        ]

    @staticmethod
    def _normalize(source: str) -> str:
        return " ".join(str(source or "").split()).upper()

    def _say(self, key: str, **fields: object) -> None:
        template = DB2_DATE_SENTINEL_MESSAGES.get(key, "")
        if template:
            self.messages.append(template.format(**fields))


__all__ = ["Db2DateSentinelPolicy"]
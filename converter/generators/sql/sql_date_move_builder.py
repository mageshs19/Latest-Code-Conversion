# LOCATION: converter/generators/sql/sql_date_move_builder.py
# ACTION: REPLACE ENTIRE FILE

"""DB2 date column detection and CCYYMMDD -> DD.MM.CCYY move builder.

The null-date sentinel decision is NOT taken here. It belongs to
Db2DateSentinelPolicy, which is the single owner shared with
update_sql_cleanup/date_move_builder.py and
postprocess/update_date_host_converter.py. Three copies of one rule is
how a PARM-sourced date acquired a guard it never needed.
"""

from __future__ import annotations

from converter.services.db2_date_sentinel_policy import Db2DateSentinelPolicy
from converter.services.name_normalizer import NameNormalizer
from rules.sql_generation_rules import (
    DATE_COLUMN_PREFIXES,
    DATE_STAGING_FIELDS,
    DB2_DATE_NULL_SENTINEL,
)


class SqlDateMoveBuilder:
    """Builds the manual CCYYMMDD -> DD.MM.CCYY host move."""

    def __init__(self) -> None:
        # Owners drain component diagnostics by attribute. Declaring the
        # list here means a decision can never be taken silently, and no
        # call site has to change: the constructor takes no arguments.
        self.messages: list[str] = []

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #
    def is_db2_date_column(self, column_name: str) -> bool:
        column = NameNormalizer.normalize(column_name)
        return any(
            column.startswith(prefix) for prefix in DATE_COLUMN_PREFIXES
        )

    @staticmethod
    def _is_staging_field(source: str) -> bool:
        """True when the source is already a DB2 date staging field.

        A staging field is this builder's OUTPUT, not a valid input. Passing
        DA-DD-MM-CCYY back in moves 10 bytes into an 8-byte group, truncating
        the year, and the CORR move back writes garbage into the DB2 host.
        """
        return str(source or "").strip().upper() in DATE_STAGING_FIELDS

    # ------------------------------------------------------------------ #
    # Generation
    # ------------------------------------------------------------------ #
    def date_ymd8_to_db2_external_move(
        self,
        source_value: str,
        host_key: str,
    ) -> list[str]:
        """Convert a CCYYMMDD source value into DB2 external date DD.MM.CCYY,
        then move it into the DB2 date host field.

        Manual standard:
        - Clear DA-CCYYMMDD.
        - Move the source date into DA-CCYYMMDD.
        - Guard the value with the DB2 low-date sentinel ONLY when it can
          actually be unset. Db2DateSentinelPolicy decides; a JCL PARM date
          is always populated and is therefore not guarded.
        - Realign via DA-CCYYMMDD-R -> DA-DD-MM-CCYY.

        Precondition: source_value must be a CCYYMMDD (8-position) field.
        A staging field is rejected by _is_staging_field and moved directly,
        because it is already in DB2 external form.
        """
        source = str(source_value or "").strip()

        # Already converted. Re-running the block would destroy the value.
        if self._is_staging_field(source):
            return [
                f"MOVE DA-DD-MM-CCYY TO {host_key}",
            ]

        if not source:
            return [
                "MOVE ZEROES TO DA-CCYYMMDD",
                f"MOVE {DB2_DATE_NULL_SENTINEL} TO DA-CCYYMMDD",
                "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY",
                f"MOVE DA-DD-MM-CCYY TO {host_key}",
            ]

        sentinel = Db2DateSentinelPolicy(DB2_DATE_NULL_SENTINEL)
        guard = sentinel.guard_lines(source)
        self.messages.extend(sentinel.messages)

        return [
            "MOVE ZEROES TO DA-CCYYMMDD",
            f"MOVE {source} TO DA-CCYYMMDD",
            *guard,
            "MOVE CORR DA-CCYYMMDD-R TO DA-DD-MM-CCYY",
            f"MOVE DA-DD-MM-CCYY TO {host_key}",
        ]


__all__ = ["SqlDateMoveBuilder"]
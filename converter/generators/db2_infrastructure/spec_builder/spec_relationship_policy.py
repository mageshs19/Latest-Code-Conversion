# LOCATION: converter/generators/db2_infrastructure/spec_builder/spec_relationship_policy.py
# ACTION: REPLACE ENTIRE FILE
"""Creates safe relationship predicates for child cursor specifications.

THE GUARANTEE THIS CLASS PROTECTS
---------------------------------
A child predicate reads a host variable belonging to the PARENT::

    CT_RKTPROD_479EVEF = :DCLDZBEFFTV.CT-RKTPROD-479BEFF

That is only correct if the parent host group holds the current parent
row when the child cursor OPENs. For a parent the program NAVIGATES -
an OBTAIN or FIND of its own - the IDMS statement guarantees it. So a
parent that is not in ``navigated_records`` was refused.

CORRECTION 1 - AN LRF PARENT IS POSITIONED, NOT NAVIGATED
----------------------------------------------------------
After LrfPathExpander rewrites::

    OBTAIN FIRST VMBTL07-R01 WHERE ALL-VMBEVEF-BY-VMBEFF
        ->  OBTAIN FIRST VMBEVEF WITHIN VMBEFF-VMBEVEF

the parent VMBEFF is positioned by the SUBSCHEMA PATH, not by a
statement in the program. It therefore never appears in
``navigated_records``, the gate fired, and the child cursor was built
with NO WHERE clause at all::

    EXEC SQL DECLARE DZEVEFC1 CURSOR WITH HOLD FOR
      SELECT ... FROM DZEVEFTV
      ORDER BY NR_ID_479EVEF DESC
    END-EXEC.

An unqualified scan of the whole table. Worse, a cursor with no WHERE
is what CLASSIFY_PARENT_BY_ABSENT_WHERE uses to decide a cursor is the
DRIVER, so the child was then numbered 710/720/730 as if it were the
parent, and the close-guarantee pass drained it.

``lrf_cursors`` was already passed in - and read ONLY to emit a message,
AFTER the gate had already returned. The lookup now happens BEFORE the
gate, and an LRF-expanded record is allowed through.

THE COUPLING THIS CREATES, STATED PLAINLY
------------------------------------------
Allowing the predicate means something else must load the parent host
group before OPEN. That something is LrfHostVariablePopulator. If it
refuses, the cursor binds against an unpopulated group and returns the
wrong rows SILENTLY. The bypass is therefore REPORTED on every use, so
the pairing is visible in the conversion log and can be checked against
the populator's own message for the same cursor.

CORRECTION 2 - THE RECORD NAME WAS NOT NORMALISED FOR THE LOOKUP
-----------------------------------------------------------------
``SpecLrfScanner`` stores its keys as ``NameNormalizer.normalize(...)``.
``record in lrf_cursors`` compared the caller's raw spelling against
those keys, so a hyphenated or differently-cased record missed and the
LRF branch never fired. A separate normalised LOOKUP KEY is used; the
resolver is still called with the caller's original spelling, so no
existing resolution changes.

CORRECTION 3 - THE EMPTY-CONDITIONS EXIT WAS SILENT
----------------------------------------------------
``if not conditions: return []`` reported nothing, so "Sheet Mapping
carries no foreign-key rows for this record" and "the parent gate
fired" produced the identical empty result with no way to tell them
apart. Both exits now report. An unqualified AREA SWEEP legitimately
has no conditions, so this is a note for an LRF record, not an error.

CORRECTION 4 - UNMAPPED DIAGNOSTIC KEYS WERE DROPPED
-----------------------------------------------------
``SPEC_MESSAGES.get(key, "")`` followed by a bare return meant a key
with no template produced NOTHING. An unmapped key is now reported as
an unmapped key.
"""

from __future__ import annotations

from converter.services.name_normalizer import NameNormalizer
from rules.cursor_spec import SPEC_MESSAGES

UNMAPPED_DIAGNOSTIC_TEMPLATE = (
    "Cursor spec: unmapped diagnostic '{key}' {values}"
)
UNRENDERABLE_DIAGNOSTIC_TEMPLATE = (
    "Cursor spec: diagnostic '{key}' could not be rendered ({error})."
)


class SpecRelationshipPolicy:
    """Build predicates once and refuse joins with unpopulated parent hosts."""

    def __init__(self, relationship_resolver, where_builder) -> None:
        self.relationship_resolver = relationship_resolver
        self.where_builder = where_builder
        self.messages: list[str] = []

    def where_conditions(
        self,
        record: str,
        navigated_records: set[str],
        lrf_cursors: dict,
    ) -> list[str]:
        """Return one de-duplicated predicate list for a child record."""
        # Normalised ONLY for the lrf_cursors membership test and for
        # messages. The resolver keeps the caller's spelling so no
        # existing resolution can shift. See CORRECTION 2.
        lookup_key = NameNormalizer.normalize(record)
        lrf_entry = (lrf_cursors or {}).get(lookup_key)

        relationship = self.relationship_resolver.resolve_for_child_record(
            record
        )
        conditions = list(getattr(relationship, "conditions", []) or [])

        if not conditions:
            # An unqualified area sweep has no parent and no join; this
            # is a note, not a failure. See CORRECTION 3.
            self._log(
                "lrf_qualified_without_conditions"
                if lrf_entry is not None
                else "no_relationship_conditions",
                record=lookup_key,
            )
            return []

        parent = NameNormalizer.normalize(
            getattr(relationship, "parent_record", "")
        )

        if parent and parent not in navigated_records:
            if lrf_entry is None:
                self._log(
                    "parent_not_navigated",
                    record=lookup_key,
                    parent=parent,
                )
                return []

            # LRF: the parent is positioned by the subschema path. The
            # host group must be loaded before OPEN by the LRF populator
            # - reported so the pairing is visible. See CORRECTION 1.
            self._log(
                "lrf_parent_positioned_by_path",
                record=lookup_key,
                parent=parent,
                keyword=getattr(lrf_entry, "sweep_condition", ""),
                mode=getattr(lrf_entry, "mode", ""),
            )

        predicates = self.where_builder.predicates(conditions)

        if lrf_entry is not None and predicates:
            self._log(
                "lrf_where_already_present",
                record=lookup_key,
                count=len(predicates),
            )

        return predicates

    def _log(self, key: str, **fields) -> None:
        """Record one diagnostic. An unmapped key is REPORTED, not dropped."""
        template = SPEC_MESSAGES.get(key, "")

        if not template:
            rendered = " ".join(
                f"{name}={value}" for name, value in sorted(fields.items())
            )
            self.messages.append(
                UNMAPPED_DIAGNOSTIC_TEMPLATE.format(key=key, values=rendered)
            )
            return

        try:
            self.messages.append(template.format(**fields))
        except (KeyError, IndexError, ValueError) as error:
            self.messages.append(
                UNRENDERABLE_DIAGNOSTIC_TEMPLATE.format(key=key, error=error)
            )


__all__ = ["SpecRelationshipPolicy"]
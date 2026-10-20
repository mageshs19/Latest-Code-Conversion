# LOCATION: converter/transformers/field_reference_replacement_engine.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

import re

from converter.services.name_normalizer import NameNormalizer
from patterns.field_reference_rewriter_patterns import (
    OF_IN_AFTER_PATTERN,
    OF_IN_BEFORE_PATTERN,
    QUALIFIED_REFERENCE_PATTERN,
)
from rules.field_reference_rewriter_rules import PROTECTED_BARE_PREFIXES

# Reported once per (record, field) when a QUALIFIED reference names a
# record this program DID map, but a field of it that carries no DB2
# column. Belongs in rules/field_reference_rewriter_rules.py beside
# FIELD_REFERENCE_GEOMETRY_MESSAGES once that module owns the
# field-gap vocabulary.
UNMAPPED_FIELD_TEMPLATE = (
    "Qualified field rewrite: {field} OF {record} has no DB2 column in "
    "the Sheet Mapping; {count} other field(s) of {record} are mapped. "
    "Left unchanged."
)
GROUP_SPLIT_AT_USE_TEMPLATE = (
    "Field decomposition: {field} OF {record} is referenced here and "
    "maps to {count} DB2 columns ({columns}). A 1:N split needs a HELP- "
    "staging group and {count} MOVE statement(s); left unchanged."
)


class FieldReferenceReplacementEngine:
    """
    Rewrites qualified and bare IDMS field references using resolved
    Sheet Mapping + DCLGEN host-reference maps.

    CORRECTION 1 - AN UNMAPPED FIELD WAS DROPPED IN SILENCE
    ---------------------------------------------------------
    ``rewrite_qualified_references`` ended its no-target branch with::

        if not target:
            return match.group(0)

    and said nothing. A qualified reference whose RECORD is mapped but
    whose FIELD is not therefore survived into the output unchanged,
    with no entry in the run log. VM4BD310 shipped::

        OR CT-EVENT OF VMBEVEF = '0092'

    because ``CT-EVENT`` is a GROUP item and the Sheet Mapping row
    carries no ``New DB2_Field name``. The consequences were real and
    traceable only by accident:

      * the field usage analyzer counted ``condition=0`` for VMBEVEF,
      * so the column never reached the cursor SELECT list,
      * so the loop that exits on that predicate could never satisfy it,
      * so the program drained the whole set and abended.

    THE REPORT IS DELIBERATELY NARROW. ``QUALIFIED_REFERENCE_PATTERN``
    matches every ``FIELD OF RECORD`` in the program, and most of them
    are not IDMS records at all - ``CC OF TS-SYSTEM``,
    ``NR-ST-FORM-AS OF VMDZ205I``, ``DD OF DA-DD-MM-CCYY``. A message is
    emitted ONLY when the record IS in record_field_map and the named
    field is not, and it is deduplicated per (record, field).

    CORRECTION 2 - THE 1:N WORK LIST CAME FROM THE WRONG PLACE
    ------------------------------------------------------------
    FieldReferenceContextBuilder analyses every record in the WORKBOOK,
    so reporting a 1:N group split from there produced twenty-five
    findings per program for three real problems - the 01 RECORD rows,
    layout scaffolding no COBOL statement names, and records the program
    never touches.

    The builder now records the column list as DATA (``group_columns``)
    and this engine reports it at the REFERENCE SITE, because only the
    engine knows the field is actually used. ``group_columns`` is
    optional and defaults to None, so an older builder still works -
    the richer message simply does not appear.

    THIS ENGINE STILL DOES NOT FIX A SPLIT, AND CANNOT. record_field_map
    is ``dict[str, dict[str, str]]`` - ONE host per field - and a split
    needs 1 -> 3 statements plus a REDEFINES group in WORKING-STORAGE.
    Substitution cannot emit statements or declarations.

    BARE references are not reported: ``rewrite_bare_references``
    iterates the MAPPED fields, so an unmapped identifier is never a
    candidate and the engine has no way to tell a missing field from any
    other word on the line.
    """

    def __init__(
        self,
        *,
        record_field_map: dict[str, dict[str, str]],
        rewrite_messages: list[str],
        group_columns: dict[str, dict[str, list[str]]] | None = None,
    ) -> None:
        self.record_field_map = record_field_map
        self.rewrite_messages = rewrite_messages

        # record -> field -> the DB2 columns a 1:N split would need.
        # Optional so an older builder still constructs this engine.
        self.group_columns = group_columns or {}

        # Per-program. FieldReferenceRewriter.rewrite() builds a fresh
        # engine for every program, so this never leaks across a batch.
        self.unmapped_fields: set[tuple[str, str]] = set()

    def rewrite_qualified_references(
        self,
        text: str,
    ) -> str:
        def repl(match):
            source_field = NameNormalizer.to_cobol(match.group("field"))
            source_record = NameNormalizer.normalize(match.group("record"))

            target = self.target_for_record_field(
                record_name=source_record,
                source_field=source_field,
            )

            if not target:
                self.report_unmapped_field(
                    record=source_record,
                    field=source_field,
                )
                return match.group(0)

            self.rewrite_messages.append(
                f"Qualified field rewrite: {source_field} OF "
                f"{NameNormalizer.to_cobol(source_record)} -> {target}"
            )

            return target

        return QUALIFIED_REFERENCE_PATTERN.sub(
            repl,
            text,
        )

    def report_unmapped_field(
        self,
        *,
        record: str,
        field: str,
    ) -> None:
        """Report a field gap on a record this program DID map.

        Silent for a record that is not in the map at all: that is a
        COBOL group, a copybook layout or a work area, not an IDMS
        record this conversion is responsible for.

        When the builder knows the group's columns, the richer 1:N
        message is emitted instead - it names the fix.
        """
        record_key = NameNormalizer.normalize(record)
        field_key = self.field_key(field)

        if not record_key or not field_key:
            return

        mapped = self.record_field_map.get(record_key)

        if not mapped:
            return

        if field_key in mapped:
            return

        marker = (record_key, field_key)

        if marker in self.unmapped_fields:
            return

        self.unmapped_fields.add(marker)
        record_display = NameNormalizer.to_cobol(record_key)

        columns = self.group_columns.get(record_key, {}).get(field_key)

        if columns:
            self.rewrite_messages.append(
                GROUP_SPLIT_AT_USE_TEMPLATE.format(
                    field=field_key,
                    record=record_display,
                    count=len(columns),
                    columns=", ".join(columns),
                )
            )
            return

        self.rewrite_messages.append(
            UNMAPPED_FIELD_TEMPLATE.format(
                field=field_key,
                record=record_display,
                count=len(mapped),
            )
        )

    def rewrite_bare_references(
        self,
        *,
        text: str,
        active_record: str,
    ) -> str:
        record = NameNormalizer.normalize(active_record)

        if not record:
            return text

        field_map = self.record_field_map.get(record, {})

        if not field_map:
            return text

        updated = str(text or "")

        for source_key, target_reference in sorted(
            field_map.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            source_name = NameNormalizer.to_cobol(source_key)

            if not source_name or not target_reference:
                continue

            if self.is_protected_bare_source_name(source_name):
                continue

            updated = self.replace_bare_identifier(
                text=updated,
                source_name=source_name,
                target_name=target_reference,
            )

        return updated

    def replace_bare_identifier(
        self,
        *,
        text: str,
        source_name: str,
        target_name: str,
    ) -> str:
        source = NameNormalizer.to_cobol(source_name)
        target = str(target_name or "").strip()

        if not source or not target:
            return text

        pattern = re.compile(
            rf"(?<![A-Z0-9-]){re.escape(source)}(?![A-Z0-9-])",
            flags=re.IGNORECASE,
        )

        def repl(match):
            before_text = text[: match.start()]
            after_text = text[match.end() :]

            if self.is_part_of_qualified_reference(
                before_text=before_text,
                after_text=after_text,
            ):
                return match.group(0)

            self.rewrite_messages.append(
                f"Bare field rewrite: {source} -> {target}"
            )

            return target

        return pattern.sub(
            repl,
            text,
        )

    def target_for_record_field(
        self,
        *,
        record_name: str,
        source_field: str,
    ) -> str:
        record = NameNormalizer.normalize(record_name)
        field = self.field_key(source_field)

        if not record or not field:
            return ""

        return self.record_field_map.get(record, {}).get(field, "")

    def field_key(
        self,
        value: str,
    ) -> str:
        return NameNormalizer.to_cobol(value)

    def is_protected_bare_source_name(
        self,
        source_name: str,
    ) -> bool:
        source = NameNormalizer.to_cobol(source_name).upper()

        if not source:
            return True

        for prefix in PROTECTED_BARE_PREFIXES:
            if source.startswith(prefix):
                return True

        return False

    def is_part_of_qualified_reference(
        self,
        *,
        before_text: str,
        after_text: str,
    ) -> bool:
        before = str(before_text or "").upper()
        after = str(after_text or "").upper()

        if OF_IN_BEFORE_PATTERN.search(before):
            return True

        if OF_IN_AFTER_PATTERN.match(after):
            return True

        return False


__all__ = [
    "FieldReferenceReplacementEngine",
]
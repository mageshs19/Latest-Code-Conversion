# LOCATION: converter/transformers/field_reference_context_builder.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

from converter.repositories.mapping_repository import MappingRepository
from converter.resolvers.host_variable_resolver import HostVariableResolver
from converter.resolvers.table_name_resolver import TableNameResolver
from converter.services.name_normalizer import NameNormalizer
from converter.transformers.field_reference.field_reference_field_extractor import (
    FieldReferenceFieldExtractor,
)
from converter.transformers.field_reference.field_reference_host_resolver import (
    FieldReferenceHostResolver,
)
from rules.field_reference_rewriter_rules import DCLGEN_GROUP_PREFIX

# A COBOL group that contributes no bytes of its own.
FILLER_NAME = "FILLER"

# Reported when a group cannot be narrowed. Belongs in
# rules/field_reference_rewriter_rules.py once that module owns the
# decomposition vocabulary.
GROUP_SPLIT_TEMPLATE = (
    "Field decomposition: {field} OF {record} is a GROUP over {count} DB2 "
    "column(s) ({columns}); a 1:N split cannot be expressed as a field "
    "rewrite. Left unchanged."
)
GROUP_PARTIAL_TEMPLATE = (
    "Field decomposition: {field} OF {record} maps one column ({column}) "
    "but also covers {count} unmapped field(s) ({fields}); narrowing "
    "would silently drop them. Left unchanged."
)
GROUP_NARROWED_TEMPLATE = (
    "Field decomposition: {field} OF {record} is a GROUP whose only "
    "mapped content is {column}; resolved to it."
)


class FieldReferenceContextBuilder:
    """Builds record-to-field and record-to-DCLGEN context maps from Sheet
    Mapping and DCLGEN metadata.

    Orchestration only. Field-name parsing is delegated to
    FieldReferenceFieldExtractor and host-reference formatting to
    FieldReferenceHostResolver.

    CORRECTION - A FLAT READER OVER HIERARCHICAL DATA
    ---------------------------------------------------
    ``field_map_for_record`` skipped every row with no DB2 column::

        if not target_table or not target_column:
            continue

    The Sheet Mapping is a COBOL LAYOUT, not a flat list. ``Cobol Zone``
    carries the LEVEL NUMBER, so a row is a node in a tree::

        02 CT-EVENT                       GROUP   -> (no column)
        03   CT-RK-TEVPR    PIC X(4)              -> CT_RKTEVPR_479EVEF

        06 NR-ID-STOCK-CD                 GROUP   -> (no column)
        07   NR-ID-STOCK-R1                       -> NR_IDSTOCK_479BEFF  (12)
        07   NR-ID-STOCK-R2 REDEFINES ...         -> (no column)
        07   NR-CD-STOCK    PIC 9                 -> NR_CDSTK_479BEFF    (1)

    A group was therefore absent from record_field_map entirely, and every
    reference to it survived unrewritten and unreported::

        OR CT-EVENT OF VMBEVEF = '0092'

    with consequences three passes away: the field usage analyzer counted
    ``condition=0`` for VMBEVEF, the column never reached the cursor
    SELECT list, the loop that exits on that predicate could never satisfy
    it, and the program drained the whole set and abended.

    THREE RULES, ALL READ FROM THE DATA
    ------------------------------------
    1. OWN COLUMN WINS. A group with its own ``New DB2_Field name`` is
       already a 1:1 mapping and its children are a breakdown of a column
       that is mapped. ``DA-CR-EVENT-PROD`` -> ``DA_CREVTPD_479EVEF`` is
       this case, and descending into it would be wrong.

    2. A REDEFINES BRANCH OCCUPIES NO NEW BYTES. ``NR-ID-STOCK-R2`` and
       ``NR-ID-STOCK-R3`` are alternate views of ``NR-ID-STOCK-R1``;
       counting them would double the column list. FILLER contributes no
       mapped content either.

    3. GATHER TRANSITIVELY. ``KY-EFFECT`` is a level 02 group whose four
       columns sit at levels 04, 06 and 07. Immediate children are not
       enough.

    WHAT THIS DOES AND DOES NOT FIX
    --------------------------------
    EXACTLY ONE mapped column beneath a group, and no unmapped non-FILLER
    leaf -> the group IS that column, and it is resolved. ``CT-EVENT``
    and ``CT-RK-TGDSERV`` are this case.

    MORE THAN ONE -> a 1:N split. It needs a HELP- staging group and two
    or three MOVE statements, which a field-name substitution cannot
    express. REPORTED, never guessed. ``NR-ID-STOCK-CD`` (2 columns),
    ``NR-CI`` (2) and ``KY-EFFECT`` (4) are this case.

    ONE mapped column but an unmapped non-FILLER leaf alongside it ->
    narrowing would silently drop those bytes. REPORTED and refused.

    Every outcome reports, so the decomposition work list is measured per
    program instead of discovered from a run-time abend. ``messages`` is
    drained by FieldReferenceRewriter.rewrite().
    """

    def __init__(
        self,
        *,
        mapping_repository: MappingRepository,
        table_name_resolver: TableNameResolver,
        host_variable_resolver: HostVariableResolver,
    ) -> None:
        self.mapping_repository = mapping_repository
        self.table_name_resolver = table_name_resolver
        self.host_variable_resolver = host_variable_resolver
        self._extractor = FieldReferenceFieldExtractor()
        self._host_resolver = FieldReferenceHostResolver(host_variable_resolver)

        # Drained by FieldReferenceRewriter.rewrite(). Reset there too,
        # because one builder serves every program in a batch run.
        self.messages: list[str] = []

    def build_reference_maps(
        self,
    ) -> tuple[
        dict[str, dict[str, str]],
        dict[str, str],
        dict[str, str],
        dict[str, str],
    ]:
        self.messages = []

        record_field_map: dict[str, dict[str, str]] = {}
        record_group_map: dict[str, str] = {}
        table_record_map: dict[str, str] = {}
        group_record_map: dict[str, str] = {}

        for record in self.mapping_repository.records():
            normalized_record = NameNormalizer.normalize(record)
            if not normalized_record:
                continue

            resolved_table = self.table_name_resolver.table_for_record(
                normalized_record
            )

            if resolved_table:
                table_key = NameNormalizer.normalize(resolved_table)
                group_name = DCLGEN_GROUP_PREFIX + NameNormalizer.to_cobol(table_key)

                record_group_map[normalized_record] = group_name
                table_record_map[table_key] = normalized_record
                group_record_map[NameNormalizer.normalize(group_name)] = (
                    normalized_record
                )

            record_field_map[normalized_record] = self.field_map_for_record(
                normalized_record
            )

        self.add_redefines_aliases(record_field_map)

        return (
            record_field_map,
            record_group_map,
            table_record_map,
            group_record_map,
        )

    def field_map_for_record(self, record_name: str) -> dict[str, str]:
        output: dict[str, str] = {}
        rows = self.mapping_repository.rows_for_record(record_name)

        # Pass 1 - every row that carries a DB2 column of its own.
        for row in rows:
            source_candidates = self.source_candidates_from_row(row)
            if not source_candidates:
                continue

            target_reference = self.target_reference_for_row(row)
            if not target_reference:
                continue

            for source_candidate in source_candidates:
                source_key = self._extractor.field_key(source_candidate)
                if not source_key:
                    continue
                if source_key not in output:
                    output[source_key] = target_reference

        # Pass 2 - groups that carry no column of their own.
        self.add_group_resolutions(
            record_name=record_name,
            rows=rows,
            output=output,
        )

        return output

    #
    # Column resolution for one row
    #
    def target_reference_for_row(self, row) -> str:
        """The DCLGEN host reference this row maps to, or ''."""
        target_table = self.table_name_resolver.resolve_table(
            self._extractor.first_non_empty(
                getattr(row, "new_db2_record", ""),
                getattr(row, "cross_application_db2_table", ""),
            )
        )
        target_column = NameNormalizer.normalize(
            self._extractor.first_non_empty(
                getattr(row, "new_db2_field_name", ""),
                getattr(row, "cross_application_db2_field_name", ""),
            )
        )

        if not target_table or not target_column:
            return ""

        return self._host_resolver.dclgen_reference_for_column(
            table_name=target_table,
            column_name=target_column,
        )

    #
    # Hierarchy
    #
    def layout_nodes(self, rows) -> list[dict]:
        """One node per row that names a COBOL field, in layout order.

        Rows with no ``Cobol Zone`` are DB2-only columns - a denormalised
        parent key, a surrogate key, an audit column - and have no place
        in the IDMS layout tree.
        """
        nodes: list[dict] = []

        for row in rows:
            zone = str(getattr(row, "cobol_zone", "") or "").strip()
            if not zone:
                continue

            parts = zone.split()
            if not parts or not parts[0].isdigit():
                continue

            name = self._extractor.extract_field_name(zone)
            key = self._extractor.field_key(name) if name else ""
            if not key:
                continue

            nodes.append(
                {
                    "level": int(parts[0]),
                    "key": key,
                    "redefines": bool(
                        self._extractor.extract_redefines_base(zone)
                    ),
                    "filler": key.upper() == FILLER_NAME,
                    "reference": self.target_reference_for_row(row),
                }
            )

        return nodes

    def gather_mapped_content(
        self,
        nodes: list[dict],
        index: int,
    ) -> tuple[list[str], list[str]]:
        """(mapped references, unmapped leaf names) beneath nodes[index].

        A node with its own reference is TERMINAL: it is already a 1:1
        mapping and its children merely break it down. A REDEFINES node
        takes its whole subtree with it. FILLER is ignored.
        """
        level = nodes[index]["level"]
        references: list[str] = []
        unmapped: list[str] = []

        position = index + 1
        total = len(nodes)

        while position < total and nodes[position]["level"] > level:
            node = nodes[position]

            if node["redefines"] or node["filler"]:
                position = self.skip_subtree(nodes, position)
                continue

            if node["reference"]:
                if node["reference"] not in references:
                    references.append(node["reference"])
                position = self.skip_subtree(nodes, position)
                continue

            is_leaf = (
                position + 1 >= total
                or nodes[position + 1]["level"] <= node["level"]
            )

            if is_leaf and node["key"] not in unmapped:
                unmapped.append(node["key"])

            position += 1

        return references, unmapped

    @staticmethod
    def skip_subtree(nodes: list[dict], index: int) -> int:
        """Index of the first node that is NOT beneath nodes[index]."""
        level = nodes[index]["level"]
        position = index + 1

        while position < len(nodes) and nodes[position]["level"] > level:
            position += 1

        return position

    def add_group_resolutions(
        self,
        *,
        record_name: str,
        rows,
        output: dict[str, str],
    ) -> None:
        """Resolve a group with no column of its own. Reports every case."""
        nodes = self.layout_nodes(rows)
        record_display = NameNormalizer.to_cobol(record_name)

        for index, node in enumerate(nodes):
            if node["reference"] or node["redefines"] or node["filler"]:
                continue
            if node["key"] in output:
                continue

            references, unmapped = self.gather_mapped_content(nodes, index)

            if not references:
                # Not a decomposition: a group with no mapped content at
                # all. The rewrite engine already reports the reference
                # site, which is the actionable end.
                continue

            if len(references) > 1:
                self.messages.append(
                    GROUP_SPLIT_TEMPLATE.format(
                        field=node["key"],
                        record=record_display,
                        count=len(references),
                        columns=", ".join(references),
                    )
                )
                continue

            if unmapped:
                self.messages.append(
                    GROUP_PARTIAL_TEMPLATE.format(
                        field=node["key"],
                        record=record_display,
                        column=references[0],
                        count=len(unmapped),
                        fields=", ".join(unmapped),
                    )
                )
                continue

            output[node["key"]] = references[0]
            self.messages.append(
                GROUP_NARROWED_TEMPLATE.format(
                    field=node["key"],
                    record=record_display,
                    column=references[0],
                )
            )

    def source_candidates_from_row(self, row) -> list[str]:
        candidates: list[str] = []

        for value in [
            getattr(row, "cobol_zone", ""),
            getattr(row, "reference_field_name_copybook", ""),
        ]:
            field_name = self._extractor.extract_field_name(value)
            if not field_name:
                continue

            cobol_name = NameNormalizer.to_cobol(field_name)
            if cobol_name and cobol_name not in candidates:
                candidates.append(cobol_name)

            redefines_base = self._extractor.extract_redefines_base(value)
            if redefines_base:
                base_name = NameNormalizer.to_cobol(redefines_base)
                if base_name and base_name not in candidates:
                    candidates.append(base_name)

        return candidates

    def add_redefines_aliases(
        self,
        record_field_map: dict[str, dict[str, str]],
    ) -> None:
        for record in self.mapping_repository.records():
            normalized_record = NameNormalizer.normalize(record)
            rows = self.mapping_repository.rows_for_record(normalized_record)
            field_map = record_field_map.get(normalized_record, {})
            if not field_map:
                continue

            for row in rows:
                cobol_zone = getattr(row, "cobol_zone", "") or ""
                alias_name = self._extractor.extract_field_name(cobol_zone)
                base_name = self._extractor.extract_redefines_base(cobol_zone)
                if not alias_name or not base_name:
                    continue

                alias_key = self._extractor.field_key(alias_name)
                base_key = self._extractor.field_key(base_name)
                if not alias_key or not base_key:
                    continue
                if alias_key in field_map:
                    continue
                if base_key in field_map:
                    field_map[alias_key] = field_map[base_key]


__all__ = [
    "FieldReferenceContextBuilder",
]
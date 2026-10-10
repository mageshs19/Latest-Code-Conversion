# LOCATION: tests/cursor_where/_fixtures.py
# ACTION: CREATE NEW FILE
"""Shared names, stubs and assertions for the cursor WHERE suite.

Leading underscore so pytest does not collect it. Imported by
conftest.py and by every test module in this package.

No real customer name appears here; the fixtures define their own.
"""

from __future__ import annotations

from converter.generators.db2_infrastructure.cursor_spec import CursorSpec
from converter.resolvers.cursor_join_resolver import CursorJoinResolver
from rules.cursor_declaration_rules import BODY_LAST_COLUMN

# A rendered body carries the indicator, so a body of length n ends at
# physical column 7 + n.
BODY_COLUMN_OFFSET = 7

CURSOR = "DZBFASC1"

CHILD_RECORD = "VMBFAS"
CHILD_TABLE = "DZBFASTV"
CHILD_GROUP = "DCLDZBFASTV"

PARENT_RECORD = "VMBSIAS"
PARENT_TABLE = "DZBSIASTV"
PARENT_GROUP = "DCLDZBSIASTV"

KEY_COLUMN = "KY_SIFORM"
DATA_COLUMN = "DA_CPTAFS"
FOREIGN_COLUMN = "NR_CIOFMAS"
UNOWNED_COLUMN = "NR_PARENT_ONLY"

CHILD_COLUMNS = [KEY_COLUMN, DATA_COLUMN, FOREIGN_COLUMN]

EXPECTED_PREDICATE = f"{KEY_COLUMN} = :{PARENT_GROUP}.KY-SIFORM"
UNOWNED_PREDICATE = f"{UNOWNED_COLUMN} = :{PARENT_GROUP}.NR-PARENT-ONLY"


# =====================================================================
# Reading rendered output
# =====================================================================
def bodies(lines: list[str]) -> list[str]:
    """Non-blank lines, trimmed. Indentation is not under test here."""
    return [line.strip() for line in lines if line.strip()]


def clause_index(rendered: list[str], token: str) -> int:
    for index, body in enumerate(rendered):
        if body.upper().startswith(token):
            return index
    return -1


def has_clause(rendered: list[str], token: str) -> bool:
    return clause_index(rendered, token) >= 0


def assert_refusal(rendered: list[str], *expected_tokens: str) -> None:
    """A refusal is a DB2 WARNING block, not SQL.

    CORRECTION - a refusal was asserted by LINE COUNT.

        assert len(bodies) == 1

    pinned the single-line warning. That form rendered to ~77
    characters with real names, and the COBOL body window is columns
    8-72 - sixty-five - so the fixed-format composer wrapped or
    truncated the one comment explaining why a cursor is missing. The
    block is MULTI-LINE now, and a count was never the property worth
    asserting.

    What matters:
      - something is emitted, so the gap is visible in the source
      - every line carries the marker, so production validation and
        CHK-02 FORBIDDEN_MARKERS both catch it
      - every line fits the window, so nothing is truncated
      - no SQL is rendered, so nothing un-bindable reaches the program
    """
    assert rendered, "a refusal must emit something"
    assert all("DB2 WARNING" in body for body in rendered), rendered
    assert all(
        BODY_COLUMN_OFFSET + len(body) <= BODY_LAST_COLUMN
        for body in rendered
    ), rendered
    assert not any(
        body.upper().startswith(("EXEC SQL", "SELECT", "FROM", "WHERE"))
        for body in rendered
    ), rendered

    joined = " ".join(rendered)
    for token in expected_tokens:
        assert token in joined, f"{token!r} missing from {joined!r}"


# =====================================================================
# Stubs
# =====================================================================
class LineUtils:
    """Minimal stand-in for the infrastructure line utils.

    Only the two list renderers the declare builder calls are needed.
    Using a stub keeps the suite independent of fixed-format geometry.
    """

    @staticmethod
    def and_lines(items: list[str], indent: str) -> list[str]:
        return [
            f"{indent}{'AND ' if index else ''}{item}"
            for index, item in enumerate(items)
        ]

    @staticmethod
    def comma_lines(items: list[str], indent: str) -> list[str]:
        return [
            f"{indent}{', ' if index else ''}{item}"
            for index, item in enumerate(items)
        ]


class Condition:
    """A fully populated RelationshipCondition."""

    def __init__(
        self,
        child_column: str = KEY_COLUMN,
        parent_host_reference: str = f":{PARENT_GROUP}.KY-SIFORM",
    ) -> None:
        self.child_record = CHILD_RECORD
        self.child_table = CHILD_TABLE
        self.child_column = child_column
        self.parent_record = PARENT_RECORD
        self.parent_table = PARENT_TABLE
        self.parent_column = KEY_COLUMN
        self.parent_host_reference = parent_host_reference


class PartialCondition:
    """D-5: a condition missing child_table entirely."""

    def __init__(self) -> None:
        self.child_column = "NOT_A_COLUMN"
        self.parent_column = KEY_COLUMN
        self.parent_host_reference = f":{PARENT_GROUP}.KY-SIFORM"


class Resolution:
    def __init__(
        self,
        conditions: list | None = None,
        parent_table: str = PARENT_TABLE,
    ) -> None:
        self.child_record = CHILD_RECORD
        self.child_table = CHILD_TABLE
        self.parent_record = PARENT_RECORD
        self.parent_table = parent_table
        self.conditions = list(conditions or [])
        self.diagnostics: list[str] = []


class ColumnNameResolver:
    def __init__(self, columns: list[str] | None = None) -> None:
        self._columns = list(CHILD_COLUMNS if columns is None else columns)

    def columns_for_table(self, table_name: str) -> list[str]:
        if str(table_name or "").upper() == CHILD_TABLE:
            return list(self._columns)
        if str(table_name or "").upper() == PARENT_TABLE:
            return [KEY_COLUMN]
        return []


class HostVariableResolver:
    """The REAL resolver surface.

    D-2: there is deliberately no host_for_column() here. Any production
    call to that name raises AttributeError and fails the test.
    """

    def group_for_table(self, table: str) -> str:
        table = str(table or "").upper()
        if table == CHILD_TABLE:
            return CHILD_GROUP
        if table == PARENT_TABLE:
            return PARENT_GROUP
        return ""

    def host_reference_for_column(
        self,
        table_name: str,
        column_name: str,
    ) -> str:
        group = self.group_for_table(table_name)
        if not group:
            return ""
        return f":{group}.{str(column_name or '').replace('_', '-')}"


class TableNameResolver:
    @staticmethod
    def table_for_record(record_name: str) -> str:
        record = str(record_name or "").upper()
        if record == CHILD_RECORD:
            return CHILD_TABLE
        if record == PARENT_RECORD:
            return PARENT_TABLE
        return ""


class KeyColumnResolver:
    def __init__(self, primary_keys: list[str] | None = None) -> None:
        self._primary_keys = list(
            [KEY_COLUMN] if primary_keys is None else primary_keys
        )

    def primary_key_columns_for_record(self, record_name: str) -> list[str]:
        return list(self._primary_keys)


class RelationshipResolver:
    """Facade exposing resolve(), as most call paths do."""

    def __init__(
        self,
        resolution=None,
        primary_keys: list[str] | None = None,
    ) -> None:
        self._resolution = resolution
        self.table_name_resolver = TableNameResolver()
        self.key_column_resolver = KeyColumnResolver(primary_keys)

    def resolve(self, child_record: str):
        return self._resolution


class LegacyRelationshipResolver:
    """D-4: facade exposing ONLY resolve_for_child_record()."""

    def __init__(self, resolution=None) -> None:
        self._resolution = resolution
        self.table_name_resolver = TableNameResolver()
        self.key_column_resolver = KeyColumnResolver()

    def resolve_for_child_record(self, child_record: str):
        return self._resolution


# =====================================================================
# Builders
# =====================================================================
def join(
    relationship_resolver,
    columns: list[str] | None = None,
) -> CursorJoinResolver:
    return CursorJoinResolver(
        relationship_resolver=relationship_resolver,
        column_name_resolver=ColumnNameResolver(columns),
        host_variable_resolver=HostVariableResolver(),
    )


def spec(
    order: int = 0,
    cursor_name: str = CURSOR,
    table_name: str = CHILD_TABLE,
    select_columns: list[str] | None = None,
    where_conditions: list[str] | None = None,
    order_by_columns: list[str] | None = None,
) -> CursorSpec:
    """CursorSpec.read() is the door the production path uses.

    Db2InfrastructureGenerator builds plain dicts; the builder never
    receives one. Going through read() keeps the fixture honest.
    """
    return CursorSpec.read(
        {
            "cursor_name": cursor_name,
            "table_name": table_name,
            "record_name": CHILD_RECORD,
            "select_columns": (
                CHILD_COLUMNS if select_columns is None else select_columns
            ),
            "where_conditions": list(where_conditions or []),
            "order_by_columns": list(order_by_columns or []),
            "cursor_order": order,
        }
    )
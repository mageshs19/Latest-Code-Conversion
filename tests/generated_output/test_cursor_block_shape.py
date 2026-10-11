from __future__ import annotations

SQL_LOCATION_SUFFIX = "TO SQL-LOCATION"
EXEC_SQL = "EXEC SQL"
END_EXEC = "END-EXEC"


def _sql_cursor_names(bodies: list[str], verb: str) -> set[str]:
    token = f"{verb.upper()} "
    inside = False
    found: set[str] = set()

    for body in bodies:
        text = body.strip().upper()

        if text.startswith(EXEC_SQL):
            inside = END_EXEC not in text
            continue

        if text.startswith(END_EXEC):
            inside = False
            continue

        if not inside or not text.startswith(token):
            continue

        parts = text.split()
        if len(parts) == 2:
            found.add(parts[1].rstrip("."))

    return found


def _entry_move(bodies: list[str], index: int) -> bool:
    for position in range(index, -1, -1):
        text = bodies[position].strip().upper()
        if text.endswith(SQL_LOCATION_SUFFIX):
            return True
        if text.endswith(".") and " " not in bodies[position]:
            return False
    return False


def test_every_sqlcode_error_branch_sets_sql_location(generated_bodies):
    inside = False
    checked = 0

    for index, body in enumerate(generated_bodies):
        text = body.strip().upper()

        if text.startswith("EVALUATE SQLCODE"):
            inside = True
            continue
        if text.startswith("EVALUATE") or text.startswith("END-EVALUATE"):
            inside = False
            continue
        if not inside or text != "WHEN OTHER":
            continue

        branch = generated_bodies[index + 1].strip().upper()
        assert branch.endswith(SQL_LOCATION_SUFFIX) or _entry_move(
            generated_bodies, index
        ), (
            f"SQLCODE error branch at body index {index} has no "
            f"SQL-LOCATION in scope: {generated_bodies[index + 1]!r}"
        )
        checked += 1

    assert checked > 0


def test_every_declare_carries_a_queryno(generated_bodies):
    declares = [
        body
        for body in generated_bodies
        if "DECLARE" in body.upper() and "CURSOR" in body.upper()
    ]
    querynos = [
        body
        for body in generated_bodies
        if body.strip().upper().startswith("QUERYNO ")
    ]

    assert declares
    assert len(querynos) == len(declares)


def test_every_opened_cursor_is_closed(generated_bodies):
    opened = _sql_cursor_names(generated_bodies, "OPEN")
    closed = _sql_cursor_names(generated_bodies, "CLOSE")

    assert opened
    assert opened == closed


def test_file_close_is_not_counted_as_a_cursor(generated_bodies):
    closed = _sql_cursor_names(generated_bodies, "CLOSE")
    for name in closed:
        assert name.endswith("C1") or name.startswith("DZ"), name
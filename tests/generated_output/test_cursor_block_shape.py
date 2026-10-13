# LOCATION: tests/generated_output/test_cursor_block_shape.py
# ACTION: REPLACE ENTIRE FILE

from __future__ import annotations

SQL_LOCATION_SUFFIX = "TO SQL-LOCATION"
EXEC_SQL = "EXEC SQL"
END_EXEC = "END-EXEC"
QUERYNO_TOKEN = "QUERYNO "
DECLARE_TOKEN = "DECLARE"
CURSOR_TOKEN = "CURSOR"
PERFORM_TOKEN = "PERFORM "

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


def _sql_blocks(bodies: list[str]) -> list[list[str]]:
    """Every EXEC SQL ... END-EXEC block, opening line included.

    The opening line is kept because the generator emits

        EXEC SQL DECLARE DZBFASC1 CURSOR WITH HOLD FOR

    on ONE body, so a block classifier that skipped it would never
    recognise a DECLARE.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    inside = False

    for body in bodies:
        text = body.strip().upper()

        if text.startswith(EXEC_SQL):
            current = [text]
            if END_EXEC in text:
                blocks.append(current)
                current = []
                inside = False
            else:
                inside = True
            continue

        if not inside:
            continue

        if text.startswith(END_EXEC):
            blocks.append(current)
            current = []
            inside = False
            continue

        current.append(text)

    if current:
        blocks.append(current)

    return blocks


def _is_declare_block(block: list[str]) -> bool:
    return any(
        DECLARE_TOKEN in line and CURSOR_TOKEN in line for line in block
    )


def _entry_move(bodies: list[str], index: int) -> bool:
    for position in range(index, -1, -1):
        text = bodies[position].strip().upper()
        if text.endswith(SQL_LOCATION_SUFFIX):
            return True
        if text.endswith(".") and " " not in bodies[position]:
            return False
    return False


def _context(bodies: list[str], index: int, before: int = 14) -> str:
    start = max(0, index - before)
    return "\n".join(
        f"  [{position}] {bodies[position]!r}"
        for position in range(start, min(len(bodies), index + 3))
    )


def test_every_sqlcode_error_branch_sets_sql_location(generated_bodies):
    """Every WHEN OTHER branch must be traceable to a SQL-LOCATION.

    The failure message now carries the surrounding bodies. A bare
    'no SQL-LOCATION in scope' said nothing about WHICH block, and the
    artefact had to be read by hand to find out.
    """
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
        assert (
            branch.endswith(SQL_LOCATION_SUFFIX)
            or _entry_move(generated_bodies, index)
            or _sqlcode_owner_is_performed(generated_bodies, index)
        ), (
            f"SQLCODE error branch at body index {index} has no "
            f"SQL-LOCATION in scope: {generated_bodies[index + 1]!r}\n"
            f"context:\n{_context(generated_bodies, index)}"
        )
        checked += 1

    assert checked > 0


def test_every_declare_carries_a_queryno(generated_bodies):
    """A cursor DECLARE must carry its own QUERYNO.

    CORRECTION - the count was PROGRAM-WIDE.

    The previous assertion compared every 'QUERYNO nnn' in the program
    with the number of cursor DECLAREs:

        assert len(querynos) == len(declares)

    Restart SQL legitimately carries its own QUERYNO - SELECT, UPDATE
    and INSERT on the restart table - so a program with ONE cursor and a
    restart family measured

        4 QUERYNO  vs  1 DECLARE

    and failed on CORRECT output. QUERYNO belongs to a STATEMENT, not to
    the cursor family, so the check is scoped to the DECLARE block: each
    DECLARE must carry one, and QUERYNOs elsewhere are none of this
    test's business.
    """
    blocks = [b for b in _sql_blocks(generated_bodies) if _is_declare_block(b)]

    assert blocks, "no EXEC SQL DECLARE ... CURSOR block was generated"

    missing = [
        block
        for block in blocks
        if not any(line.startswith(QUERYNO_TOKEN) for line in block)
    ]

    assert not missing, (
        f"{len(missing)} of {len(blocks)} cursor DECLARE block(s) carry "
        f"no {QUERYNO_TOKEN.strip()}: "
        f"{[block[0] for block in missing]}"
    )


def test_every_opened_cursor_is_closed(generated_bodies):
    opened = _sql_cursor_names(generated_bodies, "OPEN")
    closed = _sql_cursor_names(generated_bodies, "CLOSE")

    assert opened
    assert opened == closed


def test_file_close_is_not_counted_as_a_cursor(generated_bodies):
    closed = _sql_cursor_names(generated_bodies, "CLOSE")
    for name in closed:
        assert name.endswith("C1") or name.startswith("DZ"), name

def _opening_evaluate(bodies: list[str], index: int) -> int:
    """Index of the EVALUATE SQLCODE that opens the block holding `index`."""
    for position in range(index, -1, -1):
        if bodies[position].strip().upper().startswith("EVALUATE SQLCODE"):
            return position
    return -1


def _sqlcode_owner_is_performed(bodies: list[str], index: int) -> bool:
    """True when the SQLCODE under test was set in ANOTHER paragraph.

    700-RESTART-CONTROL evaluates the SQLCODE of a statement it does not
    contain:

        PERFORM 700-SELECT-DZ01RSTV.
        EVALUATE SQLCODE
          ...
          WHEN OTHER
               PERFORM SQLERROR

    The MOVE to SQL-LOCATION was written by 700-SELECT-DZ01RSTV, which
    this module checks in its own right. Requiring a second MOVE in the
    CALLER would overwrite the location of the statement that actually
    failed - the opposite of what SQL-LOCATION is for.

    Only the statement IMMEDIATELY before the EVALUATE is considered. A
    PERFORM inside the branches (WHEN 0 / WHEN 100) must never satisfy
    this test.
    """
    opening = _opening_evaluate(bodies, index)
    if opening <= 0:
        return False

    for position in range(opening - 1, -1, -1):
        text = bodies[position].strip().upper()
        if text:
            return text.startswith(PERFORM_TOKEN)
    return False
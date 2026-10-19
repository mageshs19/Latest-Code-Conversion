# LOCATION: converter/composers/record_materialisation/record_entry_renderer.py
# ACTION: REPLACE ENTIRE FILE
"""Renders a group entry and an elementary entry.

Templates plus geometry. Decides nothing about the record as a whole -
it is handed a level, a name, a picture and an indent, and returns one
finished body line.

    06  VMBFAS.
      07  CT-RK-TGDSV             PIC X(4).
      07  FILLER                  PIC X(2).

CORRECTION - VALUE ZEROES was emitted onto a REDEFINES entry
--------------------------------------------------------------
picture_of() is the ONE builder of the picture text, and
RecordLayoutGenerator._entry() calls it for EVERY field BEFORE it picks
a renderer:

    picture = self.entries.picture_of(item)

    if item.is_redefinition:
        return self.redefines.render(..., picture=picture, ...)

So the string handed to RecordRedefinesRenderer already carried the
VALUE clause, and the generated layout read

    10  CT-RK-TGOOD    REDEFINES CT-RK-TGDSV
        PIC 9(4) VALUE ZEROES.

A REDEFINES entry owns NO storage. It is an alternate reading of bytes
the redefined field already initialised, so COBOL forbids a VALUE
clause on it. IBM Enterprise COBOL raises a severity-S diagnostic, the
compile ends RC=12, no load module is produced and the job step fails.

The manual reference agrees -
mainframe/workspace/Manual Output/VMDZ7200.cbl, lines 81-83:

    10 CT-RK-TGDSV   PIC X(4).
    10 CT-RK-TGOOD   REDEFINES CT-RK-TGDSV
                     PIC 9(4).

RecordFieldPlan.is_redefinition has always answered this question and
nothing asked it. picture_of() already receives the whole item, so the
answer costs ONE condition.

RecordRedefinesRenderer is NOT at fault - it faithfully prints the
string it is given. record_layout_generator.py is NOT at fault either -
it already routes to the right renderer. Neither file changes.

WHY THE GUARD TYPE-CHECKS WHAT IT READS
----------------------------------------
picture_of() is duck-typed on purpose: the plan builder may wrap a row
in its own value object, so `item` is not guaranteed to be a
RecordFieldPlan. Any object that auto-creates attributes answers TRUE
to the obvious form

    bool(getattr(item, "is_redefinition", False))

and unittest.mock.Mock is exactly such an object:

    bool(Mock().is_redefinition)   -> True

Every Mock-built field in tests/test_db2_code_fixes.py would then be
classified as a redefinition and lose its VALUE clause. The same hole
would swallow any caller passing a proxy, a SimpleNamespace, or a stub.

_is_redefinition() therefore accepts only EVIDENCE:

    1. is_redefinition is honoured only when it is a genuine bool,
    2. otherwise the declared str field `redefines` decides,
    3. anything else - a Mock, a proxy, None - is NOT evidence.

Both paths agree for a real RecordFieldPlan, where `redefines` is a str
and `is_redefinition` returns bool(self.redefines).

False is the SAFE default: an unrecognised object keeps the behaviour
that existed before this guard, so nothing can silently lose a VALUE
clause it is entitled to.

NOT A TEXT CHECK, DELIBERATELY
-------------------------------
The REDEFINES clause and the PIC clause land on DIFFERENT physical
lines whenever RecordRedefinesRenderer wraps the entry. A guard reading
the rendered text would have to re-join those lines - a second parser
maintained beside the real one, which is the shape of defect that let
this through in the first place. The model knows; ask the model.

LEVEL 88 IS NOT RENDERED HERE
------------------------------
A condition-name VALUE is legal under a redefinition, but this class
renders groups and elementary items only. No 88 reaches picture_of(),
so no exception is coded for one.
"""

from __future__ import annotations

from converter.composers.record_materialisation.record_layout_geometry import (
    RecordLayoutGeometry,
)
from rules.record_materialisation_rules import (
    ELEMENTARY_ITEM_TEMPLATE,
    GROUP_ITEM_TEMPLATE,
)


class RecordEntryRenderer:
    """One data description entry, group or elementary."""

    def __init__(self, geometry: RecordLayoutGeometry | None = None) -> None:
        self.geometry = geometry or RecordLayoutGeometry()

    # ------------------------------------------------------------ group
    def group(self, *, level: str, name: str, indent: str) -> str:
        """`06  VMBFAS.`"""
        body = GROUP_ITEM_TEMPLATE.format(
            level=level,
            name=self.clean_name(name),
        )
        return self.geometry.cap(
            self.geometry.terminate(indent + body)
        )

    # ------------------------------------------------------- elementary
    def elementary(
        self,
        *,
        level: str,
        name: str,
        picture: str,
        indent: str,
    ) -> str:
        """`07  CT-RK-TGDSV             PIC X(4).`

        A blank picture means the sheet declared a group, so the entry
        falls back to the group shape rather than emitting a bare name.
        """
        clean_picture = str(picture or "").strip()
        clean_name = self.clean_name(name)

        if not clean_picture:
            return self.group(level=level, name=clean_name, indent=indent)

        width = self.geometry.name_width(
            indent=indent,
            level=level,
            name=clean_name,
            picture=clean_picture,
        )
        body = ELEMENTARY_ITEM_TEMPLATE.format(
            level=level,
            name=clean_name,
            width=width,
            picture=clean_picture,
        )
        return self.geometry.cap(
            self.geometry.terminate(indent + body)
        )

    # ---------------------------------------------------------- helpers
    @staticmethod
    def picture_of(item) -> str:
        """'PIC S9(13)V99' + 'COMP-3' -> 'PIC S9(13)V99 VALUE ZEROES'.

        Strips COMP-3 and other binary/packed encoding from picture clause
        to generate DB2-compatible COBOL with plain numeric fields.

        A REDEFINES entry never receives a VALUE clause - see the module
        docstring.
        """
        picture = str(getattr(item, "picture", "") or "")
        usage = str(getattr(item, "usage", "") or "")

        # Filter out binary encoding clauses that shouldn't be in DB2 output
        excluded_usage = {"COMP-3", "COMP-2", "COMP-1", "COMPUTATIONAL-3",
                          "COMPUTATIONAL-2", "COMPUTATIONAL-1", "PACKED-DECIMAL"}

        # Only include USAGE if it's not a binary encoding clause
        if usage and usage.strip().upper() not in excluded_usage:
            result = f"{picture} {usage}".strip()
        else:
            result = picture.strip()

        # A VALUE clause is legal only on an entry that OWNS storage.
        # A REDEFINES entry owns none: severity S, RC=12.
        if RecordEntryRenderer._is_redefinition(item):
            return result

        # Add VALUE ZEROES for numeric PIC clauses without it
        if result and "PIC" in result and "VALUE" not in result:
            if any(pic in result.upper() for pic in ["PIC 9", "PIC S9"]):
                result = f"{result} VALUE ZEROES"

        return result

    @staticmethod
    def _is_redefinition(item) -> bool:
        """True only on EVIDENCE, never on a duck-typed truthy value.

        See the module docstring for why a plain truth test is unsafe
        here. Order matters:

            1. a genuine bool from is_redefinition is authoritative,
            2. otherwise the declared str field `redefines` decides,
            3. anything else is NOT evidence -> False.
        """
        flag = getattr(item, "is_redefinition", None)
        if isinstance(flag, bool):
            return flag

        redefines = getattr(item, "redefines", "")
        if not isinstance(redefines, str):
            return False
        return bool(redefines.strip())

    @staticmethod
    def clean_name(name: str) -> str:
        return str(name or "").strip().upper()


__all__ = ["RecordEntryRenderer"]
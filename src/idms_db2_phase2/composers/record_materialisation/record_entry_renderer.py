# LOCATION: src/idms_db2_phase2/composers/record_materialisation/record_entry_renderer.py
# ACTION: CREATE NEW FILE
"""Renders a group entry and an elementary entry.

Templates plus geometry. Decides nothing about the record as a whole -
it is handed a level, a name, a picture and an indent, and returns one
finished body line.

    06  VMBFAS.
      07  CT-RK-TGDSV             PIC X(4).
      07  FILLER                  PIC X(2).
"""

from __future__ import annotations

from idms_db2_phase2.composers.record_materialisation.record_layout_geometry import (
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
        
        # Add VALUE ZEROES for numeric PIC clauses without it
        if result and "PIC" in result and "VALUE" not in result:
            if any(pic in result.upper() for pic in ["PIC 9", "PIC S9"]):
                result = f"{result} VALUE ZEROES"
        
        return result

    @staticmethod
    def clean_name(name: str) -> str:
        return str(name or "").strip().upper()


__all__ = ["RecordEntryRenderer"]
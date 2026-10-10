# LOCATION: tools/probe_join_key_label.py
# ACTION: CREATE NEW FILE  (delete after use)
"""Three questions, in order. The first NO is the defect."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TABLE = "DZBEFFTV"
COLUMN = "CT_RKTPROD_479BEFF"
HOST = "CT-RKTPROD-479BEFF"


def main(mapping_repository) -> None:
    # 1. does the accessor exist?
    has = hasattr(mapping_repository, "cobol_field_for_column")
    print(f"1. accessor present      : {has}")
    if not has:
        print("   -> add it to MappingRepository. Nothing else matters.")
        return

    # 2. does it resolve this column?
    value = mapping_repository.cobol_field_for_column(
        table_name=TABLE, column_name=COLUMN
    )
    print(f"2. resolves {COLUMN:<22}: {value or '(empty)'}")
    if not value:
        print("   -> check the Sheet Mapping COBOL Zone cell for this row.")
        return

    # 3. does the resolver return it?
    from converter.generators.cursor_paragraph.join_key_label_resolver import (
        JoinKeyLabelResolver,
    )

    resolver = JoinKeyLabelResolver(mapping_repository)
    label = resolver.label_for(table=TABLE, column=COLUMN, host=HOST)
    print(f"3. resolver label        : {label}")
    print(f"   fallback messages     : {resolver.messages or 'none'}")


if __name__ == "__main__":
    print("Call main() with a loaded MappingRepository.")
from converter.generators.timestamp_generator import TimestampGenerator

SOURCE = "\n".join([
    "       DATA DIVISION.",
    "       FILE SECTION.",
    "       FD  UITBST",
    "           RECORD CONTAINS 50 CHARACTERS.",
    "       01  UITRECORD.",
    "           03  UIT-NR-ID                PIC X(04).",
    "       WORKING-STORAGE SECTION.",
    "       01  WS-TE-WORK.",
    "           10  WS-STATUS                PIC X    VALUE SPACE.",
    "       LINKAGE SECTION.",
    "       01  PARAM-DATONLY.",
    "           03  L-PARAM                  PIC S9(4) COMP.",
    "       PROCEDURE DIVISION USING PARAM-DATONLY.",
    "           DISPLAY 'GO'",
    "           STOP RUN.",
])

text, messages = TimestampGenerator().apply(SOURCE, "VMDZ4420")
print(text)
print("--- MESSAGES ---")
print("\n".join(messages))
print("--- IDEMPOTENT ---")
again, _ = TimestampGenerator().apply(text, "VMDZ4420")
print("stable" if again == text else "CHANGED ON SECOND RUN")

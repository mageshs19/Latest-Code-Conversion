# LOCATION: tests/test_lrf_update_expander.py
# ACTION: CREATE NEW FILE
"""LRF update (MODIFY / STORE) expansion tests.

ASSERTION CONTRACT
------------------
Like the read/delete expander, the update expander KEEPS an audit trail:
every expanded statement is preceded by a '*DB2:' comment quoting the
original LRF statement, and every refusal keeps a '*DB2-KEEP:' comment.
Those comments are a feature, not residue, so assertions about "no LRF verb
remains" must look at EXECUTABLE lines only.
"""

from converter.parsers.lrf_parser import LrfParser
from converter.repositories.lrf_repository import LrfRepository
from converter.resolvers.lrf_path_resolver import LrfPathResolver
from converter.transformers.lrf_update_expander import LrfUpdateExpander


# A MODIFY path-group (single element) and a STORE path-group (two elements).
SUBSCHEMA = """
     ADD SUBSCHEMA NAME IS VMBTS07 OF SCHEMA NAME IS VMBTSCH
         .
     ADD LOGICAL RECORD VMBTL07-R01
         ELEMENTS ARE
             VMBEFF
         .
     ADD LOGICAL RECORD VMBTL07-R02
         ELEMENTS ARE
             VMBWCEF
             VMBEVEF
         .
     ADD PATH-GROUP MODIFY VMBTL07-R01
         SELECT FOR KEYWORD MO-VMBEFF
             FIND CURRENT VMBEFF
                 ON 0000 NEXT
             MODIFY VMBEFF
                 ON 0000 NEXT
         .
     ADD PATH-GROUP STORE VMBTL07-R02
         SELECT FOR KEYWORD ST-VMBWCEF-TO-VMBEVEF
             OBTAIN FIRST VMBWCEF WITHIN AR-VMBWRM1
                 ON 0000 NEXT
             STORE VMBWCEF
                 ON 0000 NEXT
             STORE VMBEVEF
                 ON 0000 NEXT
         .
"""

COMMENT_INDICATORS = ("*", "/")


# ---------------------------------------------------------------- helpers
def _expander(mapping_repository=None):
    records = LrfParser().parse(SUBSCHEMA)
    resolver = LrfPathResolver(
        lrf_repository=LrfRepository(records),
        mapping_repository=mapping_repository,
    )
    return LrfUpdateExpander(path_resolver=resolver)


def _is_comment(line: str) -> bool:
    text = str(line or "")
    if len(text) >= 7 and text[:6].strip().isdigit():
        return text[6] in COMMENT_INDICATORS
    return text.lstrip().startswith(COMMENT_INDICATORS)


def _executable(output: str) -> str:
    return "\n".join(
        line for line in str(output or "").splitlines()
        if line.strip() and not _is_comment(line)
    )


def _comments(output: str) -> str:
    return "\n".join(
        line for line in str(output or "").splitlines()
        if _is_comment(line)
    )


# --------------------------------------------------------------- expansion
def test_modify_is_expanded_to_classic_idms():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    code = _executable(_expander().expand(source))

    assert "MODIFY VMBEFF." in code
    # No logical-record verb survives as EXECUTABLE code.
    assert "VMBTL07-R01" not in code
    assert "WHERE MO-VMBEFF" not in code


def test_modify_expansion_keeps_an_audit_trail():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    notes = _comments(_expander().expand(source))

    assert "*DB2:" in notes
    assert "VMBTL07-R01" in notes
    assert "MO-VMBEFF" in notes


def test_expanded_names_use_cobol_hyphens_never_underscores():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    assert "_" not in _expander().expand(source)


def test_store_into_single_element_lr_is_expanded():
    """A STORE keyword whose logical record has one element is unambiguous."""
    subschema = """
     ADD LOGICAL RECORD VMBTL09-R01
         ELEMENTS ARE
             VMBONE
         .
     ADD PATH-GROUP STORE VMBTL09-R01
         SELECT FOR KEYWORD ST-VMBONE
             OBTAIN FIRST VMBONE WITHIN AR-VMBONE
                 ON 0000 NEXT
             STORE VMBONE
                 ON 0000 NEXT
         .
"""
    records = LrfParser().parse(subschema)
    resolver = LrfPathResolver(lrf_repository=LrfRepository(records))
    expander = LrfUpdateExpander(path_resolver=resolver)

    source = (
        "       PROCEDURE DIVISION.\n"
        "           STORE VMBTL09-R01 WHERE ST-VMBONE.\n"
    )
    code = _executable(expander.expand(source))

    assert "STORE VMBONE." in code
    assert "VMBTL09-R01" not in code


# ----------------------------------------------------------- safe refusal
def test_store_with_multiple_elements_is_kept_for_manual_review():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           STORE VMBTL07-R02 WHERE ST-VMBWCEF-TO-VMBEVEF.\n"
    )
    out = _expander().expand(source)
    notes = _comments(out)
    code = _executable(out)

    assert "*DB2-KEEP:" in notes
    assert "ST-VMBWCEF-TO-VMBEVEF" in notes
    # Nothing was guessed: no classic STORE statement was emitted.
    assert "STORE VMBWCEF" not in code
    assert "STORE VMBEVEF" not in code


def test_unknown_keyword_is_kept_and_commented():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE UNKNOWN-KEYWORD.\n"
    )
    out = _expander().expand(source)

    assert "*DB2-KEEP:" in _comments(out)
    assert "UNKNOWN-KEYWORD" in _comments(out)
    assert "MODIFY VMBEFF" not in _executable(out)


def test_unmapped_record_is_kept_for_manual_review():
    class _NoRecordMapping:
        def has_record(self, _record):
            return False

    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    out = _expander(mapping_repository=_NoRecordMapping()).expand(source)

    assert "*DB2-KEEP:" in _comments(out)
    assert "MODIFY VMBEFF" not in _executable(out)


# ------------------------------------------------------- no-LRF contract
def test_without_lrf_metadata_source_is_unchanged():
    resolver = LrfPathResolver(
        lrf_repository=LrfRepository([]),
        mapping_repository=None,
    )
    expander = LrfUpdateExpander(path_resolver=resolver)
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    assert expander.expand(source) == source


def test_program_without_lrf_update_syntax_is_unchanged():
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBEFF.\n"
        "           OBTAIN FIRST VMBEFF WITHIN AR-VMBFRM1.\n"
    )
    assert _expander().expand(source) == source


def test_no_path_resolver_returns_source_unchanged():
    expander = LrfUpdateExpander(path_resolver=None)
    source = (
        "       PROCEDURE DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    assert expander.expand(source) == source


# ----------------------------------------------------------- safe scope
def test_data_division_lines_are_never_touched():
    source = (
        "       DATA DIVISION.\n"
        "           MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    out = _expander().expand(source)
    assert "MODIFY VMBEFF." not in _executable(out)


def test_comment_lines_are_never_expanded():
    source = (
        "       PROCEDURE DIVISION.\n"
        "      *    MODIFY VMBTL07-R01 WHERE MO-VMBEFF.\n"
    )
    out = _expander().expand(source)
    assert "MODIFY VMBEFF" not in _executable(out)

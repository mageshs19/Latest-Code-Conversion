from idms_db2_phase2.postprocess.copybook_reference_renamer import (
    CopybookReferenceRenamer,
)


def _fixed(body: str, seq: str = "000750") -> str:
    # 6-digit sequence, space indicator, body in area A/B, trailing seq.
    return f"{seq} {body[:65].ljust(65)} 00750000"


def _comment(body: str, seq: str = "000260") -> str:
    # Column 7 = '*' comment indicator.
    return f"{seq}*{body[:65].ljust(65)} 00260000"


def test_bd_copybook_and_references_renamed():
    block = "\n".join([
        _fixed("COPY VMBD205I."),
        _fixed("INITIALIZE VMBD205I."),
        _fixed("READ OPERATIES INTO VMBD205I"),
        _fixed("MOVE NR-ID-FORM-AS OF VMBD205I"),
    ])
    out = CopybookReferenceRenamer().apply(block)
    assert "VMBD205I" not in out
    assert "COPY VMDZ205I" in out
    assert "INITIALIZE VMDZ205I" in out
    assert "INTO VMDZ205I" in out
    assert "OF VMDZ205I" in out


def test_bz_copybook_and_rec_reference_renamed():
    block = "\n".join([
        _fixed("COPY VMBZ270I."),
        _fixed("READ DAARCH INTO VMBZ270I-REC"),
        _fixed("MOVE DA-ARCH-YMD OF VMBZ270I-REC TO DA-CCYYMMDD"),
    ])
    out = CopybookReferenceRenamer().apply(block)
    assert "VMBZ270I" not in out
    assert "COPY VMDZ270I" in out
    # The hyphen-qualified record name is renamed, keeping its -REC suffix.
    assert "INTO VMDZ270I-REC" in out
    assert "OF VMDZ270I-REC" in out


def test_comment_lines_are_preserved():
    block = "\n".join([
        _comment("DAISY SECURITIES KASBONS : VMBD510X --> VMBD205I"),
        _fixed("COPY VMBD205I."),
    ])
    out = CopybookReferenceRenamer().apply(block)
    # The historical REMARKS comment keeps the original name verbatim.
    assert "VMBD205I" in out.splitlines()[0]
    # The executable COPY is renamed.
    assert "COPY VMDZ205I" in out


def test_non_derivable_copybooks_untouched():
    block = "\n".join([
        _fixed("COPY ESDATMAS."),
        _fixed("COPY IDMS SUBSCHEMA-CTRL."),
        _fixed("COPY IDMS LR VMBTL03-R01."),
    ])
    out = CopybookReferenceRenamer().apply(block)
    assert out == block


def test_line_lengths_are_preserved():
    # The derived name is the same length as the source, so every column -
    # including the sequence area - must stay byte-aligned.
    block = "\n".join([
        _fixed("COPY VMBZ270I."),
        _fixed("READ DAARCH INTO VMBZ270I-REC"),
    ])
    out = CopybookReferenceRenamer().apply(block)
    for before, after in zip(block.split("\n"), out.split("\n")):
        assert len(before) == len(after)


def test_duplicate_copy_is_deduplicated():
    block = "\n".join([
        _fixed("COPY VMBD205I.", seq="000750"),
        _fixed("COPY VMDZ205I.", seq="001680"),
    ])
    out = CopybookReferenceRenamer().apply(block)
    # Renaming the first COPY to VMDZ205I would duplicate it; keep only one.
    assert out.upper().count("COPY VMDZ205I") == 1


def test_no_copybook_returns_text_unchanged():
    block = _fixed("MOVE A TO B.")
    assert CopybookReferenceRenamer().apply(block) == block


def test_empty_text_is_safe():
    assert CopybookReferenceRenamer().apply("") == ""
    assert CopybookReferenceRenamer().apply(None) == ""


def test_idms_restart_table_ffrecab_stays_unchanged():
    # FFRECAB is IDMS-only, used with OBTAIN/STORE/MODIFY (not DB2 SQL).
    # It should stay as FFRECAB, not renamed to a DB2 DCLGEN.
    block = "\n".join([
        _fixed("MOVE 'VM1BDF567-A' TO NM-ID-FF OF FFRECAB."),
        _fixed("MOVE DATE-YMD8 TO DA-CR-FF OF FFRECAB."),
        _fixed("OBTAIN CALC FFRECAB."),
        _fixed("STORE FFRECAB."),
        _fixed("MODIFY FFRECAB."),
    ])
    out = CopybookReferenceRenamer().apply(block)
    # FFRECAB should remain unchanged (not copied, not DB2 SQL).
    assert out == block


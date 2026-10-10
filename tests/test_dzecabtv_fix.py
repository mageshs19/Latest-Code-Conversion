"""Test that FFRECAB (restart table) is filtered from DCLGEN dependency resolution.

Background:
  VM1BD526 and VM1BD567 perform OBTAIN on FFRECAB (a control record for restart
  state management). The resolver was blindly generating DZECABTV as a DCLGEN
  dependency for this record. However:
  
  1. FFRECAB is not a data table; it's a restart control structure
  2. The converted programs use DZ01RSTV (standard restart table infrastructure)
  3. DZECABTV was never found in the fetch phase (warning spam)
  4. Manual team outputs never reference DZECABTV (it's unnecessary)
  
Solution:
  Filter FFRECAB from the _NOT_A_RECORD set so it never generates a DCLGEN.
  This matches the manual team behavior and eliminates wasteful fetch attempts.

Testing:
  Verify that OBTAIN FFRECAB does NOT produce DZECABTV in the DCLGEN list.
"""

import pytest

from zowe.zowe_resolver import resolve_dependencies


class TestFfrecabFiltering:
    """FFRECAB should be filtered from DCLGEN dependency resolution."""

    def test_ffrecab_not_generates_dclgen_when_sole_record(self):
        """OBTAIN FFRECAB alone should produce no DCLGENs."""
        source = "020000     OBTAIN FFRECAB WITHIN WS-RUN RECORD."
        deps = resolve_dependencies("TEST_PROG", source)
        
        assert "FFRECAB" not in deps.records, "FFRECAB should be filtered"
        assert len(deps.dclgens) == 0, "No DCLGENs should be generated"

    def test_ffrecab_filtered_alongside_data_records(self):
        """OBTAIN FFRECAB + data records: only data records generate DCLGENs."""
        source = """
        020000     OBTAIN FFRECAB WITHIN WS-RUN RECORD.
        030000     STORE VMBEVEF.
        040000     MODIFY VMBTL07-R01.
        """
        deps = resolve_dependencies("TEST_PROG", source)
        
        assert "FFRECAB" not in deps.records, "FFRECAB should be filtered"
        assert "VMBEVEF" in deps.records, "VMBEVEF should be included"
        assert "VMBTL07-R01" in deps.records, "VMBTL07-R01 should be included"
        assert "DZECABTV" not in deps.dclgens, "DZECABTV should not be generated"
        assert "DZEVEFTV" in deps.dclgens, "DZEVEFTV should be generated for VMBEVEF"
        assert "DZTL07TV" in deps.dclgens, "DZTL07TV should be generated for VMBTL07"

    def test_vm1bd526_real_source(self):
        """Verify actual VM1BD526 source no longer generates DZECABTV."""
        # Simplified excerpt from VM1BD526.cbl
        source = """
        005000     COPY VMBD205I.
        020000     OBTAIN FFRECAB WITHIN WS-RUN RECORD.
        030000     STORE VMBEVEF.
        040000     MODIFY VMBTL07-R01.
        """
        deps = resolve_dependencies("VM1BD526", source)
        
        # DZECABTV should NOT be in the list anymore
        dzecabtv_present = any("ECABTV" in dclgen for dclgen in deps.dclgens)
        assert not dzecabtv_present, (
            f"DZECABTV should be filtered (got: {deps.dclgens})"
        )
        
        # Expected DCLGENs: only the data records
        expected = {"DZEVEFTV", "DZTL07TV"}
        actual = set(deps.dclgens)
        assert actual == expected, (
            f"Expected {expected}, got {actual}"
        )

    def test_vm1bd567_real_source(self):
        """Verify actual VM1BD567 source no longer generates DZECABTV."""
        # Simplified excerpt from VM1BD567.cbl
        source = """
        008200 COPY VMBD205I.
        020000     OBTAIN FFRECAB WITHIN WS-RUN RECORD.
        030000     STORE VMBFAR.
        """
        deps = resolve_dependencies("VM1BD567", source)
        
        # DZECABTV should NOT be in the list anymore
        dzecabtv_present = any("ECABTV" in dclgen for dclgen in deps.dclgens)
        assert not dzecabtv_present, (
            f"DZECABTV should be filtered (got: {deps.dclgens})"
        )
        
        # Expected DCLGENs: only DZBFARTV
        expected = {"DZBFARTV"}
        actual = set(deps.dclgens)
        assert actual == expected, (
            f"Expected {expected}, got {actual}"
        )

    def test_manifest_no_longer_lists_dzecabtv(self):
        """End-to-end: VM1BD526 and VM1BD567 should not reference DZECABTV."""
        # This is more of an integration test that would run after pipeline fetch
        # For now, we verify the resolver behavior which drives the manifest
        
        vm1bd526 = "020000     OBTAIN FFRECAB WITHIN WS. 030000 STORE VMBEVEF."
        vm1bd567 = "020000     OBTAIN FFRECAB WITHIN WS. 030000 STORE VMBFAR."
        
        deps1 = resolve_dependencies("VM1BD526", vm1bd526)
        deps2 = resolve_dependencies("VM1BD567", vm1bd567)
        
        # Neither should generate DZECABTV
        assert "DZECABTV" not in deps1.dclgens
        assert "DZECABTV" not in deps2.dclgens
        
        # Manifest will no longer warn "DZECABTV was not found"
        # because it will never try to fetch it in the first place

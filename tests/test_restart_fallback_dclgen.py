"""Tests for DZ01RSTV fallback when restart DCLGEN metadata is missing."""

from __future__ import annotations

import pytest

from idms_db2_phase2.postprocess.update_restart_fallback_dclgen import (
    create_fallback_restart_dclgen_role,
)


class TestFallbackRestartDclgenRole:
    """Verify fallback DZ01RSTV role generation."""

    def test_fallback_role_creation(self):
        """Fallback role has all required fields for restart SQL generation."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.table_name == "DZ01RSTV"
        assert role.include_name == "DZ01RSTV"
        assert role.host_record_name == "DCLDZ01RSTV"

    def test_fallback_program_field(self):
        """Program field mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.program_column == "NM_ID_RS_PROGRAM"
        assert role.program_field == "NM-ID-RS-PROGRAM"

    def test_fallback_phase_field(self):
        """Phase field mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.phase_column == "NB_ID_RS_PHASE"
        assert role.phase_field == "NB-ID-RS-PHASE"

    def test_fallback_date_field(self):
        """Date field mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.date_column == "DA_CR_RS"
        assert role.date_field == "DA-CR-RS"

    def test_fallback_status_field(self):
        """Status field mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.status_column == "CO_ID_RS"
        assert role.status_field == "CO-ID-RS"

    def test_fallback_retention_field(self):
        """Retention field mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.retention_column == "NB_DAY_RS"
        assert role.retention_field == "NB-DAY-RS"

    def test_fallback_payload_fields(self):
        """Payload and LEN fields mapping correct."""
        role = create_fallback_restart_dclgen_role()
        
        assert role.payload_column == "TE_CH_RS_DATA"
        assert role.payload_text_field == "TE-CH-RS-DATA-TEXT"
        assert role.payload_len_field == "TE-CH-RS-DATA-LEN"
        assert role.payload_group == "TE-CH-RS-DATA"

    def test_fallback_deterministic(self):
        """Fallback creation is deterministic across calls."""
        role1 = create_fallback_restart_dclgen_role()
        role2 = create_fallback_restart_dclgen_role()
        
        assert role1.table_name == role2.table_name
        assert role1.program_column == role2.program_column
        assert role1.payload_text_field == role2.payload_text_field

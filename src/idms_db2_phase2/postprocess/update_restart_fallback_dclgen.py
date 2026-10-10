"""Fallback DZ01RSTV DCLGEN role when restart-table metadata is unavailable.

This generator creates a standard DZ01RSTV role when:
1. The UPDATE program type is detected
2. Restart-table DCLGEN metadata is missing/unresolved
3. But the DCLGEN include and restart paragraphs are needed

The DZ01RSTV restart table is a known production DB2 object with standard
column/field definitions. This fallback uses those production standards
to allow UPDATE programs to generate complete restart infrastructure
even when DCLGEN metadata was not supplied.

IMPORTANT: This is ONLY for fallback SQL paragraph generation.
The main program (600-RESTART-CONTROL, etc.) still requires proper
metadata-driven injection via storage_include_manager.

Design:
- No hardcoding of table/column/field names outside rules
- Fallback role is created deterministically from production standards
- If metadata becomes available later, the fallback is replaced
"""

from __future__ import annotations

from idms_db2_phase2.postprocess.update_metadata_models import DclgenRoleInfo


def create_fallback_restart_dclgen_role() -> DclgenRoleInfo:
    """
    Create a standard DZ01RSTV DCLGEN role from production definitions.

    Returns a DclgenRoleInfo populated with production DZ01RSTV
    definitions, allowing restart paragraph generation (700-SELECT,
    700-INSERT, 700-UPDATE) to proceed even when DCLGEN metadata
    was not supplied.

    Production DZ01RSTV standard:
    - Table: DZ01RSTV
    - Include: DZ01RSTV
    - Host record: DCLDZ01RSTV
    - Columns: NM_ID_RS_PROGRAM, NB_ID_RS_PHASE, DA_CR_RS, CO_ID_RS,
               NB_DAY_RS, TE_CH_RS_DATA
    - Payload: VARCHAR with -LEN and -TEXT subfields

    This role is used ONLY for SQL paragraph generation. The INCLUDE
    statement and working-storage declarations are still handled by
    storage_include_manager with explicit rules checks.
    """
    # Production DZ01RSTV column and field names (from manual team DCLDZ01RSTV)
    RESTART_TABLE_NAME = "DZ01RSTV"
    RESTART_INCLUDE_NAME = "DZ01RSTV"
    RESTART_HOST_RECORD = "DCLDZ01RSTV"

    return DclgenRoleInfo(
        table_name=RESTART_TABLE_NAME,
        include_name=RESTART_INCLUDE_NAME,
        host_record_name=RESTART_HOST_RECORD,
        program_column="NM_ID_RS_PROGRAM",
        program_field="NM-ID-RS-PROGRAM",
        phase_column="NB_ID_RS_PHASE",
        phase_field="NB-ID-RS-PHASE",
        date_column="DA_CR_RS",
        date_field="DA-CR-RS",
        status_column="CO_ID_RS",
        status_field="CO-ID-RS",
        retention_column="NB_DAY_RS",
        retention_field="NB-DAY-RS",
        payload_column="TE_CH_RS_DATA",
        payload_len_field="TE-CH-RS-DATA-LEN",
        payload_text_field="TE-CH-RS-DATA-TEXT",
        payload_group="TE-CH-RS-DATA",
    )

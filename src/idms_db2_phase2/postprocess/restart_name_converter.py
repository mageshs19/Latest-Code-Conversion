"""
Sheet mapping to COBOL name converter for restart logic.

This module handles the critical conversion pattern:
  Sheet Mapping (TB suffix) → COBOL DCLGEN (TV suffix)

Example: VMDZ1567 updating DZBFARTV with restart on DZ01RSTV
  Sheet Name: "DZBFAR_TB" (update table with restart support)
  COBOL DCL: "DCLDZBFARTV" (column and data structure)
  Restart Table: "DZ01RSTV" (checkpoint storage)

This converter NEVER affects retrieval logic or other unrelated tables.
It only applies to the business update table when restart is enabled.
"""

from __future__ import annotations

import re
from typing import Optional


class RestartNameConverter:
    """
    Convert between sheet mapping names and COBOL DCL names.
    
    Conventions:
    1. Sheet mapping uses _TB suffix (table base / with backup)
    2. COBOL DCLGEN uses _TV suffix (table variable / DCLGEN structure)
    3. Business update tables: [NAME]_TB ↔ [NAME]TV (with DCL prefix)
    4. Restart tables: DZ01RSTV (no conversion, standard naming)
    
    Important:
    - This converter is for the BUSINESS table (what gets updated)
    - The RESTART table is separate and does NOT use this converter
    - Retrieval tables are not affected
    """
    
    # Standard restart table - never converted
    STANDARD_RESTART_TABLES = {
        "DZ01RSTV",  # Standard restart checkpoint table
        "FFRECAB",   # Legacy restart control area
    }
    
    # Common prefixes for DCL names (always prepended if not present)
    DCL_PREFIX = "DCL"
    
    @staticmethod
    def is_restart_table(name: str) -> bool:
        """Check if name refers to a restart/checkpoint table."""
        return name in RestartNameConverter.STANDARD_RESTART_TABLES
    
    @staticmethod
    def sheet_to_dclgen(sheet_name: str) -> str:
        """
        Convert sheet mapping name (with _TB suffix) to COBOL DCLGEN name (with TV suffix).
        
        Examples:
            "DZBFAR_TB" → "DCLDZBFARTV"
            "VMBEVEF_TB" → "VMBEVEFTV" (if already has DCL prefix)
            "DZ01RSTV" → "DCLDZ01RSTV" (standard restart table)
            "SOMETHING_TB" → "DCL{SOMETHING}TV"
        
        Args:
            sheet_name: Name from sheet mapping (may have _TB suffix)
        
        Returns:
            COBOL DCLGEN name with TV suffix
        """
        if not sheet_name:
            return ""
        
        # If it's a standard restart table, always add DCL prefix
        if RestartNameConverter.is_restart_table(sheet_name):
            if not sheet_name.startswith(RestartNameConverter.DCL_PREFIX):
                return RestartNameConverter.DCL_PREFIX + sheet_name
            return sheet_name
        
        # Remove _TB suffix if present
        if sheet_name.endswith("_TB"):
            base_name = sheet_name[:-3]  # Remove "_TB"
        else:
            base_name = sheet_name
        
        # Build DCLGEN name with TV suffix and DCL prefix
        cobol_name = base_name + "TV"
        
        if not cobol_name.startswith(RestartNameConverter.DCL_PREFIX):
            cobol_name = RestartNameConverter.DCL_PREFIX + cobol_name
        
        return cobol_name
    
    @staticmethod
    def dclgen_to_sheet(dclgen_name: str) -> str:
        """
        Reverse conversion: COBOL DCLGEN name → sheet mapping name.
        
        Examples:
            "DCLDZBFARTV" → "DZBFAR_TB"
            "DCLDZ01RSTV" → "DZ01RSTV" (standard restart)
            "VMBEVEFTV" → "VMBEVEF_TB"
        
        Args:
            dclgen_name: COBOL DCLGEN name (with TV suffix)
        
        Returns:
            Sheet mapping name with _TB suffix
        """
        if not dclgen_name:
            return ""
        
        # Remove DCL prefix if present
        if dclgen_name.startswith(RestartNameConverter.DCL_PREFIX):
            name = dclgen_name[len(RestartNameConverter.DCL_PREFIX):]
        else:
            name = dclgen_name
        
        # Check if this is a standard restart table
        if RestartNameConverter.is_restart_table(name):
            return name  # Return as-is, no _TB suffix
        
        # Remove TV suffix and add _TB suffix
        if name.endswith("TV"):
            base_name = name[:-2]  # Remove "TV"
            return base_name + "_TB"
        
        return name + "_TB"  # Fallback: add _TB if no TV suffix
    
    @staticmethod
    def extract_base_name(dclgen_or_sheet: str) -> str:
        """
        Extract base name regardless of DCL prefix or suffix.
        
        Examples:
            "DCLDZBFARTV" → "DZBFAR"
            "DZBFAR_TB" → "DZBFAR"
            "DZ01RSTV" → "DZ01RSTV" (standard restart, no change)
        """
        name = dclgen_or_sheet
        
        # Remove DCL prefix
        if name.startswith(RestartNameConverter.DCL_PREFIX):
            name = name[len(RestartNameConverter.DCL_PREFIX):]
        
        # Remove TV suffix
        if name.endswith("TV"):
            name = name[:-2]
        
        # Remove _TB suffix
        if name.endswith("_TB"):
            name = name[:-3]
        
        return name
    
    @staticmethod
    def is_business_table_with_restart(sheet_name: str) -> bool:
        """
        Check if this is a business table (not restart, not retrieval-only).
        
        Business tables with restart support end in _TB in sheet mapping.
        
        Examples:
            "DZBFAR_TB" → True (update table with restart support)
            "DZ01RSTV" → False (restart table, not a business table)
            "SOME_TABLE" → False (retrieval-only, no _TB suffix)
        """
        return (
            sheet_name.endswith("_TB")
            and not RestartNameConverter.is_restart_table(
                RestartNameConverter.extract_base_name(sheet_name)
            )
        )
    
    @staticmethod
    def validate_conversion(sheet_name: str, dclgen_name: str) -> bool:
        """
        Validate that sheet name and DCLGEN name are consistent conversions.
        
        Examples:
            validate_conversion("DZBFAR_TB", "DCLDZBFARTV") → True
            validate_conversion("DZBFAR_TB", "DCLDZBFAR") → False (missing TV)
            validate_conversion("DZ01RSTV", "DCLDZ01RSTV") → True
        """
        return RestartNameConverter.sheet_to_dclgen(sheet_name) == dclgen_name
    
    @staticmethod
    def suggest_conversion(partial_name: str) -> tuple[str, str]:
        """
        Given a partial name, suggest both sheet and DCLGEN names.
        
        Examples:
            suggest_conversion("DZBFAR") → ("DZBFAR_TB", "DCLDZBFARTV")
            suggest_conversion("DZ01RSTV") → ("DZ01RSTV", "DCLDZ01RSTV")
        
        Useful for: Code review, documentation, setup instructions.
        """
        sheet = (
            partial_name
            if RestartNameConverter.is_restart_table(partial_name)
            else partial_name + "_TB"
        )
        dclgen = RestartNameConverter.sheet_to_dclgen(sheet)
        return sheet, dclgen


class RestartFieldConverter:
    """
    Convert between sheet mapping column names and COBOL DCL field names
    for restart checkpoint fields.
    
    Restart table columns follow a naming pattern based on roles:
    - Program ID: NM_ID_RS_PROGRAM (role tokens: ["NM", "ID", "RS", "PROGRAM"])
    - Phase: NB_ID_RS_PHASE (role tokens: ["NB", "ID", "RS", "PHASE"])
    - Date: DA_CR_RS (role tokens: ["DA", "CR", "RS"])
    - Status: CO_ID_RS (role tokens: ["CO", "ID", "RS"])
    - Retention: NB_DAY_RS (role tokens: ["NB", "DAY", "RS"])
    - Payload: TE_CH_RS_DATA (role tokens: ["TE", "CH", "RS", "DATA"])
    """
    
    # Role-based token patterns (from rules/update_restart_rules.py)
    ROLE_TOKEN_PATTERNS = {
        "program": ["NM", "ID", "RS", "PROGRAM"],
        "program_fallback": ["PROGRAM"],
        "phase": ["NB", "ID", "RS", "PHASE"],
        "phase_fallback": ["PHASE"],
        "date": ["DA", "CR", "RS"],
        "date_fallback": ["DATE"],
        "status": ["CO", "ID", "RS"],
        "status_fallback": ["STATUS"],
        "retention": ["NB", "DAY", "RS"],
        "retention_fallback": ["DAY"],
        "payload": ["TE", "CH", "RS", "DATA"],
        "payload_fallback": ["DATA"],
    }
    
    @staticmethod
    def sql_to_cobol_field(sql_column: str) -> str:
        """
        Convert SQL column name to COBOL field name (replace _ with -).
        
        Examples:
            "NM_ID_RS_PROGRAM" → "NM-ID-RS-PROGRAM"
            "TE_CH_RS_DATA" → "TE-CH-RS-DATA"
        """
        return sql_column.replace("_", "-")
    
    @staticmethod
    def cobol_to_sql_field(cobol_field: str) -> str:
        """
        Convert COBOL field name to SQL column name (replace - with _).
        
        Examples:
            "NM-ID-RS-PROGRAM" → "NM_ID_RS_PROGRAM"
            "TE-CH-RS-DATA" → "TE_CH_RS_DATA"
        """
        return cobol_field.replace("-", "_")
    
    @staticmethod
    def get_role_for_tokens(tokens: list[str]) -> Optional[str]:
        """
        Given a list of tokens, find matching role.
        
        Examples:
            ["NM", "ID", "RS", "PROGRAM"] → "program"
            ["TE", "CH", "RS", "DATA"] → "payload"
        """
        for role, pattern in RestartFieldConverter.ROLE_TOKEN_PATTERNS.items():
            if all(token.upper() in [t.upper() for t in pattern] for token in tokens):
                return role
        return None

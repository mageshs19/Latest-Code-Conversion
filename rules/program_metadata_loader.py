# LOCATION: rules/program_metadata_loader.py
"""Load program metadata (AUTHOR, DATE-WRITTEN) from configuration file.

Reads rules/program_metadata_config.txt and provides configured values
for generated COBOL programs.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


class ProgramMetadataLoader:
    """Loads AUTHOR and DATE-WRITTEN configuration from file."""

    CONFIG_FILE = Path(__file__).parent / "program_metadata_config.txt"

    @classmethod
    def load_author(cls) -> str:
        """Load AUTHOR value from configuration file.
        
        Returns:
            str: Author name configured in program_metadata_config.txt
                 or empty string if not found.
        """
        return cls._get_config_value("AUTHOR", "")

    @classmethod
    def load_date_written(cls) -> str:
        """Load DATE-WRITTEN value from configuration file.
        
        Handles special values:
        - TODAY: Replaced with current date (YYYY-MM-DD)
        - CURRENT: Replaced with current date and time
        
        Returns:
            str: Date-written value, with TODAY/CURRENT expanded to actual dates.
        """
        value = cls._get_config_value("DATE_WRITTEN", "TODAY")
        
        if value.upper() == "TODAY":
            return datetime.now().strftime("%Y-%m-%d")
        elif value.upper() == "CURRENT":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            return value

    @classmethod
    def _get_config_value(cls, key: str, default: str = "") -> str:
        """Read a configuration value from the metadata config file.
        
        Args:
            key: Configuration key to read (e.g., "AUTHOR")
            default: Default value if key not found
            
        Returns:
            str: Configuration value or default
        """
        if not cls.CONFIG_FILE.exists():
            return default

        try:
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    # Remove comments and strip whitespace
                    line = line.split("#")[0].strip()
                    if not line or "=" not in line:
                        continue

                    config_key, config_value = line.split("=", 1)
                    config_key = config_key.strip()
                    config_value = config_value.strip()
                    
                    # Remove surrounding quotes if present (allows both quoted and unquoted values)
                    if (config_value.startswith('"') and config_value.endswith('"')) or \
                       (config_value.startswith("'") and config_value.endswith("'")):
                        config_value = config_value[1:-1]

                    if config_key == key:
                        return config_value

        except (IOError, OSError):
            pass

        return default

    @classmethod
    def reload(cls) -> None:
        """Reload configuration from file (clears any cached values).
        
        Useful when the configuration file is updated during runtime.
        """
        pass  # Currently no caching, so nothing to clear


# Module-level convenience functions
def get_author() -> str:
    """Get configured AUTHOR name."""
    return ProgramMetadataLoader.load_author()


def get_date_written() -> str:
    """Get configured DATE-WRITTEN value."""
    return ProgramMetadataLoader.load_date_written()


__all__ = [
    "ProgramMetadataLoader",
    "get_author",
    "get_date_written",
]

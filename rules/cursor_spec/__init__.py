# LOCATION: rules/cursor_spec/__init__.py
# ACTION: CREATE NEW FILE
"""Cursor specification rules."""

from rules.cursor_spec.cursor_spec_messages import SPEC_MESSAGES
from rules.cursor_spec.cursor_spec_rules import *  # noqa: F401,F403
from rules.cursor_spec.cursor_spec_rules import __all__ as _RULES_ALL

__all__ = [*_RULES_ALL, "SPEC_MESSAGES"]
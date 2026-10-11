# LOCATION: converter/composers/restart/__init__.py
# ACTION: CREATE NEW FILE
"""Restart composers.

A composer MUTATES generated COBOL. A generator RENDERS it. The split
matters: a generator can be tested against its templates alone, while a
composer has to be tested against real source shapes.
"""

from __future__ import annotations

__all__: list[str] = []
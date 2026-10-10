# LOCATION: converter/composers/counter_declaration/__init__.py
# ACTION: CREATE NEW FILE
"""Placement and rendering helpers for generated row counters.

CounterDeclarationComposer decides WHAT to declare.
This package decides WHERE it goes and HOW it is rendered.
"""

from converter.composers.counter_declaration.counter_anchor import (
    CounterAnchor,
    CounterAnchorFinder,
)
from converter.composers.counter_declaration.counter_anchor_resolver import (
    CounterAnchorResolver,
)
from converter.composers.counter_declaration.counter_line_factory import (
    CounterLineFactory,
)
from converter.composers.counter_declaration.counter_totals_writer import (
    CounterTotalsWriter,
)

__all__ = [
    "CounterAnchor",
    "CounterAnchorFinder",
    "CounterAnchorResolver",
    "CounterLineFactory",
    "CounterTotalsWriter",
]
from __future__ import annotations

import re

from rules.timestamp_audit_rules import (
    TIMESTAMP_DEFAULT_PROGRAM_ID,
    TIMESTAMP_PROGRAM_ID_LENGTH,
)

PROGRAM_ID_PATTERN = re.compile(
    r"^PROGRAM-ID\s*\.\s*(?P<name>[A-Z0-9-]+)",
    flags=re.IGNORECASE,
)


class ProgramIdResolver:

    def resolve(self, target_program_id: str) -> str:
        program_id = str(target_program_id or "").strip().upper()
        if not program_id:
            program_id = TIMESTAMP_DEFAULT_PROGRAM_ID
        return program_id[:TIMESTAMP_PROGRAM_ID_LENGTH]

    def from_source(self, bodies: list[str]) -> str:
        for body in bodies or []:
            match = PROGRAM_ID_PATTERN.match(str(body or "").strip())
            if match:
                return match.group("name").upper()
        return ""

    def resolve_with_fallback(
        self,
        target_program_id: str,
        bodies: list[str],
    ) -> str:
        explicit = str(target_program_id or "").strip()
        if explicit:
            return self.resolve(explicit)
        return self.resolve(self.from_source(bodies))

    def padded(self, program_id: str) -> str:
        return self.resolve(program_id).ljust(TIMESTAMP_PROGRAM_ID_LENGTH)


__all__ = ["ProgramIdResolver", "PROGRAM_ID_PATTERN"]
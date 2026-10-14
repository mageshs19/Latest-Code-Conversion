# LOCATION: converter/services/program_name_sync_service.py
# ACTION: REPLACE ENTIRE FILE
"""Program name synchronization service.

Generic behavior:
- Read final PROGRAM-ID.
- Rewrite only safe MOVE literal TO PROGRAM-NAME statements.
- Derive any VM..BD.. program id found INSIDE a quoted literal.
- Do not globally replace program names.

CORRECTION - the source id survived inside a DISPLAY literal
--------------------------------------------------------------
sync() rewrote MOVE literal TO PROGRAM-NAME and nothing else, so

    DISPLAY 'VM7BD200: ** DATE ARCHIVAGE NOT OK **'

kept the SOURCE id on the abend path - the one message an operator
reads when the job fails. PROGRAM-ID said VMDZ7200; the job log said
VM7BD200, a program that no longer exists. This is CORRECTION 2 of
cobol_transformer.py in a second disguise.

WHY THIS IS SAFE
------------------
1. The rewrite is scoped to text INSIDE single quotes, so a data name,
   a paragraph name and a picture clause can never be touched.

2. The transform is NOT implemented here. Every candidate token is
   handed to NameDerivationResolver, the single owner of the
   VM<site>?BD<tail> -> VMDZ<site><tail> rule. A token that does not
   match the shape comes back unchanged.

3. The derived name is ALWAYS the same length as the source name -
   VM + site + BD + tail  ->  VM + DZ + site + tail - so no literal can
   grow and no line can overflow column 72. That is why this pass needs
   no fixed-format geometry and cannot disturb columns 73-80.

4. Every rewrite is reported. A silent rename cannot be reviewed.

No program name is hardcoded.
"""

from __future__ import annotations

from converter.services.name_derivation_resolver import (
    NameDerivationResolver,
)
from patterns.final_feedback_fix_patterns import (
    COBOL_LITERAL_PATTERN,
    MOVE_TO_PROGRAM_NAME_PATTERN,
    PROGRAM_ID_PATTERN,
    VM_BD_TOKEN_PATTERN,
)


class ProgramNameSyncService:
    """Synchronizes PROGRAM-NAME and embedded ids from final PROGRAM-ID."""

    def __init__(
        self,
        name_derivation_resolver: NameDerivationResolver | None = None,
    ) -> None:
        # Injected, not constructed inline, so the one owner of the
        # derivation rule can be substituted in a test.
        self._resolver = name_derivation_resolver or NameDerivationResolver()
        self.messages: list[str] = []

    def reset(self) -> None:
        """Drop diagnostics from the previous program."""
        self.messages = []

    # =================================================================
    # Public surface
    # =================================================================
    def sync(self, text: str) -> str:
        """Rewrite MOVE literal TO PROGRAM-NAME, then embedded ids."""
        source = str(text or "")

        program_match = PROGRAM_ID_PATTERN.search(source)
        if not program_match:
            self.messages.append(
                "PROGRAM-NAME sync: no PROGRAM-ID found; text unchanged."
            )
            return source

        final_program_id = program_match.group("program").upper()

        def replace_program_name(match) -> str:
            return (
                match.group("prefix")
                + final_program_id
                + match.group("suffix")
            )

        updated, moves = MOVE_TO_PROGRAM_NAME_PATTERN.subn(
            replace_program_name, source
        )

        if moves:
            self.messages.append(
                f"PROGRAM-NAME sync: set {moves} MOVE statement(s) to "
                f"{final_program_id}."
            )

        return self.sync_literals(updated)

    def sync_literals(self, text: str) -> str:
        """Derive any VM..BD.. program id embedded in a COBOL literal.

        Length preserving by construction - see WHY THIS IS SAFE (3) -
        so the result needs no re-layout and no resequencing.
        """
        source = str(text or "")
        if "'" not in source:
            return source

        rewritten: list[str] = []

        def _derive_inside(literal_match) -> str:
            def _derive_token(token_match) -> str:
                token = token_match.group(0)
                derived = self._resolver.derive(token)
                if derived.upper() != token.upper():
                    rewritten.append(f"{token} -> {derived}")
                return derived

            return VM_BD_TOKEN_PATTERN.sub(
                _derive_token, literal_match.group(0)
            )

        updated = COBOL_LITERAL_PATTERN.sub(_derive_inside, source)

        if rewritten:
            self.messages.append(
                "PROGRAM-NAME sync: derived "
                f"{len(rewritten)} program id(s) inside literal(s): "
                + "; ".join(sorted(set(rewritten)))
            )

        return updated


__all__ = [
    "ProgramNameSyncService",
]
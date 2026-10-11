# LOCATION: converter/resolvers/restart_context_builder.py
# ACTION: CREATE NEW FILE
"""Builds the run-scoped context the restart pass needs.

    build(...) -> (RestartRunContext | None, messages)

WHAT DECIDES THAT A PROGRAM RESTARTS

Not "it contains STORE / MODIFY / ERASE" - that is true of every update
program whether it ever restarted or not. The signal is that the SOURCE
maintains an IDMS checkpoint record:

    STORE FFRECAB  /  FIND CURRENT FFRECAB  /  MODIFY FFRECAB

DZ01RSTV is the DB2 replacement for that record. The record NAMES are
site vocabulary and live in catalogs/restart_trigger_catalog.py; this
module owns only the matching.

THE DCLGEN RESOLVER IS INJECTED

Its import path is a fact to be read, not inferred, and a collaborator
missing its method must fail at CONSTRUCTION naming the method - not
three passes later with an AttributeError.

REFUSAL IS THE NORMAL CASE

A retrieval program, a program with no checkpoint record, no restart
DCLGEN or no retention value all return None WITH a reason. None of
those is an error; silence would be.
"""

from __future__ import annotations

from typing import Any

from catalogs.restart_site_catalog import RESTART_RETENTION_DAYS
from catalogs.restart_trigger_catalog import (
    CHECKPOINT_VERBS,
    LEGACY_CHECKPOINT_RECORDS,
)
from converter.composers.restart.restart_stage_adapter import (
    RestartRunContext,
)
from converter.composers.restart.restart_injection_composer import (
    PROGRAM_KIND_RETRIEVAL,
    PROGRAM_KIND_UPDATE,
)

MESSAGE_PREFIX = "Restart context:"
RESOLVER_METHOD = "resolve_restart_dclgen"


class RestartContextBuilder:
    """Turns conversion inputs into a RestartRunContext, or refuses."""

    def __init__(self, dclgen_resolver: Any = None) -> None:
        self.dclgen_resolver = dclgen_resolver
        self.messages: list[str] = []
        if dclgen_resolver is not None:
            self._verify(dclgen_resolver)

    #
    # Public surface
    #
    def build(
        self,
        *,
        source_text: str,
        dclgen_columns: Any = (),
        is_update: bool = False,
        retention_days: int = RESTART_RETENTION_DAYS,
    ) -> tuple[RestartRunContext | None, list[str]]:
        self.messages = []

        if not is_update:
            self._say("retrieval program; no restart context built.")
            return (
                RestartRunContext(program_kind=PROGRAM_KIND_RETRIEVAL),
                list(self.messages),
            )

        record = self._checkpoint_record(source_text)
        if not record:
            self._say(
                "the source maintains no checkpoint record; this update "
                "program is not a restart program."
            )
            return None, list(self.messages)

        self._say(f"checkpoint record {record} found in the source.")

        role = self._dclgen_role(dclgen_columns)
        if role is None:
            return None, list(self.messages)

        table = str(getattr(role, "table_name", "") or "").strip()
        context = RestartRunContext(
            program_kind=PROGRAM_KIND_UPDATE,
            record_name=record,
            table_hint=table,
            retention_days=int(retention_days or 0),
            dclgen_role=role,
            totals=(),
        )
        self._say(
            f"built for {table or 'an unnamed restart table'} with a "
            f"retention of {context.retention_days} day(s)."
        )
        return context, list(self.messages)

    #
    # Trigger detection
    #
    @staticmethod
    def _checkpoint_record(source_text: str) -> str:
        """The first checkpoint record the source ACTS on.

        A name in a comment is not a checkpoint; the record must appear
        with an IDMS verb.
        """
        text = " ".join(str(source_text or "").upper().split())
        for record in LEGACY_CHECKPOINT_RECORDS:
            name = str(record).upper()
            if any(f"{verb} {name}" in text for verb in CHECKPOINT_VERBS):
                return name
            if any(f"{verb} CURRENT {name}" in text for verb in CHECKPOINT_VERBS):
                return name
        return ""

    #
    # DCLGEN role
    #
    def _dclgen_role(self, dclgen_columns: Any) -> Any:
        if self.dclgen_resolver is None:
            self._say(
                "no restart DCLGEN resolver was supplied; the restart "
                "role cannot be built."
            )
            return None

        method = getattr(self.dclgen_resolver, RESOLVER_METHOD)
        role = method(list(dclgen_columns or []))
        if role is None:
            self._say(
                "the DCLGEN input declares no restart table; the restart "
                "role cannot be built."
            )
        return role

    #
    # Construction-time contract check
    #
    @staticmethod
    def _verify(resolver: Any) -> None:
        if not callable(getattr(resolver, RESOLVER_METHOD, None)):
            raise TypeError(
                "RestartContextBuilder needs a resolver exposing "
                f"{RESOLVER_METHOD}(); got {type(resolver).__name__}."
            )

    def _say(self, message: str) -> None:
        self.messages.append(f"{MESSAGE_PREFIX} {message}")


__all__ = ["MESSAGE_PREFIX", "RESOLVER_METHOD", "RestartContextBuilder"]
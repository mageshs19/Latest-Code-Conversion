"""Host-reference and SET/WHERE/comma line-builder mixin.

THREE FORMS OF ONE FACT

    _host_reference        ':DCLGROUP.FIELD'      inside EXEC SQL
    _host_reference_key     'DCLGROUP.FIELD'      a dictionary key
    _host_reference_cobol   'FIELD OF DCLGROUP'   inside a MOVE

CORRECTION - the third form did not exist.

bare_move_rewriter.py needed a COBOL reference and reached for
_host_reference_key, because the key is the only colon-free form and
therefore the only one that LOOKS usable outside SQL. It emitted a
lookup key as a data-name:

    MOVE DA-DD-MM-CCYY TO DCLDZBFARTV.DA-INFSDGD-479BFAR

which the compiler reads as a sentence terminator. The two forms differ
by one character, which is why the substitution looked harmless and
compiled nowhere.

A KEY IS NOT A REFERENCE. _host_reference_key is for lookup, dedupe and
comparison only; it must never reach generated text.
"""

from __future__ import annotations

from converter.services.host_reference_normalizer import (
    HostReferenceNormalizer,
)


class SqlLineMixin:
    #
    # The three forms
    #
    def _host_reference(
        self,
        table: str,
        column: str,
    ) -> str:
        """':DCLGROUP.FIELD' - the SQL form. For EXEC SQL bodies only."""
        return self.host_variable_resolver.host_reference_for_column(
            table_name=table,
            column_name=column,
        )

    def _host_reference_key(
        self,
        table: str,
        column: str,
    ) -> str:
        """'DCLGROUP.FIELD' - a LOOKUP KEY. Never emit this.

        Returned for dictionary keys, dedupe and comparison. It is not
        valid COBOL and not valid SQL. Use _host_reference_cobol to
        write a MOVE and _host_reference to write SQL.
        """
        if hasattr(self.host_variable_resolver, "host_reference_key"):
            return self.host_variable_resolver.host_reference_key(
                table_name=table,
                column_name=column,
            )

        reference = self._host_reference(table, column)

        if reference.startswith(":"):
            return reference[1:].strip()

        return reference

    def _host_reference_cobol(
        self,
        table: str,
        column: str,
    ) -> str:
        """'FIELD OF DCLGROUP' - the COBOL form. For a MOVE.

        Derived from _host_reference, NOT from _host_reference_key: the
        key path may be overridden by the resolver and carries no
        guarantee about shape. HostReferenceNormalizer is the one owner
        of this conversion; RecordHostResolver already used it and was
        correct, which is how the asymmetry was found.
        """
        return HostReferenceNormalizer.to_cobol(
            self._host_reference(table, column)
        )

    #
    # SQL clause builders - all use the SQL form
    #
    def _set_lines(
        self,
        table: str,
        columns: list[str],
        indent: str,
    ) -> list[str]:
        output: list[str] = []

        for index, column in enumerate(columns):
            host = self._host_reference(table, column)
            if not host:
                continue
            suffix = "," if index < len(columns) - 1 else ""
            output.append(f"{indent}{column} = {host}{suffix}")

        return output

    def _where_lines(
        self,
        table: str,
        columns: list[str],
        indent: str,
    ) -> list[str]:
        output: list[str] = []

        for index, column in enumerate(columns):
            host = self._host_reference(table, column)
            if not host:
                continue
            prefix = "" if index == 0 else "AND "
            output.append(f"{indent}{prefix}{column} = {host}")

        return output

    def _comma_lines(
        self,
        values: list[str],
        indent: str,
    ) -> list[str]:
        output: list[str] = []

        for index, value in enumerate(values):
            suffix = "," if index < len(values) - 1 else ""
            output.append(f"{indent}{value}{suffix}")

        return output


__all__ = ["SqlLineMixin"]
"""A MOVE target must be COBOL, never a lookup key.

    correct   MOVE DA-DD-MM-CCYY TO DA-INFSDGD-479BFAR OF DCLDZBFARTV
    emitted   MOVE DA-DD-MM-CCYY TO DCLDZBFARTV.DA-INFSDGD-479BFAR

The second is a dictionary key. It reached generated COBOL because
_host_reference_key was the only colon-free accessor and therefore the
only one that looked usable outside SQL.
"""

from __future__ import annotations

from converter.services.host_reference_normalizer import (
    HostReferenceNormalizer,
)

SQL_FORM = ":DCLDZBFARTV.DA-INFSDGD-479BFAR"
KEY_FORM = "DCLDZBFARTV.DA-INFSDGD-479BFAR"
COBOL_FORM = "DA-INFSDGD-479BFAR OF DCLDZBFARTV"


class _Resolver:
    def host_reference_for_column(self, table_name, column_name):
        return SQL_FORM


class _Owner:
    from converter.composers.update_sql_cleanup.sql_line_mixin import (
        SqlLineMixin,
    )

    host_variable_resolver = _Resolver()
    _host_reference = SqlLineMixin._host_reference
    _host_reference_key = SqlLineMixin._host_reference_key
    _host_reference_cobol = SqlLineMixin._host_reference_cobol


#
# The three forms are distinct
#
def test_the_sql_form_keeps_its_colon():
    assert _Owner()._host_reference("DZBFARTV", "DA_INFSDGD_479BFAR") == SQL_FORM


def test_the_key_form_is_not_cobol():
    key = _Owner()._host_reference_key("DZBFARTV", "DA_INFSDGD_479BFAR")
    assert key == KEY_FORM
    assert "." in key, "a key keeps the dot; that is why it must never be emitted"


def test_the_cobol_form_carries_no_dot():
    cobol = _Owner()._host_reference_cobol("DZBFARTV", "DA_INFSDGD_479BFAR")
    assert cobol == COBOL_FORM
    assert "." not in cobol
    assert " OF " in cobol


#
# The normaliser is total
#
def test_an_already_cobol_reference_is_unchanged():
    assert HostReferenceNormalizer.to_cobol(COBOL_FORM) == COBOL_FORM


def test_an_empty_reference_yields_empty():
    assert HostReferenceNormalizer.to_cobol("") == ""
    assert HostReferenceNormalizer.to_cobol(None) == ""


#
# A qualified continuation is refused, not half-rewritten
#
def test_a_target_qualified_on_the_next_line_is_refused():
    from converter.composers.update_sql_cleanup.bare_move_rewriter import (
        QUALIFIER_CONNECTORS,
    )

    assert "OF " in QUALIFIER_CONNECTORS
    assert "IN " in QUALIFIER_CONNECTORS
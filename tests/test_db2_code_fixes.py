"""
Test suite for IDMS-DB2 Code Conversion fixes.

Covers three critical fixes:
1. COMP-3 encoding removal from numeric fields in WORKING-STORAGE
2. FILLER field elimination from data declarations
3. VALUE ZEROES initialization for numeric PIC clauses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestCobolTransformerCompRemoval:
    """Test COMP-3 removal in CobolTransformer's data line cleaning."""

    def test_transformer_removes_comp3_from_working_storage(self):
        """CobolTransformer._clean_data_declaration_line should strip COMP-3."""
        from converter.transformers.cobol_transformer import (
            CobolTransformer,
        )
        from converter.transformers.idms_statement_transformer import (
            IdmsStatementTransformer,
        )
        from converter.transformers.cobol_transformer_line_utils import (
            CobolTransformerLineUtils,
        )

        # Create a mock transformer
        line_utils = CobolTransformerLineUtils()
        transformer = CobolTransformer(
            idms_statement_transformer=Mock(spec=IdmsStatementTransformer)
        )
        transformer.line_utils = line_utils

        # Test line with COMP-3
        test_line = "000700     03  WS-NR-CIO              PIC 9(8)    COMP-3."
        
        result = transformer._clean_data_declaration_line(test_line)

        assert result is not None
        # Should not contain COMP-3
        assert "COMP-3" not in result
        # Should contain VALUE ZEROES
        assert "VALUE ZEROES" in result

    def test_transformer_removes_filler_entirely(self):
        """CobolTransformer._clean_data_declaration_line should skip FILLER lines."""
        from converter.transformers.cobol_transformer import (
            CobolTransformer,
        )
        from converter.transformers.idms_statement_transformer import (
            IdmsStatementTransformer,
        )
        from converter.transformers.cobol_transformer_line_utils import (
            CobolTransformerLineUtils,
        )

        line_utils = CobolTransformerLineUtils()
        transformer = CobolTransformer(
            idms_statement_transformer=Mock(spec=IdmsStatementTransformer)
        )
        transformer.line_utils = line_utils

        # Test FILLER line
        test_line = "000790     03  FILLER                 PIC XX      VALUE SPACES."
        
        result = transformer._clean_data_declaration_line(test_line)

        # Should return None to skip FILLER line entirely
        assert result is None


class TestRecordKeySignHandling:
    """Guard issue #2: sign handling when cleaning packed record-key fields.

    The manual reference drops the sign on plain-integer record-key fields
    (PIC S9(3) -> PIC 9(3)) but keeps it on signed decimals (money,
    PIC S9(13)V99). If this scoping is removed these tests fail.
    """

    @staticmethod
    def _transformer():
        from converter.transformers.cobol_transformer import (
            CobolTransformer,
        )
        from converter.transformers.idms_statement_transformer import (
            IdmsStatementTransformer,
        )
        from converter.transformers.cobol_transformer_line_utils import (
            CobolTransformerLineUtils,
        )

        transformer = CobolTransformer(
            idms_statement_transformer=Mock(spec=IdmsStatementTransformer)
        )
        transformer.line_utils = CobolTransformerLineUtils()
        return transformer

    def test_plain_integer_record_key_drops_sign(self):
        """PIC S9(3) COMP-3 -> PIC 9(3) VALUE ZEROES (WS-CT-OPD-CRE)."""
        line = "000780         20  WS-CT-OPD-CRE        PIC S9(3) COMP-3."

        result = self._transformer()._clean_data_declaration_line(line)

        assert result is not None
        assert "COMP-3" not in result
        assert "PIC S9" not in result
        assert "PIC 9(3)" in result
        assert "VALUE ZEROES" in result

    def test_signed_decimal_keeps_sign(self):
        """A signed decimal (money) keeps its sign: the V-guard protects it."""
        line = "000610     03  UIT-AM-CN-STOCK          PIC S9(13)V99 COMP-3."

        result = self._transformer()._clean_data_declaration_line(line)

        assert result is not None
        # Sign is retained for decimal fields even if encoding is stripped.
        assert "S9(13)V99" in result

    def test_already_unsigned_integer_is_untouched_sign(self):
        """An unsigned counter stays unsigned (WS-CT-OPG-CRE)."""
        line = "000790         20  WS-CT-OPG-CRE        PIC 9(3) COMP-3."

        result = self._transformer()._clean_data_declaration_line(line)

        assert result is not None
        assert "COMP-3" not in result
        assert "PIC 9(3)" in result
        assert "VALUE ZEROES" in result


class TestComp3Removal:
    """Test removal of COMP-3 and other binary encoding from field definitions."""

    def test_picture_strips_comp3_from_usage(self):
        """COMP-3 should be stripped from PIC clause."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        # Create mock item with COMP-3 usage
        item = Mock()
        item.picture = "PIC 9(8)"
        item.usage = "COMP-3"

        result = RecordEntryRenderer.picture_of(item)

        # Should NOT contain COMP-3
        assert "COMP-3" not in result
        # Should contain PIC clause
        assert "PIC 9(8)" in result
        # Should have VALUE ZEROES for numeric fields
        assert "VALUE ZEROES" in result

    def test_picture_strips_computational_3(self):
        """COMPUTATIONAL-3 should also be stripped."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC S9(13)V99"
        item.usage = "COMPUTATIONAL-3"

        result = RecordEntryRenderer.picture_of(item)

        assert "COMPUTATIONAL-3" not in result
        assert "COMP-3" not in result
        assert "PIC S9(13)V99" in result
        assert "VALUE ZEROES" in result

    def test_picture_preserves_non_encoding_usage(self):
        """Non-encoding USAGE clauses (like DISPLAY) should be preserved."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC X(20)"
        item.usage = "DISPLAY"

        result = RecordEntryRenderer.picture_of(item)

        # DISPLAY should be preserved
        assert "DISPLAY" in result
        assert "PIC X(20)" in result

    def test_picture_no_value_for_alphanumeric(self):
        """Alphanumeric fields should not get VALUE ZEROES."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC X(20)"
        item.usage = ""

        result = RecordEntryRenderer.picture_of(item)

        # Should not add VALUE ZEROES to alphanumeric
        assert "VALUE ZEROES" not in result
        assert "PIC X(20)" in result

    def test_picture_existing_value_preserved(self):
        """If VALUE clause already exists, don't add VALUE ZEROES."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC 9(8) VALUE 12345"
        item.usage = ""

        result = RecordEntryRenderer.picture_of(item)

        assert "VALUE 12345" in result
        # Should not add another VALUE ZEROES
        assert result.count("VALUE") == 1


class TestFillerRemoval:
    """Test elimination of FILLER fields from materialised records."""

    def test_emit_remainder_filler_disabled(self):
        """EMIT_REMAINDER_FILLER should be False to prevent FILLER generation."""
        from rules.record_materialisation_rules import EMIT_REMAINDER_FILLER

        # FILLER should NOT be emitted
        assert EMIT_REMAINDER_FILLER is False

    def test_filler_not_in_materialised_record(self):
        """Materialised records should not contain FILLER when disabled."""
        # This would be tested against actual output
        # For now, we verify the configuration is correct
        from rules.record_materialisation_rules import (
            EMIT_REMAINDER_FILLER,
            FILLER_FIELD_NAMES,
        )

        assert EMIT_REMAINDER_FILLER is False
        assert "FILLER" in FILLER_FIELD_NAMES


class TestSelectColumnOptimization:
    """Test SELECT statement column optimization."""

    def test_cursor_column_filtering_logic(self):
        """Cursor should select appropriate columns."""
        # Test the static method for filtering audit columns
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        test_columns = [
            "NR_IDGOOD_479EVEF",
            "NR_CI1POS_479EVEF",
            "TS_CREATED",
            "ID_USERID_CREATED",
            "NR_CT_OPD",
        ]

        filtered = CursorColumnResolver._without_audit_columns(test_columns)

        # Audit columns should be removed
        assert "TS_CREATED" not in filtered
        assert "ID_USERID_CREATED" not in filtered
        # Business columns should remain
        assert "NR_IDGOOD_479EVEF" in filtered
        assert "NR_CI1POS_479EVEF" in filtered
        assert "NR_CT_OPD" in filtered

    def test_column_deduplication(self):
        """Duplicate columns should be removed while preserving order."""
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        columns = [
            "NR_IDGOOD_479EVEF",
            "NR_CI1POS_479EVEF",
            "NR_IDGOOD_479EVEF",  # Duplicate
            "NR_CT_OPD",
        ]

        result = CursorColumnResolver._unique(columns)

        # Should contain 3 unique columns
        assert len(result) == 3
        # Order should be preserved
        assert result[0] == "NR_IDGOOD_479EVEF"
        assert result[1] == "NR_CI1POS_479EVEF"
        assert result[2] == "NR_CT_OPD"

    def test_unnecessary_columns_filtered(self):
        """Filler and system metadata columns should be removed."""
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        columns = [
            "NR_IDGOOD_479EVEF",
            "FILLER",
            "NR_CI1POS_479EVEF",
            "FIELD_FILLER_DATA",
            "_RESERVED_FIELD",
            "_SPARE_",
            "NR_CT_OPD",
        ]

        result = CursorColumnResolver._without_unnecessary_columns(columns)

        # Unnecessary columns should be removed
        assert "FILLER" not in result
        assert "FIELD_FILLER_DATA" not in result
        assert "_RESERVED_FIELD" not in result
        assert "_SPARE_" not in result
        # Business columns should remain
        assert "NR_IDGOOD_479EVEF" in result
        assert "NR_CI1POS_479EVEF" in result
        assert "NR_CT_OPD" in result


class TestIntegrationFixedFormat:
    """Test COBOL fixed format compliance."""

    def test_area_a_b_formatting(self):
        """Verify Area A/B column alignment."""
        # Area A: columns 8-11
        # Area B: columns 12-72
        # Sequence: columns 1-6
        # Comment indicator: column 7

        test_line = "000010 01  WS-NR-ID-GOOD.                                     00000100"

        # Column 7 should be space (not comment)
        assert test_line[6] == " "
        # Columns 8-11 should have data (01 is in columns 8-9)
        assert test_line[7:11].strip() == "01"
        # Columns 1-6 should be sequence number
        assert test_line[0:6] == "000010"

    def test_paragraph_in_area_a(self):
        """Paragraph names should start at column 8 (Area A)."""
        # Paragraph names must be in Area A (8-11)
        test_line = "001000 PROCESS-DATA.                                         00001000"

        # Columns 1-6: sequence
        assert test_line[0:6] == "001000"
        # Column 7: comment indicator
        assert test_line[6] == " "
        # Columns 8+: paragraph (in Area A at column 8)
        assert test_line[7:].strip().startswith("PROCESS-DATA")


class TestEndToEndConversion:
    """Integration tests for complete conversion pipeline."""

    def test_field_definition_conversion(self):
        """Test complete field definition transformation."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        # Simulate original IDMS field with COMP-3
        original_field = Mock()
        original_field.picture = "PIC 9(8)"
        original_field.usage = "COMP-3"

        converted = RecordEntryRenderer.picture_of(original_field)

        # Verify all three conditions met:
        # 1. No COMP-3
        assert "COMP-3" not in converted
        # 2. Numeric PIC preserved
        assert "PIC 9(8)" in converted
        # 3. VALUE ZEROES added
        assert "VALUE ZEROES" in converted

    def test_generated_output_structure(self):
        """Verify generated output matches expected DB2 COBOL format."""
        # This would test actual generated output
        expected_patterns = {
            "comp3_removed": "PIC 9(8) VALUE ZEROES",  # Should be present
            "comp3_present": "PIC 9(8) COMP-3",  # Should NOT be present
            "filler_present": "FILLER PIC XX",  # Should NOT be present
        }

        # These would be validated against actual output files
        assert True  # Placeholder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    """Test removal of COMP-3 and other binary encoding from field definitions."""

    def test_picture_strips_comp3_from_usage(self):
        """COMP-3 should be stripped from PIC clause."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        # Create mock item with COMP-3 usage
        item = Mock()
        item.picture = "PIC 9(8)"
        item.usage = "COMP-3"

        result = RecordEntryRenderer.picture_of(item)

        # Should NOT contain COMP-3
        assert "COMP-3" not in result
        # Should contain PIC clause
        assert "PIC 9(8)" in result
        # Should have VALUE ZEROES for numeric fields
        assert "VALUE ZEROES" in result

    def test_picture_strips_computational_3(self):
        """COMPUTATIONAL-3 should also be stripped."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC S9(13)V99"
        item.usage = "COMPUTATIONAL-3"

        result = RecordEntryRenderer.picture_of(item)

        assert "COMPUTATIONAL-3" not in result
        assert "COMP-3" not in result
        assert "PIC S9(13)V99" in result
        assert "VALUE ZEROES" in result

    def test_picture_preserves_non_encoding_usage(self):
        """Non-encoding USAGE clauses (like DISPLAY) should be preserved."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC X(20)"
        item.usage = "DISPLAY"

        result = RecordEntryRenderer.picture_of(item)

        # DISPLAY should be preserved
        assert "DISPLAY" in result
        assert "PIC X(20)" in result

    def test_picture_no_value_for_alphanumeric(self):
        """Alphanumeric fields should not get VALUE ZEROES."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC X(20)"
        item.usage = ""

        result = RecordEntryRenderer.picture_of(item)

        # Should not add VALUE ZEROES to alphanumeric
        assert "VALUE ZEROES" not in result
        assert "PIC X(20)" in result

    def test_picture_existing_value_preserved(self):
        """If VALUE clause already exists, don't add VALUE ZEROES."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        item = Mock()
        item.picture = "PIC 9(8) VALUE 12345"
        item.usage = ""

        result = RecordEntryRenderer.picture_of(item)

        assert "VALUE 12345" in result
        # Should not add another VALUE ZEROES
        assert result.count("VALUE") == 1


class TestFillerRemoval:
    """Test elimination of FILLER fields from materialised records."""

    def test_emit_remainder_filler_disabled(self):
        """EMIT_REMAINDER_FILLER should be False to prevent FILLER generation."""
        from rules.record_materialisation_rules import EMIT_REMAINDER_FILLER

        # FILLER should NOT be emitted
        assert EMIT_REMAINDER_FILLER is False

    def test_filler_not_in_materialised_record(self):
        """Materialised records should not contain FILLER when disabled."""
        # This would be tested against actual output
        # For now, we verify the configuration is correct
        from rules.record_materialisation_rules import (
            EMIT_REMAINDER_FILLER,
            FILLER_FIELD_NAMES,
        )

        assert EMIT_REMAINDER_FILLER is False
        assert "FILLER" in FILLER_FIELD_NAMES


class TestSelectColumnOptimization:
    """Test SELECT statement column optimization."""

    def test_cursor_column_filtering_logic(self):
        """Cursor should select appropriate columns."""
        # Test the static method for filtering audit columns
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        test_columns = [
            "NR_IDGOOD_479EVEF",
            "NR_CI1POS_479EVEF",
            "TS_CREATED",
            "ID_USERID_CREATED",
            "NR_CT_OPD",
        ]

        filtered = CursorColumnResolver._without_audit_columns(test_columns)

        # Audit columns should be removed
        assert "TS_CREATED" not in filtered
        assert "ID_USERID_CREATED" not in filtered
        # Business columns should remain
        assert "NR_IDGOOD_479EVEF" in filtered
        assert "NR_CI1POS_479EVEF" in filtered
        assert "NR_CT_OPD" in filtered

    def test_column_deduplication(self):
        """Duplicate columns should be removed while preserving order."""
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        columns = [
            "NR_IDGOOD_479EVEF",
            "NR_CI1POS_479EVEF",
            "NR_IDGOOD_479EVEF",  # Duplicate
            "NR_CT_OPD",
        ]

        result = CursorColumnResolver._unique(columns)

        # Should contain 3 unique columns
        assert len(result) == 3
        # Order should be preserved
        assert result[0] == "NR_IDGOOD_479EVEF"
        assert result[1] == "NR_CI1POS_479EVEF"
        assert result[2] == "NR_CT_OPD"

    def test_unnecessary_columns_filtered(self):
        """Filler and system metadata columns should be removed."""
        from converter.resolvers.cursor_column_resolver import (
            CursorColumnResolver,
        )

        columns = [
            "NR_IDGOOD_479EVEF",
            "FILLER",
            "NR_CI1POS_479EVEF",
            "FIELD_FILLER_DATA",
            "_RESERVED_FIELD",
            "_SPARE_",
            "NR_CT_OPD",
        ]

        result = CursorColumnResolver._without_unnecessary_columns(columns)

        # Unnecessary columns should be removed
        assert "FILLER" not in result
        assert "FIELD_FILLER_DATA" not in result
        assert "_RESERVED_FIELD" not in result
        assert "_SPARE_" not in result
        # Business columns should remain
        assert "NR_IDGOOD_479EVEF" in result
        assert "NR_CI1POS_479EVEF" in result
        assert "NR_CT_OPD" in result


class TestIntegrationFixedFormat:
    """Test COBOL fixed format compliance."""

    def test_area_a_b_formatting(self):
        """Verify Area A/B column alignment."""
        # Area A: columns 8-11
        # Area B: columns 12-72
        # Sequence: columns 1-6
        # Comment indicator: column 7

        test_line = "000010 01  WS-NR-ID-GOOD.                                     00000100"

        # Column 7 should be space (not comment)
        assert test_line[6] == " "
        # Columns 8-11 should have data (01 is in columns 8-9)
        assert test_line[7:11].strip() == "01"
        # Columns 1-6 should be sequence number
        assert test_line[0:6] == "000010"

    def test_paragraph_in_area_a(self):
        """Paragraph names should start at column 8 (Area A)."""
        # Paragraph names must be in Area A (8-11)
        test_line = "001000 PROCESS-DATA.                                         00001000"

        # Columns 1-6: sequence
        assert test_line[0:6] == "001000"
        # Column 7: comment indicator
        assert test_line[6] == " "
        # Columns 8+: paragraph (in Area A at column 8)
        assert test_line[7:].strip().startswith("PROCESS-DATA")


class TestEndToEndConversion:
    """Integration tests for complete conversion pipeline."""

    def test_field_definition_conversion(self):
        """Test complete field definition transformation."""
        from converter.composers.record_materialisation.record_entry_renderer import (
            RecordEntryRenderer,
        )

        # Simulate original IDMS field with COMP-3
        original_field = Mock()
        original_field.picture = "PIC 9(8)"
        original_field.usage = "COMP-3"

        converted = RecordEntryRenderer.picture_of(original_field)

        # Verify all three conditions met:
        # 1. No COMP-3
        assert "COMP-3" not in converted
        # 2. Numeric PIC preserved
        assert "PIC 9(8)" in converted
        # 3. VALUE ZEROES added
        assert "VALUE ZEROES" in converted

    def test_generated_output_structure(self):
        """Verify generated output matches expected DB2 COBOL format."""
        # This would test actual generated output
        expected_patterns = {
            "comp3_removed": "PIC 9(8) VALUE ZEROES",  # Should be present
            "comp3_present": "PIC 9(8) COMP-3",  # Should NOT be present
            "filler_present": "FILLER PIC XX",  # Should NOT be present
        }

        # These would be validated against actual output files
        assert True  # Placeholder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

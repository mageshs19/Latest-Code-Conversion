def test_core_imports():
    from converter.domain.models import ConversionInput
    from converter.pipeline.conversion_service import ConversionService
    from converter.parsers.sheet_mapping_parser import SheetMappingParser
    from converter.parsers.dclgen_parser import DclgenParser
    from converter.parsers.copybook_parser import CopybookParser
    from converter.parsers.cobol_parser import CobolParser

    assert ConversionInput is not None
    assert ConversionService is not None
    assert SheetMappingParser is not None
    assert DclgenParser is not None
    assert CopybookParser is not None
    assert CobolParser is not None


def test_clean_architecture_imports():
    from catalogs.sheet_mapping_schema import SHEET_MAPPING_MODEL_FIELD_MAP
    from patterns.idms_patterns import OBTAIN_CALC_PATTERN
    from rules.authority_rules import INPUT_AUTHORITY_RULES

    assert SHEET_MAPPING_MODEL_FIELD_MAP
    assert OBTAIN_CALC_PATTERN
    assert INPUT_AUTHORITY_RULES


def test_layer_imports():
    from converter.repositories.mapping_repository import MappingRepository
    from converter.resolvers.table_name_resolver import TableNameResolver
    from converter.generators.sql_generator import SqlGenerator
    from converter.transformers.cobol_transformer import CobolTransformer
    from converter.validators.production_validator import ProductionValidator
    from converter.composers.cobol_formatter import CobolFormatter

    assert MappingRepository is not None
    assert TableNameResolver is not None
    assert SqlGenerator is not None
    assert CobolTransformer is not None
    assert ProductionValidator is not None
    assert CobolFormatter is not None
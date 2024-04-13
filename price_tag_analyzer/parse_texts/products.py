import os
from yargy import rule
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from price_tag_analyzer.parse_texts.unit import UNIT
from price_tag_analyzer.parse_texts.utils import create_synonyms_mapping, read_synoms_from_csv

Product = fact(
    'Product',
    ['type']
)

dirname = os.path.dirname(__file__)
file_path = os.path.join(dirname, 'data/products.csv')
products = read_synoms_from_csv(file_path)
names, mapping = create_synonyms_mapping(products)

PRODUCT_TYPE = morph_pipeline(names).interpretation(
    Product.type.normalized().custom(mapping.get)
)

PRODUCT_MEASUREMENT = UNIT

MilkType = fact(
    'MilkType',
    ['type']
)

dirname = os.path.dirname(__file__)
file_path = os.path.join(dirname, 'data/milk_types.csv')
milk_types = read_synoms_from_csv(file_path)
mt_names, mt_mapping = create_synonyms_mapping(milk_types)

MILK_TYPE = morph_pipeline(mt_names).interpretation(
    MilkType.type.normalized().custom(mt_mapping.get)
)

# ====================

PRODUCT = rule(
    PRODUCT_TYPE,
).interpretation(
    Product
)
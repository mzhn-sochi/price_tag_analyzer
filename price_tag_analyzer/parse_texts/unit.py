import os
from yargy import or_
from yargy.interpretation import fact
from yargy.pipelines import morph_pipeline
from price_tag_analyzer.parse_texts.utils import create_synonyms_mapping, read_synoms_from_csv

Unit = fact(
    'Unit',
    ['value']
)

dirname = os.path.dirname(__file__)

solid = read_synoms_from_csv(os.path.join(dirname, 'data/unit_solid.csv'))
solid_names, solid_mapping = create_synonyms_mapping(solid)

UNIT_SOLID = morph_pipeline(solid_names).interpretation(
    Unit.value.normalized().custom(solid_mapping.get)
)

liquid = read_synoms_from_csv(os.path.join(dirname, 'data/unit_liquid.csv'))
liquid_names, liquid_mapping = create_synonyms_mapping(liquid)

UNIT_LIQUID = morph_pipeline(liquid_names).interpretation(
    Unit.value.normalized().custom(liquid_mapping.get)
)


UNIT = or_(
    UNIT_SOLID,
    UNIT_LIQUID
).interpretation(
    Unit
)
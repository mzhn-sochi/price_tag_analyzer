from yargy import or_
from yargy import rule
from yargy.interpretation import fact

from price_tag_analyzer.parse_texts.unit import UNIT
from price_tag_analyzer.parse_texts.utils import DIGIT, FLOAT

Measurement = fact(
    'Measurement',
    ['amount', 'unit']
)

AMOUNT = or_(
    DIGIT,
    FLOAT
).interpretation(
    Measurement.amount
)

UNIT = UNIT.interpretation(
    Measurement.unit
)

MEASUREMENT = rule(
    AMOUNT.optional(),
    UNIT
).interpretation(
    Measurement
)
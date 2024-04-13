import re
import csv
from yargy import or_
from yargy.record import Record
from yargy.predicates import (
    eq, type as type_, in_, normalized
)
from yargy import interpretation as interp, rule
from yargy.interpretation import fact


class Synonyms(Record):
    __attributes__ = ['name', 'synonyms']
    
    def __init__(self, name, synonyms=()):
        self.name = name
        self.synonyms = synonyms


def read_synoms_from_csv(file_path):
    products = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            name, *synonyms = row
            products.append(Synonyms(name, synonyms))
    return products


def create_synonyms_mapping(synonyms_list):
    names = []
    mapping = {}
    for record in synonyms_list:
        name = record.name
        names.append(name)
        mapping[name] = name
        for synonym in record.synonyms:
            names.append(synonym)
            mapping[synonym] = name
    
    return names, mapping


INT = type_('INT')
DOT = eq('.')


def normalize_float(value):
    value = re.sub('[\s,.]+', '.', value)
    return float(value)


FLOAT = rule(
    INT,
    in_('.,'),
    INT
).interpretation(
    interp.custom(normalize_float)
)

DIGIT = INT.interpretation(
    interp.custom(int)
)


Percent = fact(
    'Percent',
    ['value']
)

PERCENT = rule(
    or_(
        DIGIT,
        FLOAT
    ).interpretation(Percent.value),
    or_(
        eq('%'),
        normalized('процент')
    )
).interpretation(
    Percent
)

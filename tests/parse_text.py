from yargy import Parser

from price_tag_analyzer.parse_texts.products import PRODUCT, EXCLUDE_PRODUCT
from price_tag_analyzer.parse_texts.measurement import MEASUREMENT
from price_tag_analyzer.parse_texts.utils import PERCENT

texts = [
    'молоко простоквашино паст.1,5% 930мл',
    'яблоко "зимний банан", цена за кг',
    'томатная паста за 0,5 кг',
    'кефир 2,5% 0,9л',
    'сыр плавленный Дружба',
    'сыр рокфор'
]

for text in texts:
    productParser = Parser(EXCLUDE_PRODUCT)
    match = productParser.find(text)

    if match:
        continue

    print('------------')

    productParser = Parser(PRODUCT)
    match = productParser.find(text)

    if not match:
        continue

    product = match.fact
    print('Название товара:', product.type)

    if product.type in ['молоко', 'кефир']:
        percentParser = Parser(PERCENT)
        match = percentParser.find(text)

        if match:
            print(f'{match.fact.value}%')


    unitParser = Parser(MEASUREMENT)
    match = unitParser.find(text)

    if match:
        print(f'за {match.fact.amount or 1} {match.fact.unit.value}')
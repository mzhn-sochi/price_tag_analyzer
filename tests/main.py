import sys
import ultralytics
from ultralytics import YOLO
import supervision as sv
import cv2
import easyocr
from spellchecker import SpellChecker
from yargy import Parser

from price_tag_analyzer.parse_texts.products import PRODUCT, EXCLUDE_PRODUCT
from price_tag_analyzer.parse_texts.measurement import MEASUREMENT
from price_tag_analyzer.parse_texts.utils import PERCENT

similar_characters = {
    'з': '3',
    'o': '0',
    'о': '0',
    'б': '6',
}


def main():

    ultralytics.checks()

    img = cv2.imread('test-1.jpg')

    #### ШАГ 1 - YOLO

    model = YOLO('yolov8-price-tag-detection.pt')
    results = model(img)
    detections = sv.Detections.from_ultralytics(results[0])

    #### ШАГ 2 - OCR

    reader = easyocr.Reader(['ru', 'en'])
    price = ''

    description = False
    price_whole = False
    price_fraction = False


    detections = [list(z) for z in zip(detections.xyxy, detections.confidence, detections.class_id)]

    sorted_detections = sorted(detections, key=lambda x: x[1], reverse=True)

    N = 10

    for bbox, confidence, class_id in sorted_detections:
        class_name = model.names[class_id]
        x_min, y_min, x_max, y_max = map(int, bbox[:4])

        x_min = max(x_min - N, 0)
        y_min = max(y_min - N, 0)
        x_max = min(x_max + N, img.shape[1])
        y_max = min(y_max + N, img.shape[0])

        cropped_image = img[y_min:y_max, x_min:x_max]
        ocr_result = reader.readtext(cropped_image)

        # TODO: сделать красивее
        if len(ocr_result) > 0:
            if class_name == 'description' and not description:
                description = ''
                for r in ocr_result:
                    description += r[1] + ' '
                description = description.strip()
            if class_name == 'price_whole' and not price_whole:
                price_whole = ocr_result[0][1]
            if class_name == 'price_fraction' and not price_fraction:
                print(price_fraction)
                price_fraction = ocr_result[0][1]

    if not price_fraction:
        price_fraction = '00'

    price = f'{price_whole}.{price_fraction}'

    print('Description:', description)
    print('Price:', price)
    
    #### ШАГ 3.1 - попытка исправить цену и описание

    corrected_price = ""
    for character in price:
        if character in similar_characters:
            corrected_price += similar_characters[character]
        else:
            corrected_price += character
    price = corrected_price


    description = description.lower()

    corrected_text = ""
    for i, character in enumerate(description):
        next_character_is_digit = (i + 1 < len(description)) and description[i + 1].isdigit()
        previous_character_is_digit = (i - 1 >= 0) and corrected_text[i - 1].isdigit()

        if (previous_character_is_digit or next_character_is_digit) and character in similar_characters:
            corrected_text += similar_characters[character]
        else:
            corrected_text += character

    description = corrected_text

    #### ШАГ 3 - SPELLCHECKER

    spell = SpellChecker(language='ru')

    # ?????
    # Нужно добавить словарь
    # ?????

    # Удаляем существующий словарь
    spell.word_frequency.remove_by_threshold(sys.maxsize)

    # TODO: загружать из файлов parse_texts/data
    spell.word_frequency.add('сыр', 10000)

    text = description
    words = text.split()

    # Находим слова с ошибками
    mistakes = spell.unknown(words)

    # Создаем словарь с исправлениями
    corrections = {mistake: spell.correction(mistake) if spell.correction(mistake) is not None else mistake for mistake in mistakes}

    # Заменяем каждую ошибку в тексте на ее исправление, используя .get() для избежания None
    corrected_words = [corrections.get(word, word) for word in words]

    # Собираем обратно в предложение
    corrected_text = ' '.join(corrected_words)

    description = corrected_text

    print('Corrected description: ', description)

    #### ШАГ 4 - NER с помощью парсера Yargy (правила для извлечения сущностей описываются с помощью контекстно-свободных грамматик и словарей)

    productParser = Parser(EXCLUDE_PRODUCT)
    match = productParser.find(text)

    if match:
        return

    print('------------')

    productParser = Parser(PRODUCT)
    match = productParser.find(text)

    if not match:
        return

    product = match.fact
    print('Название товара:', product.type)

    if product.type in ['молоко', 'кефир']:
        percentParser = Parser(PERCENT)
        match = percentParser.find(text)

        if match:
            print(f'- {match.fact.value}%')


    unitParser = Parser(MEASUREMENT)
    match = unitParser.find(text)

    if match:
        print(f'- {match.fact.amount or 1} {match.fact.unit.value}')

    print('Цена:', price)


if __name__ == '__main__':
    main()
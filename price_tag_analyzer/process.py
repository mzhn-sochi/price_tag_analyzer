import json

import supervision as sv
from dataclasses import dataclass

from loguru import logger
from yargy import Parser
import time
from price_tag_analyzer import settings
from price_tag_analyzer.parse_texts.products import MILK_TYPE, PRODUCT
from price_tag_analyzer.parse_texts.measurement import MEASUREMENT
from price_tag_analyzer.parse_texts.utils import PERCENT


@dataclass
class Measure:
    amount: float
    unit: str


@dataclass
class ImageInfo:
    product: str
    description: str
    price: float
    measure: Measure
    attributes: dict


def yolo(img, model):
    results = model(img, verbose=False, imgsz=settings.YOLO_IMAGE_SIZE)
    detections = sv.Detections.from_ultralytics(results[0])
    return detections


BBOX_OCR_PADDING = 10
SIMILAR_CHARACTERS_NUMBERS = {
    'з': '3',
    'o': '0',
    'о': '0',
    'б': '6',
}

SIMILAR_CHARACTERS_SPECIAL = {
    'r': 'г',
}

# SIMILAR_CHARACTERS = {**SIMILAR_CHARACTERS_NUMBERS, **SIMILAR_CHARACTERS_SPECIAL}


def _fix_price_part(price_part: str):
    price_part = price_part.lower()

    corrected = ''
    for character in price_part:
        if character in SIMILAR_CHARACTERS_NUMBERS:
            corrected += SIMILAR_CHARACTERS_NUMBERS[character]
        elif character.isdigit():
            corrected += character

    return corrected


def ocr(img, detections, reader, model):
    """
    Функция для оптического распознавания символов на изображении с использованием детектированных объектов.

    :param img: Изображение, на котором нужно выполнить OCR.
    :param detections: Объекты, детектированные на изображении.
    :param reader: Экземпляр OCR-читалки, который будет использоваться для распознавания текста.
    :param model: Модель, используемая для детекции объектов на изображении. Должна содержать атрибут names для
                  получения названия класса по его идентификатору.

    :return: Возвращает кортеж из трех элементов:
             - Описание товара (строка).
             - Цена товара в формате строка, где целая и дробная части разделены точкой.
             - Булево значение, указывающее на успешное распознавание и извлечение и описания, и целой части цены.
    """
    detections = sorted(
        [(bbox, confidence, class_id) for bbox, confidence, class_id in
         zip(detections.xyxy, detections.confidence, detections.class_id)],
        key=lambda x: x[1], reverse=True
    )

    description, price_whole, price_fraction = "", "0", "00"
    description_parsed, price_whole_parsed, price_fraction_parsed = False, False, False

    for bbox, confidence, class_id in detections:
        class_name = model.names[class_id]
        x_min, y_min, x_max, y_max = map(int, bbox[:4])

        x_min, y_min = max(x_min - BBOX_OCR_PADDING, 0), max(y_min - BBOX_OCR_PADDING, 0)
        x_max, y_max = min(x_max + BBOX_OCR_PADDING, img.shape[1]), min(y_max + BBOX_OCR_PADDING, img.shape[0])

        cropped_image = img[y_min:y_max, x_min:x_max]
        ocr_result = reader.readtext(cropped_image, paragraph=True)

        if ocr_result:
            text = ocr_result[0][1]
            if class_name == 'description' and not description_parsed:
                description = ' '.join([r[1] for r in ocr_result]).strip()
                description_parsed = True
            elif class_name == 'price_whole' and not price_whole_parsed:
                price_whole = _fix_price_part(text)
                price_whole_parsed = True
            elif class_name == 'price_fraction' and not price_fraction_parsed:
                price_fraction = _fix_price_part(text)
                price_fraction_parsed = True
            elif class_name == 'social_price_label':
                logger.info("СОЦИАЛЬНЫЙ ТОВАР!")

    price = f'{price_whole}.{price_fraction}'
    return description, price, description_parsed and price_whole_parsed


def spellcheck(description, spellchecker):
    description = description.lower()

    corrected_text = ""
    for i, character in enumerate(description):
        next_character_is_digit = (i + 1 < len(description)) and description[i + 1].isdigit()
        previous_character_is_digit = (i - 1 >= 0) and corrected_text[i - 1].isdigit()

        if (previous_character_is_digit or next_character_is_digit) and character in SIMILAR_CHARACTERS_NUMBERS:
            corrected_text += SIMILAR_CHARACTERS_NUMBERS[character]
        else:
            corrected_text += character

    description = corrected_text
    corrected_text = ""
    for i, character in enumerate(corrected_text):
        if character in SIMILAR_CHARACTERS_SPECIAL:
            corrected_text += SIMILAR_CHARACTERS_SPECIAL[character]
        else:
            corrected_text += character
    corrected_text = description

    spell = spellchecker
    text = description
    words = text.split()
    mistakes = spell.unknown(words)
    corrections = {mistake: spell.correction(mistake) if spell.correction(mistake) is not None else mistake for mistake
                   in mistakes}
    # Заменяем каждую ошибку в тексте на ее исправление, используя .get() для избежания None
    corrected_words = [corrections.get(word, word) for word in words]
    # Собираем обратно в предложение
    description = ' '.join(corrected_words)
    return description


product_parser = Parser(PRODUCT)
unit_parser = Parser(MEASUREMENT)
percent_parser = Parser(PERCENT)
milk_type_parser = Parser(MILK_TYPE)


def ner_extract_product(description):
    text = description
    match = product_parser.find(text)

    if not match:
        product_type = "Прочее"
    else:
        product_type = match.fact.type

    attributes = dict()


    # TODO: обработка большего количества атрибутов/продуктов

    if product_type in ['Молоко', 'Кефир']:
        match = percent_parser.find(text)
        if match:
            attributes['fat_content'] = str(match.fact.value)

    if product_type == 'Молоко':
        match = milk_type_parser.find(text)
        if match:
            attributes['milk_type'] = str(match.fact)
        
        # temp fix
        product_type += ' ' + attributes['milk_type']

    measure = Measure(
        amount=1,
        unit="штука"
    )

    match = unit_parser.find(text)
    if match:
        measure = Measure(
            amount=match.fact.amount or 1,
            unit=match.fact.unit.value
        )

    return product_type, measure, attributes


class ProcessException(Exception):
    step: str
    attributes = []

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def json_dump(self):
        obj = {'step': self.step}
        for attribute in self.attributes:
            if hasattr(self, attribute):
                obj[attribute] = getattr(self, attribute)

        return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)


class YOLOException(ProcessException):
    step = 'yolo'


class OCRException(ProcessException):
    step = 'ocr'
    attributes = ['description', 'price', 'reason']
    description: str
    price: str
    reason: str


class SpellcheckerException(ProcessException):
    step = 'spell'
    attributes = ['description', 'price']
    description: str
    price: str


class NERExtractionException(ProcessException):
    step = 'ner'
    attributes = ['description', 'price']
    description: str
    price: str


def process(img, model, reader, spellchecker):
    start = time.time()
    # ШАГ 1 - YOLO
    try:
        detections = yolo(img, model)
    except Exception as e:
        logger.exception("YOLO Exception!")
        raise YOLOException()
    end = time.time()
    logger.debug("YOLO: {:.2f} sec".format(end - start))
    
    start = time.time()
    # ШАГ 2 - OCR
    description, price = '', ''
    try:
        description, price, description_and_price_whole_found = ocr(img, detections, reader, model)
    except Exception as e:
        logger.exception("ocr_error")
        raise OCRException(
            reason='ocr_error',
            description=description,
            price=price,
        )

    if not description_and_price_whole_found:
        raise OCRException(
            reason='description_or_price_not_found',
            description=description,
            price=price,
        )

    try:
        price = float(price)
    except ValueError:
        raise OCRException(
            reason='price_is_not_float',
            description=description,
            price=price
        )
    end = time.time()
    logger.debug("OCR: {:.2f} sec".format(end - start))

    start = time.time()
    # ШАГ 3 - Spellchecker
    fixed_description = description
    try:
        fixed_description = spellcheck(description, spellchecker)
    except Exception as e:
        raise SpellcheckerException(
            description=fixed_description,
            price=price
        )
    end = time.time()
    logger.debug("Spellcheck: {:.2f} sec".format(end - start))

    logger.debug(f"Description: {description}")
    logger.debug(f"Fixed description: {fixed_description}")

    start = time.time()
    # ШАГ 4 - NER
    try:
        product_type, measure, attributes = ner_extract_product(fixed_description)
    except Exception as e:
        raise NERExtractionException(
            description=fixed_description,
            price=price
        )
    end = time.time()
    logger.debug("NER: {:.2f} sec".format(end - start))

    return ImageInfo(
        product=product_type,
        price=price,
        description=fixed_description,
        measure=measure,
        attributes=attributes,
    )

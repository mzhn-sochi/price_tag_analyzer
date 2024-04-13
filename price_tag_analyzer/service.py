import os
import sys
import time

import grpc
import numpy as np
from loguru import logger

from price_tag_analyzer.grpc_compiled import PriceTagAnalyzerService_pb2, PriceTagAnalyzerService_pb2_grpc
from ultralytics import YOLO
from spellchecker import SpellChecker
import cv2
import easyocr

from price_tag_analyzer.process import process, ProcessException

MODEL_NAME = 'yolov8-price-tag-detection.pt'


class PriceTagAnalyzerService(PriceTagAnalyzerService_pb2_grpc.PriceTagAnalyzerService):
    def __init__(self):
        self.model = YOLO(MODEL_NAME)
        self.reader = easyocr.Reader(['ru', 'en'])
        self.spellchecker = SpellChecker(language=['ru', 'en'])
        # Повышаем приоритет известных слов (названий продуктов и единиц измерений) в словаре
        current_dir = os.path.dirname(os.path.realpath(__file__))
        csv_files = ['products.csv', 'unit_liquid.csv', 'unit_solid.csv']
        for file_name in csv_files:
            with open(os.path.join(current_dir, 'parse_texts/data/', file_name), 'r') as f:
                for line in f:
                    for phrase in line.strip().split(','):
                        for word in phrase.split(' '):
                            self.spellchecker.word_frequency.add(word, sys.maxsize)

    @logger.catch
    def AnalyzeImage(self, request_iterator, context):
        start = time.time()

        image_data = b''
        for chunk in request_iterator:
            image_data += chunk.content

        np_arr = np.frombuffer(image_data, np.uint8)
        img_np = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        try:
            imginfo = process(
                img_np,
                self.model,
                self.reader,
                self.spellchecker,
            )

            result = PriceTagAnalyzerService_pb2.ImageInfo(
                product=imginfo.product,
                description=imginfo.description,
                price=imginfo.price,
                attributes=imginfo.attributes,
            )

            if imginfo.measure is not None:
                result.measure.amount = imginfo.measure.amount
                result.measure.unit = imginfo.measure.unit

            logger.info(f"{imginfo}")
            return result
        except ProcessException as e:
            logger.warning(f"ProcessException: {e.json_dump()}")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(e.json_dump())
        except Exception as e:
            logger.exception(e)
        finally:
            del img_np
            end = time.time()
            logger.info("Request took {:.2f} sec".format(end - start))


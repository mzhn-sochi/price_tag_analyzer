import asyncio
import json
import time
import aiohttp
from loguru import logger
import nats

import os
import sys

import numpy as np
from loguru import logger

from ultralytics import YOLO
from spellchecker import SpellChecker
import cv2
import easyocr

from price_tag_analyzer.process import process, ProcessException

MODEL_NAME = 'yolov8-price-tag-detection.pt'

OCR_QUEUE = 'queue:ocr'
ERRORS_QUEUE = 'queue:tickets:errors'
TICKETS_STATUS_QUEUE = 'queue:tickets:status'
VALIDATION_QUEUE = 'queue:validation'


class Server:
    def __init__(self, nats_url="nats://localhost:4222", image_base_url=''):
        self.nats_url = nats_url
        self.image_base_url = image_base_url
        self.nc = None
        self.semaphore = asyncio.Semaphore(1)

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

    async def fetch_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.image_base_url + url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    img_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
                    return img_np
                else:
                    raise Exception(f"Failed to fetch image with status {response.status}")

    def serialize_dataclass(self, obj):
        if isinstance(obj, list):
            return [self.serialize_dataclass(item) for item in obj]
        if not hasattr(obj, "__dataclass_fields__"):
            return obj
        return {field: self.serialize_dataclass(getattr(obj, field)) for field in obj.__dataclass_fields__}

    async def message_handler(self, msg):
        async with self.semaphore:
            try:
                start = time.time()

                if 'ticket_id' not in msg.headers:
                    logger.warning("No ticket_id in message headers")
                    return

                ticket_id = msg.headers['ticket_id']
                data = msg.data.decode()
                logger.info(f"Received a message: {data}")

                message_data = json.loads(data)
                image_url = message_data['image_url']

                img_np = await self.fetch_image(image_url)

                try:
                    imginfo = process(
                        img_np,
                        self.model,
                        self.reader,
                        self.spellchecker,
                    )

                    result_message = json.dumps(self.serialize_dataclass(imginfo))

                    await self.nc.publish(
                        TICKETS_STATUS_QUEUE,
                        '{"type":"ocr"}'.encode(),
                        headers={'ticket_id': ticket_id}
                    )
                    await self.nc.publish(
                        VALIDATION_QUEUE,
                        result_message.encode(),
                        headers={'ticket_id': ticket_id}
                    )

                    logger.info(f"{imginfo}")
                except ProcessException as e:
                    error_message = f"ProcessException: {e.json_dump()}"
                    err = {
                        'message': error_message
                    }
                    await self.nc.publish(ERRORS_QUEUE, json.dumps(err).encode(), headers={"ticket_id": ticket_id})
                    logger.warning(error_message)
                except Exception as e:
                    error_message = f"Unexpected error: {str(e)}"
                    err = {
                        'message': error_message
                    }
                    await self.nc.publish(ERRORS_QUEUE, json.dumps(err).encode(), headers={"ticket_id": ticket_id})
                    logger.exception(e)
                finally:
                    del img_np
                    end = time.time()
                    logger.info("Request took {:.2f} sec".format(end - start))
            except (json.JSONDecodeError, KeyError) as e:
                error_message = f"Error processing message: {str(e)}"
                await self.nc.publish("ERRORS", error_message.encode())
                logger.error(error_message)
            except Exception as e:
                error_message = f"Unexpected error: {str(e)}"
                await self.nc.publish("ERRORS", error_message.encode())
                logger.exception(e)

    async def serve(self):
        self.nc = await nats.connect(self.nats_url)

        # Подписываемся на тему "OCR" с обработчиком сообщений
        await self.nc.subscribe(OCR_QUEUE, cb=self.message_handler)

        logger.info("Server is ready!")

        try:
            # Ждем бесконечно или пока соединение активно
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Server is shutting down.")
        finally:
            await self.nc.close()

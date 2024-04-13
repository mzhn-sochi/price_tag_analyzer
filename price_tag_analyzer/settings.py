import os

NATS_URL = os.getenv("NATS_URL", "nats://localhost:4222")
ENVIRONMENT = os.getenv('ENVIRONMENT', "production")
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG').upper()
YOLO_IMAGE_SIZE = int(os.getenv('YOLO_IMAGE_SIZE', '320'))

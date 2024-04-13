import ultralytics
import asyncio

from price_tag_analyzer import settings
from price_tag_analyzer.loguru_intercept_handler import setup_logging
from price_tag_analyzer.server import Server

setup_logging(settings.LOG_LEVEL, False)


async def main():
    ultralytics.checks()

    server = Server(
        nats_url=settings.NATS_URL,
        image_base_url=settings.IMAGE_BASE_URL,
    )
    await server.serve()

loop = asyncio.get_event_loop()
if settings.ENVIRONMENT == 'development':
    import tracemalloc
    tracemalloc.start()
    import aiomonitor
    with aiomonitor.start_monitor(loop=loop):
        loop.run_until_complete(main())
else:
    loop.run_until_complete(main())

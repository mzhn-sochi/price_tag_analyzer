import asyncio
import json
from nats.aio.client import Client as NATS

async def run():
    # Connect to a NATS server
    nc = NATS()
    await nc.connect("nats://77.221.158.75:4222")

    # Data to send, replace 'your_image_url' with an actual URL
    ticket_id = "12345"
    photo_url = "https://download.slipenko.com/mzhn-team-sochi/train_dataset_dnr-train/train/IMG_6028.jpg"

    # Construct the message as a JSON string
    message = json.dumps({
        "image_url": photo_url
    })

    # Publish the message to the OCR subject
    await nc.publish("queue:ocr", message.encode('utf-8'), headers={"ticket_id": ticket_id})
    print(f"Message published to 'OCR': {message}")

    # Gracefully close the connection
    await nc.drain()

# Run the client
if __name__ == '__main__':
    asyncio.run(run())

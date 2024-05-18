import enum
import json
import uuid

import aio_pika

from config import settings


def _create_message(data):
    return aio_pika.Message(
        body=data,
        content_type="application/json",
        content_encoding="utf-8",
        message_id=uuid.uuid4().hex,
        delivery_mode=aio_pika.abc.DeliveryMode.PERSISTENT,
        app_id=settings.TITLE,
    )


class Exchanges(enum.Enum):
    notification = "notification-service"
    email = "smtp-service"


async def publish_message(data, queue):
    connection = await aio_pika.connect_robust(settings.rabbit_conn)
    async with connection:
        routing_key = getattr(Exchanges, queue).value
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        message = _create_message(data.model_dump_json().encode())
        await channel.default_exchange.publish(
            message,
            routing_key=routing_key
        )

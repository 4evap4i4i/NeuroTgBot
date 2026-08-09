import logging

from aiogram import BaseMiddleware
from aiogram.types import Update

logger = logging.getLogger(__name__)

class Loger(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        user = data.get("event_from_user")
        logger.info(f"Update from {user.id if user else '?'}: {event.event_type}")
        try:
            return await handler(event, data)
        except Exception:
            logger.exception(f"Unhandled error processing update {event.update_id}")
            raise
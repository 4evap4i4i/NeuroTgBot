import asyncpg
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import db_url

router = Router()

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_history (
    id         SERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


@router.message(Command("reset"))
async def router_reset_history(message: Message) -> None:
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_TABLE_SQL)
        result = await conn.execute(
            "DELETE FROM chat_history WHERE user_id = $1", message.from_user.id
        )
    finally:
        await conn.close()

    deleted = int(result.split()[-1])
    await message.answer(
        f"История чата очищена ({deleted} сообщений удалено)."
        if deleted
        else "История чата была пуста — начинаем с чистого листа."
    )
"""
Модуль работы с таблицей истории чата в Neon.

Схема (создаётся автоматически при первом обращении, если её ещё нет):

    CREATE TABLE chat_history (
        id         SERIAL PRIMARY KEY,
        user_id    BIGINT NOT NULL,
        role       TEXT NOT NULL,      -- 'user' / 'assistant' / 'system'
        content    TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );

Зависимость: asyncpg (та же, что для tools/document_tool.py)
"""

import asyncpg

from config import db_url

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS chat_history (
    id         SERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    role       TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def ensure_table() -> None:
    """
    Гарантирует существование таблицы chat_history.
    CREATE TABLE IF NOT EXISTS атомарен на уровне Postgres — отдельная
    проверка "существует ли таблица" перед созданием не нужна и создаёт
    гонку при параллельных вызовах.
    """
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_TABLE_SQL)
    finally:
        await conn.close()


async def save_message(user_id: int, role: str, content: str) -> None:
    """Добавляет одно сообщение в историю. Таблицу создаёт при необходимости."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_TABLE_SQL)  # безопасно вызывать каждый раз
        await conn.execute(
            "INSERT INTO chat_history (user_id, role, content) VALUES ($1, $2, $3)",
            user_id, role, content,
        )
    finally:
        await conn.close()


async def get_history(user_id: int) -> list[dict]:
    """Возвращает историю сообщений пользователя в хронологическом порядке."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_TABLE_SQL)
        rows = await conn.fetch(
            "SELECT role, content FROM chat_history WHERE user_id = $1 ORDER BY created_at ASC",
            user_id,
        )
    finally:
        await conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]
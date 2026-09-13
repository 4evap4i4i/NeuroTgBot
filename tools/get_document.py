"""
Tool: get_document

Запрашивает документ (PDF, хранится как bytea) из Neon по его id
и возвращает извлечённый текст, готовый к подстановке в контекст модели.

Допущение по схеме (поправь под свою реальную таблицу):

    CREATE TABLE documents (
        id       SERIAL PRIMARY KEY,
        filename TEXT,
        content  BYTEA
    );

Зависимости: добавить в requirements.txt
    asyncpg
    pymupdf
"""

import asyncpg
import fitz  # PyMuPDF

from config import db_url

CREATE_DOCUMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id         SERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL,
    filename   TEXT,
    content    BYTEA NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


async def ensure_documents_table() -> None:
    """Гарантирует существование таблицы documents. Вызывается на старте бота."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_DOCUMENTS_TABLE_SQL)
    finally:
        await conn.close()


async def save_document(user_id: int, filename: str, content: bytes) -> int:
    """Сохраняет PDF в Neon и возвращает id новой записи."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        await conn.execute(CREATE_DOCUMENTS_TABLE_SQL)
        row = await conn.fetchrow(
            "INSERT INTO documents (user_id, filename, content) VALUES ($1, $2, $3) RETURNING id",
            user_id, filename, content,
        )
    finally:
        await conn.close()
    return row["id"]


async def get_document(document_id: int, user_id: int) -> str:
    """
    Достаёт документ из Neon по id и возвращает его текстовое содержимое.
    Ограничено владельцем (user_id), чтобы один пользователь не мог прочитать
    чужой документ, подобрав id.

    :param document_id: id строки в таблице documents
    :param user_id: id пользователя Telegram, которому должен принадлежать документ
    :return: извлечённый текст, либо сообщение о проблеме (документ не найден,
             принадлежит другому пользователю, или это скан без текстового слоя —
             тогда нужен отдельный OCR/vision-путь)
    """
    conn = await asyncpg.connect(dsn=db_url)
    try:
        row = await conn.fetchrow(
            "SELECT filename, content FROM documents WHERE id = $1 AND user_id = $2",
            document_id, user_id,
        )
    finally:
        await conn.close()

    if row is None:
        return f"Документ с id={document_id} не найден (или принадлежит другому пользователю)."

    filename, content = row["filename"], row["content"]

    doc = fitz.open(stream=content, filetype="pdf")
    pages_text = [page.get_text() for page in doc]
    doc.close()

    text = "\n".join(pages_text).strip()
    if not text:
        return f"В документе «{filename}» не найдено текста (возможно, это скан — нужен OCR)."

    return text


async def get_user_documents(user_id: int) -> list[dict]:
    """Возвращает список документов пользователя (id + filename) для меню-кнопок."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        rows = await conn.fetch(
            "SELECT id, filename FROM documents WHERE user_id = $1 ORDER BY created_at DESC",
            user_id,
        )
    finally:
        await conn.close()
    return [{"id": row["id"], "filename": row["filename"]} for row in rows]


# JSON-схема для регистрации инструмента в вызове модели (tools=[...])
get_document_tool_schema = {
    "type": "function",
    "function": {
        "name": "get_document",
        "description": "Возвращает текстовое содержимое документа (PDF) по его id из базы данных.",
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {
                    "type": "integer",
                    "description": "id документа в таблице documents",
                }
            },
            "required": ["document_id"],
        },
    },
}
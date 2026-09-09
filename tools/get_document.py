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


async def get_document(document_id: int) -> str:
    """
    Достаёт документ из Neon по id и возвращает его текстовое содержимое.

    :param document_id: id строки в таблице documents
    :return: извлечённый текст, либо сообщение об ошибке, если документ
             не найден или не содержит текстового слоя (тогда нужен
             отдельный OCR/vision-путь — см. предыдущий вариант с рендером
             страниц в картинки)
    """
    conn = await asyncpg.connect(dsn=db_url)
    try:
        row = await conn.fetchrow(
            "SELECT filename, content FROM documents WHERE id = $1",
            document_id,
        )
    finally:
        await conn.close()

    if row is None:
        return f"Документ с id={document_id} не найден."

    filename, content = row["filename"], row["content"]

    doc = fitz.open(stream=content, filetype="pdf")
    pages_text = [page.get_text() for page in doc]
    doc.close()

    text = "\n".join(pages_text).strip()
    if not text:
        raise ValueError(f"There's no any text in {filename}!")

    return text


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
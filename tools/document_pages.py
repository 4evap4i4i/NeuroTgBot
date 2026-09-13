"""
Tools: read_document, get_pages

Двухшаговый пайплайн работы модели с PDF:

1. read_document(document_id) — отдаёт ВЕСЬ текст документа целиком, без
   каких-либо сокращений, но с пометкой номера каждой страницы. Модель
   читает документ полностью и сама решает, какие страницы ей нужны.

2. get_pages(document_id, page_numbers) — модель передаёт только номера
   нужных страниц. Инструмент возвращает их текст в точности как он есть
   в PDF — без обрезки предложений, без скоринга, без фильтрации.

Никакой эвристики и урезания информации в пайплайне нет: шаг 1 показывает
всё, шаг 2 отдаёт запрошенное один в один.
"""

import asyncpg
import fitz  # PyMuPDF

from config import db_url

PAGE_MARKER = "=== Страница {n} ==="

# Самопроверка для модели, добавляется в конец ответа каждого инструмента
READ_DOCUMENT_GUIDANCE = (
    "\n\n---\n"
    "Прежде чем звать get_pages: на каких страницах есть нужная информация, "
    "и хватает ли уверенности в этих номерах?"
)
GET_PAGES_GUIDANCE = (
    "\n\n---\n"
    "Это та информация, которая нужна? Если нет — вернись к read_document "
    "или вызови get_pages ещё раз с другими номерами."
)


async def _fetch_document(document_id: int, user_id: int) -> tuple[str, bytes] | None:
    """Общий доступ к БД. Возвращает (filename, content) или None, если документа нет / не тот владелец."""
    conn = await asyncpg.connect(dsn=db_url)
    try:
        row = await conn.fetchrow(
            "SELECT filename, content FROM documents WHERE id = $1 AND user_id = $2",
            document_id, user_id,
        )
    finally:
        await conn.close()

    if row is None:
        return None
    return row["filename"], row["content"]


async def read_document(document_id: int, user_id: int) -> str:
    """
    Возвращает полный текст документа, страница за страницей, без сокращений.
    Каждая страница помечена номером, чтобы модель могла потом запросить
    конкретные страницы через get_pages.
    """
    doc_row = await _fetch_document(document_id, user_id)
    if doc_row is None:
        return f"Документ с id={document_id} не найден (или принадлежит другому пользователю)."

    filename, content = doc_row
    pdf = fitz.open(stream=content, filetype="pdf")

    parts = [f"Документ «{filename}», всего страниц: {pdf.page_count}.\n"]
    for i, page in enumerate(pdf, start=1):
        text = page.get_text().strip()
        parts.append(f"{PAGE_MARKER.format(n=i)}\n{text if text else '(страница пустая или без текстового слоя)'}")
    pdf.close()

    return "\n\n".join(parts) + READ_DOCUMENT_GUIDANCE


async def get_pages(document_id: int, page_numbers: list[int], user_id: int) -> str:
    """
    Возвращает текст указанных страниц в точности как в PDF — без каких-либо
    сокращений или фильтрации. Некорректные номера (вне диапазона, дубликаты)
    аккуратно пропускаются с пояснением, остальные страницы возвращаются полностью.
    """
    doc_row = await _fetch_document(document_id, user_id)
    if doc_row is None:
        return f"Документ с id={document_id} не найден (или принадлежит другому пользователю)."

    filename, content = doc_row
    pdf = fitz.open(stream=content, filetype="pdf")

    if not page_numbers:
        pdf.close()
        return "Не передано ни одного номера страницы."

    seen = set()
    valid_parts = []
    skipped = []

    for n in page_numbers:
        if n in seen:
            continue
        seen.add(n)

        if not (1 <= n <= pdf.page_count):
            skipped.append(n)
            continue

        text = pdf[n - 1].get_text().strip()
        valid_parts.append(f"{PAGE_MARKER.format(n=n)}\n{text if text else '(страница пустая или без текстового слоя)'}")

    page_count = pdf.page_count
    pdf.close()

    if skipped and not valid_parts:
        return (
            f"⚠️ ОШИБКА: страниц(ы) {skipped} не существует в документе «{filename}» "
            f"(всего страниц: {page_count}). Ни одна из запрошенных страниц не найдена — "
            f"перепроверь номера по результату read_document и вызови get_pages заново."
        )

    result = [f"Документ «{filename}»:\n"]

    if skipped:
        result.append(
            f"⚠️ ОШИБКА В ЗАПРОСЕ: страниц(ы) {skipped} не существует в документе "
            f"(всего страниц: {page_count}). Эти номера проигнорированы — если искомая информация "
            f"должна была быть на одной из них, значит номер указан неверно. Ниже — только те "
            f"страницы, что удалось найти; при необходимости перепроверь остальные номера и "
            f"вызови get_pages ещё раз.\n"
        )

    result.extend(valid_parts)

    return "\n\n".join(result) + GET_PAGES_GUIDANCE


# JSON-схемы для регистрации инструментов в вызове модели (tools=[...])

read_document_tool_schema = {
    "type": "function",
    "function": {
        "name": "read_document",
        "description": (
            "Возвращает ПОЛНЫЙ текст документа целиком, без сокращений, каждая страница помечена номером. "
            "Вызови первым шагом, чтобы прочитать документ и понять, на каких страницах нужная информация."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer", "description": "id документа в таблице documents"},
            },
            "required": ["document_id"],
        },
    },
}

get_pages_tool_schema = {
    "type": "function",
    "function": {
        "name": "get_pages",
        "description": (
            "Возвращает текст указанных страниц документа в полном объёме, без каких-либо сокращений. "
            "Вызови вторым шагом, после read_document, передав только номера страниц, которые реально нужны."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "document_id": {"type": "integer", "description": "id документа в таблице documents"},
                "page_numbers": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "номера нужных страниц, с 1",
                },
            },
            "required": ["document_id", "page_numbers"],
        },
    },
}

import json

from openai import AsyncOpenAI, DefaultAioHttpClient

from config import ai
from tools.document_pages import get_pages, get_pages_tool_schema, read_document, read_document_tool_schema
from tools.get_document import get_document, get_document_tool_schema

model = "qwen/qwen3.6-27b"

TOOLS = [get_document_tool_schema, read_document_tool_schema, get_pages_tool_schema]

MAX_TOOL_ROUNDS = 5

TOOL_FUNCTIONS = {
    "get_document": lambda args, user_id: get_document(args["document_id"], user_id),
    "read_document": lambda args, user_id: read_document(args["document_id"], user_id),
    "get_pages": lambda args, user_id: get_pages(args["document_id"], args["page_numbers"], user_id),
}


async def call(data: list[dict], user_id: int) -> str:
    """
    Отправляет историю чата модели. Пока модель просит вызвать инструменты
    (get_document / read_document / get_pages) — выполняем их и отправляем
    результат обратно, до MAX_TOOL_ROUNDS раундов. Это нужно, чтобы модель
    могла сначала прочитать документ целиком (read_document), а затем
    отдельным вызовом запросить только нужные страницы (get_pages) —
    одного раунда tool-calling для такой цепочки не хватит.

    user_id берётся из Telegram, а не от модели — чтобы модель не могла
    подставить чужой document_id и прочитать не свой документ.
    """
    messages = list(data)

    async with AsyncOpenAI(
        api_key=ai,
        http_client=DefaultAioHttpClient(),
        base_url="https://api.groq.com/openai/v1",
    ) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.chat.completions.create(
                messages=messages,
                model=model,
                tools=TOOLS,
            )
            message = response.choices[0].message

            if not message.tool_calls:
                return str(message.content)

            messages.append(message.model_dump(exclude_none=True))

            for tool_call in message.tool_calls:
                func = TOOL_FUNCTIONS.get(tool_call.function.name)
                if func is None:
                    result = f"Неизвестный инструмент: {tool_call.function.name}"
                else:
                    try:
                        args = json.loads(tool_call.function.arguments)
                        result = await func(args, user_id)
                    except Exception as exc:
                        result = f"Ошибка при вызове {tool_call.function.name}: {exc}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # раунды закончились, а модель всё ещё зовёт инструменты — делаем
        # последний запрос без tools, чтобы получить хоть какой-то ответ,
        # а не зависнуть в цикле навсегда
        final_response = await client.chat.completions.create(
            messages=messages,
            model=model,
        )
        return str(final_response.choices[0].message.content)

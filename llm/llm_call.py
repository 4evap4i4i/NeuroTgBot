from openai import AsyncOpenAI
from config import ai
from openai import DefaultAioHttpClient

async def call(data: dict) -> str:
    async with AsyncOpenAI(
            api_key=ai,  # This is the default and can be omitted
            http_client=DefaultAioHttpClient(),
            base_url="https://api.groq.com/openai/v1"
        ) as client:
            chat_completion = await client.chat.completions.create(
                messages=data,
                model="openai/qwen3.8-27b",
            )

    return str(chat_completion.choices[0].message.content)
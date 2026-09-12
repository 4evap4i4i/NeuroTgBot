from openai import AsyncOpenAI
from config import ai
from openai import DefaultAioHttpClient

model = "qwen/qwen3.8-27b"

async def call(data: dict) -> str:
    async with AsyncOpenAI(
            api_key=ai,  # This is the default and can be omitted
            http_client=DefaultAioHttpClient(),
            base_url="https://api.groq.com/openai/v1"
        ) as client:
            chat_completion = await client.chat.completions.create(
                messages=data,
                model=model,
            )

    return str(chat_completion.choices[0].message.content)
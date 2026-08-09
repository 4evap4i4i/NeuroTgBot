from aiogram import Router
from aiogram.types import Message
from openai import AsyncOpenAI, DefaultAioHttpClient

from config import ai

router_message = Router()

@router_message.message()
async def message(message: Message):
    async with AsyncOpenAI(
            api_key=ai,  # This is the default and can be omitted
            http_client=DefaultAioHttpClient(),
            base_url="https://api.groq.com/openai/v1"
        ) as client:
            chat_completion = await client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"{message.text}",
                    }
                ],
                model="openai/gpt-oss-20b",
            )
            await message.answer(str(chat_completion.choices[0].message.content))
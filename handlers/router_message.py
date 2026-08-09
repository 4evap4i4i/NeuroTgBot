from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from openai import AsyncOpenAI, DefaultAioHttpClient

from config import ai

router_message = Router()

@router_message.message(Command("say"))
async def message(message: Message, state: FSMContext, command: CommandObject):
    try:
        data = await state.get_value("context")
    except AttributeError:
        data = []
        
    data.update({"role": "user", "content": f"{command.args}"})

    async with AsyncOpenAI(
            api_key=ai,  # This is the default and can be omitted
            http_client=DefaultAioHttpClient(),
            base_url="https://api.groq.com/openai/v1"
        ) as client:
            chat_completion = await client.chat.completions.create(
                messages=data,
                model="openai/gpt-oss-20b",
            )
            await message.answer(str(chat_completion.choices[0].message.content))

            data.update({"role": "assistant", "content": f"{chat_completion.choices[0].message.content}"})
    await state.update_data(context=data)
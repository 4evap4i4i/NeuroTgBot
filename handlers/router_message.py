from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from llm.chat_toole import save_message, get_history
from llm.llm_call import call

router_message = Router()


@router_message.message(Command("say"))
async def message(message: Message, command: CommandObject) -> None:
    text = command.args
    if not text:
        await message.answer("Напиши текст после команды, например:\n/say Привет!")
        return

    await save_message(message.from_user.id, "user", content=text)
    data = await get_history(message.from_user.id)

    answer = await call(data, message.from_user.id)
    await message.answer(answer)
    await save_message(message.from_user.id, "assistant", str(answer))

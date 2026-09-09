from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from llm.chat_toole import save_message, get_history
from llm.llm_call import call

router_message = Router()

@router_message.message(Command("say"))
async def message(message: Message, command: CommandObject):

    await save_message(message.from_user.id, "user", str(CommandObject.args))
    data = await get_history()
    
    answer = await call(data)
    await message.answer(answer)
    await save_message(message.from_user.id, "assistant", str(answer))
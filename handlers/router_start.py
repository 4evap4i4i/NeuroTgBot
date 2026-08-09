from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router_start = Router()

@router_start.message(CommandStart())
async def start(message: Message):
    await message.answer(message.text)
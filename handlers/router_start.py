from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from states import State_context

router_start = Router()

@router_start.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(State_context.context)
    await message.answer(message.text)
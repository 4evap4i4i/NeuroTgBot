from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tools.get_document import get_user_documents

router_files = Router()

CALLBACK_PREFIX = "doc:"


@router_files.message(Command("files"))
async def show_files_menu(message: Message) -> None:
    documents = await get_user_documents(message.from_user.id)

    if not documents:
        await message.answer("У тебя пока нет загруженных PDF. Просто пришли файл сюда.")
        return

    builder = InlineKeyboardBuilder()
    for doc in documents:
        label = doc["filename"] or f"Документ #{doc['id']}"
        builder.row(
            InlineKeyboardButton(
                text=label,
                callback_data=f"{CALLBACK_PREFIX}{doc['id']}",
            )
        )

    await message.answer("Твои PDF-файлы:", reply_markup=builder.as_markup())


@router_files.callback_query(lambda c: c.data and c.data.startswith(CALLBACK_PREFIX))
async def select_file(callback: CallbackQuery) -> None:
    document_id = callback.data.removeprefix(CALLBACK_PREFIX)

    await callback.answer()
    await callback.message.answer(
        f"Выбран документ ID: {document_id}.\n"
        f"Спроси про него через /say, например:\n"
        f"/say Что написано в документе {document_id}?"
    )

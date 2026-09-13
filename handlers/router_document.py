from aiogram import F, Router
from aiogram.types import Message

from tools.get_document import save_document

router_document = Router()

ALLOWED_MIME = "application/pdf"


@router_document.message(F.document)
async def handle_document(message: Message) -> None:
    doc = message.document

    if doc.mime_type != ALLOWED_MIME:
        await message.answer("Пока умею работать только с PDF-файлами.")
        return

    file = await message.bot.get_file(doc.file_id)
    file_bytes_io = await message.bot.download_file(file.file_path)

    document_id = await save_document(
        user_id=message.from_user.id,
        filename=doc.file_name or "document.pdf",
        content=file_bytes_io.read(),
    )

    await message.answer(
        f"Документ сохранён, ID: {document_id}.\n"
        f"Теперь спроси про него через /say, упомянув этот ID, например:\n"
        f"/say Что написано в документе {document_id}?"
    )

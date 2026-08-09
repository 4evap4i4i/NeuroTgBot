import os

from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
Bot = Bot(token=os.getenv("TOKEN"))
db_url = os.getenv("NEON")
webhook = os.getenv("WEBHOOK")
render_url = os.getenv("RENDER_EXTERNAL_URL")
ai = os.getenv('AI_TOKEN')
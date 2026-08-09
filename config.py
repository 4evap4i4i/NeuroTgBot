import os

from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

Bot = Bot(token=os.getenv("TOKEN"))
webhook = os.getenv("WEBHOOK")
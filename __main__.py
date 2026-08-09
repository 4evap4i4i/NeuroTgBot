import os

from aiogram import Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config import Bot, render_url, webhook
from handlers import routers

dp = Dispatcher()
for r in routers:
    dp.include_router(r)

async def on_startup(bot):
    await bot.set_webhook(f"{render_url}/webhook", secret_token=webhook)

app = web.Application()
dp.startup.register(on_startup)
SimpleRequestHandler(dispatcher=dp, bot=Bot, secret_token=webhook).register(app, path="/webhook")
setup_application(app, dp, bot=Bot)

web.run_app(app, host="0.0.0.0", port=os.getenv("PORT"))
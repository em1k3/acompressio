import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer

from bot.config import BOT_TOKEN
from bot.handlers import router


async def main():
    print("ENTERED MAIN")

    session = AiohttpSession(
        api=TelegramAPIServer.from_base('http://localhost:8081')
    )

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    dp.include_router(router)
    print("START POLLING")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

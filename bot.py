import asyncio
import logging
import datetime
import sys

import aiogram.exceptions
import oracledb
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config_data.config import *
from database.oracle_db import get_shifts, date2, read_shifts
from handlers import user_handlers
from aiogram.client.session.aiohttp import AiohttpSession
from database.db import db_start, cur
from database.oracle_db import maintain_connection

PROXY_URL = load_proxy()
session = AiohttpSession(proxy=PROXY_URL)
logger = logging.getLogger(__name__)
storage = MemoryStorage()
config: Config = load_config()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML', session=session)


# Функция отправки напоминаний пользователям

async def check():
    logger.info('Reminder started!')
    while True:
        cur.execute("SELECT * FROM accounts;")
        reminders_results = cur.fetchall()
        time = datetime.datetime.now().strftime("%H:%M")
        for col in reminders_results:
            try:
                if col[5] == time:
                    await bot.send_message(int(col[1]), f'Напоминание: завтра у Вас '
                                                        f'{str(read_shifts(get_shifts(date2(), col[6])))}')
                    logger.debug(f'user {col[1]} got notifications for {col[5]}')
            except aiogram.exceptions.TelegramBadRequest:
                logger.debug(f'user {col[1]} blocked bot and left channel')
        await asyncio.sleep(60)


# Функция для поддержания коннекта с БД Oracle (Один запрос в 10 минут)
async def oracle():
    while True:
        try:
            maintain_connection()
            logger.info('Oracle connection maintained')
            await asyncio.sleep(600)
        except oracledb.DatabaseError:
            logger.warning('Oracle lost connection! Retry in 10 seconds')
            await asyncio.sleep(10)
            continue


# Синхронизация секунд при запуске бота (чтобы уведомления приходили ровно в 00 секунд)
async def start():
    current_sec = int(datetime.datetime.now().strftime("%S"))
    delay = 60 - current_sec
    if delay == 60:
        delay = 0
    #
    await asyncio.sleep(delay)
    await check()


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        stream=sys.stdout,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    logger.info('Starting bot')

    dp = Dispatcher(storage=storage)

    dp.include_router(user_handlers.router)
    asyncio.ensure_future(start())
    asyncio.ensure_future(oracle())
    await db_start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

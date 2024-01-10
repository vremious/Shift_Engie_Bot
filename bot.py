import asyncio
import logging
import datetime
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config_data.config import Config, load_config
from database.oracle_db import get_shifts, date2, read_shifts
from handlers import user_handlers
from aiogram.client.session.aiohttp import AiohttpSession
from database.db import db_start, cur


# redis = Redis(host='10.248.38.211')
PROXY_URL = 'http://10.248.36.11:3128'
session = AiohttpSession(proxy=PROXY_URL)
# storage = RedisStorage(redis=redis)
logger = logging.getLogger(__name__)
storage = MemoryStorage()
config: Config = load_config()
bot = Bot(token=config.tg_bot.token, parse_mode='HTML', session=session)


async def check():
    print('Reminder started!')
    while True:
        cur.execute("SELECT * FROM accounts;")
        reminders_results = cur.fetchall()
        time = datetime.datetime.now().strftime("%H:%M")
        for x in reminders_results:
            if x[5] == time:
                await bot.send_message(int(x[1]), f'Напоминание: завтра у Вас '
                                                  f'{str(read_shifts(get_shifts(date2(), x[6])))}')
        await asyncio.sleep(60)


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
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    logger.info('Starting bot')

    dp = Dispatcher(storage=storage)

    dp.include_router(user_handlers.router)
    asyncio.ensure_future(start())
    await db_start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

import asyncio
from datetime import datetime

import requests
from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram_calendar import SimpleCalendar, get_user_locale, SimpleCalendarCallback

from bot import PROXY_URL
from keyboards.keyboards import yes_no_kb
from config_data.config import load_secret
from database.db import cmd_start_db, cur, add_tabel, add_notifications, add_notifications_time
from database.oracle_db import get_shifts, read_shifts, get_all_tabels, date2, match_dates
from aiogram.fsm.context import FSMContext
from services.services import input_date

router = Router()
secret = load_secret()
admin_ids = 1
user_dict = {}
session = requests.Session()
session.proxies = {'http': 'http://10.248.36.11:3128',
                   'https': 'http://10.248.36.11:3128',
                   }
API_CATS_URL = 'https://api.thecatapi.com/v1/images/search'
API_DOGS_URL = 'https://random.dog/woof.json'


class FSMFillForm(StatesGroup):
    fill_tabel = State()
    fill_notification = State()
    fill_time = State()


@router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await cmd_start_db(message.from_user.id)
    await message.answer(
        text=f'👋👋👋 Добро пожаловать в Сменобот, {message.from_user.first_name}!\n'
             '⭕Для коректной работы бота нужно заполнить анкету! 👉 /fillform\n'
             'Чтобы узнать, что умеет этот бот 👉 /help'
    )


@router.message(F.text.lower().in_(['/help', 'помощь по работе бота', "помощь по работе бота 🆘"]),
                StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='🤖Бот умеет:🤖\n'
             '🔹Напоминать о предстоящих сменах\n'
             '🔹Показывать график работы на определенную дату\n'

    )
    await asyncio.sleep(1)
    await message.answer(
        text='⭕Для коректной работы бота нужно заполнить анкету!\n👉 /fillform'

    )
    await asyncio.sleep(1)
    await message.answer(text='🔹 Узнать завтрашнюю смену можно с помощью команды /TS\n')
    await asyncio.sleep(1)
    await message.answer(
        text='🔹Узнать смену на любую дату можно отправив боту сообщение в формате "дд.мм.гггг"\n')
    await asyncio.sleep(1)
    await message.answer(
        text='🤓Например чтобы узнать график работы на 23 февраля 2024 года - отправьте боту 23.02.2024')
    await asyncio.sleep(1)
    await message.answer(
        text='🔹Также можно сделать запрос через календарь по нажатию на нижнюю кнопку "Календарь"'
             '\nИли написать "Календарь" либо "Дата" боту)')
    await message.answer(
        text='😸Приятного пользования', reply_markup=yes_no_kb)


@router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(
        text='🤷‍ Отменять нечего. Вы не заполняете пнкету\n\n'
             'Чтобы перейти к заполнению анкеты \n👉 '
             '/fillform'
    )


@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(
        text='❌ Вы прервали заполнение анкеты\n\n'
             'Чтобы снова перейти к заполнению анкеты\n 👉 /fillform'
    )
    # Сбрасываем состояние и очищаем данные, полученные внутри состояний
    await state.clear()


@router.message(F.text.lower().in_(['/fillform', "изменить настройки анкеты ⚙"]), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text=' 🖥 Пожалуйста, введите ваш номер CSP:')
    await state.set_state(FSMFillForm.fill_tabel)


@router.message(StateFilter(FSMFillForm.fill_tabel),
                lambda x: x.text.isdigit() and int(x.text) in get_all_tabels())
async def process_tabel_sent(message: Message, state: FSMContext):
    await state.update_data(tabel=message.text)
    await add_tabel(message.from_user.id, message.text)

    yes_news_button = InlineKeyboardButton(
        text='✔ Да',
        callback_data='1'
    )
    no_news_button = InlineKeyboardButton(
        text='❌ Нет',
        callback_data='0')
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_news_button, no_news_button]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    await message.answer(
        text='🔔 Хотите ли получать напоминание о завтрашней смене?',
        reply_markup=markup
    )

    await state.set_state(FSMFillForm.fill_notification)


@router.message(StateFilter(FSMFillForm.fill_tabel))
async def warning_not_tabel(message: Message):
    await message.answer(
        text='⛔ Номер CSP должен состоять только из цифр ⛔\n\n'
             '❗ Введенного Вами номера нет в базе, попробуйте ещё раз ❗\n')

    await message.answer(text='\nЕсли вы хотите прервать '
                              'заполнение анкеты 👉 /cancel'
                         )


@router.callback_query(StateFilter(FSMFillForm.fill_notification),
                       F.data.in_(['0']))
async def process_notifications_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(notifications=callback.data)
    await add_notifications(callback.from_user.id, int(callback.data))
    await callback.message.delete()
    await callback.message.answer(
        text='😊 Теперь вы можете делать запросы по рабочим сменам\n', reply_markup=yes_no_kb)
    user_dict[callback.from_user.id] = await state.get_data()
    await state.clear()


@router.callback_query(StateFilter(FSMFillForm.fill_notification),
                       F.data.in_(['1']))
async def process_notifications_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(notifications=callback.data)
    await add_notifications(callback.from_user.id, int(callback.data))
    await callback.message.delete()
    await state.set_state(FSMFillForm.fill_time)

    t12_button = InlineKeyboardButton(
        text='12:00',
        callback_data='12:00'
    )
    t13_button = InlineKeyboardButton(
        text='13:00',
        callback_data='13:00'
    )
    t14_button = InlineKeyboardButton(
        text='14:00',
        callback_data='14:00'
    )
    t15_button = InlineKeyboardButton(
        text='15:00',
        callback_data='15:00'
    )
    t16_button = InlineKeyboardButton(
        text='16:00',
        callback_data='16:00'
    )
    t17_button = InlineKeyboardButton(
        text='17:00',
        callback_data='17:00'
    )
    t18_button = InlineKeyboardButton(
        text='18:00',
        callback_data='18:00'
    )
    t19_button = InlineKeyboardButton(
        text='19:00',
        callback_data='19:00'
    )
    t20_button = InlineKeyboardButton(
        text='20:00',
        callback_data='20:00'
    )
    t21_button = InlineKeyboardButton(
        text='21:00',
        callback_data='21:00'
    )
    t22_button = InlineKeyboardButton(
        text='22:00',
        callback_data='22:00'
    )
    t23_button = InlineKeyboardButton(
        text='23:00',
        callback_data='23:00'
    )
    keyboard: list[list[InlineKeyboardButton]] = [
        [t12_button, t13_button, t14_button, t15_button], [t16_button, t17_button, t18_button, t19_button], [t20_button,
                                                                                                             t21_button,
                                                                                                             t22_button,
                                                                                                             t23_button]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await callback.message.answer(
        text='\n🕒🔔 Укажите время в которое хотите получать уведомления:',
        reply_markup=markup)


@router.callback_query(StateFilter(FSMFillForm.fill_time),
                       F.data.in_(['12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00',
                                   '21:00', '22:00', '23:00']))
async def process_notifications_press(callback: CallbackQuery, state: FSMContext):
    await state.update_data(notifications_time=callback.data)
    await add_notifications_time(callback.from_user.id, str(callback.data))
    await callback.message.delete()
    await callback.message.answer(
        text='😊 Теперь вы можете делать запросы по рабочим сменам', reply_markup=yes_no_kb
    )
    user_dict[callback.from_user.id] = await state.get_data()
    await state.clear()


@router.message(StateFilter(FSMFillForm.fill_notification), StateFilter(FSMFillForm.fill_time))
async def warning_not_notification(message: Message):
    await message.answer(
        text='⛔ Пожалуйста, пользуйтесь кнопками '
             'для выбора ответа\n\nЕсли вы хотите прервать '
             'заполнение анкеты 👉 /cancel'
    )


@router.message(F.text.lower().in_(['какая смена завтра', '/ts', 'какая завтра смена 🤔']),  StateFilter(default_state))
async def tomorrow_shift(message: Message):
    cur.execute("SELECT * FROM accounts WHERE tg_id == {user_id}".format(user_id=message.from_user.id))
    print(message.from_user.id)
    try:
        result = cur.fetchall()[0][-1]
        print(result)
        if result:
            await message.answer(f'Завтра - {date2()} \nУ вас {str(read_shifts(get_shifts(date2(), result)))}',
                                 reply_markup=yes_no_kb)
        else:
            await message.answer(f'⛔ Вы не заполнили форму \n👉 /fillform')
    except IndexError:
        await message.answer(f'⛔ Ошибка!\n'
                             f'Нажмите 👉 /start\n'
                             f'Повторите заполнение формы\n👉 /fillform ')


@router.message(F.text.lower().in_(["котик", "кот", "кошечка", "кошка", "котэ", "котейка", "киса", "кисуня", "кисуля",
                                    "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾", "🐱", "🐈", "🐈‍⬛", "кошак"]),
                StateFilter(default_state))
async def tomorrow_shift(message: Message):
    cat_response = session.get(API_CATS_URL)
    cat_link = cat_response.json()[0]['url']
    await message.answer_photo(cat_link)
    await message.answer(f'😸 Вот вам котик ', reply_markup=yes_no_kb)


@router.message(F.text.lower().in_(["песик", "пес", "собака", "собакен", "пёс", "пёсель", "пёсик",
                                    "🐶", "🐕", "🐩", "🦮", "🐕‍", "🐕‍🦺"]),
                StateFilter(default_state))
async def tomorrow_shift(message: Message):
    dog_response = session.get(API_DOGS_URL, proxies=PROXY_URL)
    dog_link = dog_response.json()['url']
    await message.answer_photo(dog_link)
    await message.answer(f'🐶 Вот вам пёсик', reply_markup=yes_no_kb)


@router.message(F.text.lower().in_(["дата", "календарь 🗓️", "календарь"]),
                StateFilter(default_state))
async def calendar_show(message: Message):
    await message.answer(text='Выберите дату', reply_markup=await SimpleCalendar(locale='ru_RU').start_calendar())


@router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    calendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user), show_alerts=True
    )
    calendar.set_dates_range(datetime(2024, 1, 1), datetime(2025, 12, 31))
    selected, date = await calendar.process_selection(callback_query, callback_data)
    if selected:
        print(match_dates(date.strftime("%d.%m.%Y")))
        if match_dates(date.strftime("%d.%m.%Y")):
            cur.execute(
                "SELECT * FROM accounts WHERE tg_id == {user_id}".format(user_id=str(callback_query.from_user.id)))
            try:
                result = cur.fetchall()[0][-1]
                if result:
                    await callback_query.message.answer(f'{date.strftime("%d.%m.%Y")}\nУ вас '
                                                        f'{str(read_shifts(get_shifts(input_date(match_dates(date.strftime("%d.%m.%Y"))), result)))}', reply_markup=yes_no_kb)
                else:
                    await callback_query.message.answer(f'⛔ Вы не заполнили форму \n👉 /fillform')
            except IndexError:
                await callback_query.message.answer(f'⛔ Ошибка!\n'
                                                    f'Нажмите 👉 /start\n'
                                                    f'Повторите заполнение формы\n👉 /fillform ')
        else:
            await callback_query.message.answer(text='🤷 Извините, моя твоя не понимать. 🤷‍', reply_markup=yes_no_kb)


@router.message(StateFilter(default_state))
async def send_echo(message: Message):
    if match_dates(message.text):
        cur.execute("SELECT * FROM accounts WHERE tg_id == {user_id}".format(user_id=message.from_user.id))
        print(message.from_user.id)
        try:
            result = cur.fetchall()[0][-1]
            if result:
                await message.reply(f'\nУ вас '
                                    f'{str(read_shifts(get_shifts(input_date(match_dates(message.text)), result)))}',
                                    reply_markup=yes_no_kb)
            else:
                await message.answer(f'⛔ Вы не заполнили форму \n👉 /fillform')
        except IndexError:
            await message.answer(f'⛔ Ошибка!\n'
                                 f'Нажмите 👉 /start\n'
                                 f'Повторите заполнение формы\n👉 /fillform ')
    else:
        await message.reply(text='🤷 Извините, моя твоя не понимать. 🤷‍', reply_markup=yes_no_kb)

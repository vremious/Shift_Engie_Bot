from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from lexicon.lexicon_RU import LEXICON_RU

button_ts = KeyboardButton(text='Какая завтра смена 🤔')
button_cal = KeyboardButton(text='Календарь 🗓️')
button_ff = KeyboardButton(text="Изменить настройки анкеты ⚙")
button_help = KeyboardButton(text='Помощь по работе бота 🆘')

yes_no_kb_builder = ReplyKeyboardBuilder()
yes_no_kb_builder.row(button_ts, button_cal, button_ff, button_help, width=2)

yes_no_kb: ReplyKeyboardMarkup = yes_no_kb_builder.as_markup(
    one_time_keyboard=False,
    resize_keyboard=False
)

button_1 = KeyboardButton(text=LEXICON_RU['rock'])
button_2 = KeyboardButton(text=LEXICON_RU['scissors'])
button_3 = KeyboardButton(text=LEXICON_RU['paper'])

game_kb = ReplyKeyboardMarkup(
    keyboard=[[button_1],
              [button_2],
              [button_3]],
    resize_keyboard=True
)

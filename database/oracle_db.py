import math
import os
import platform
import oracledb
import datetime
import re
from config_data.config import load_oracle_password, load_oracle_dsn, load_oracle_user
import logging

logger = logging.getLogger(__name__)

# Создание коннекта с БД Oracle (с использованием Thick Client)

# oracledb.init_oracle_client(lib_dir=r"D:\instantclient_11_2")
d = None  # default suitable for Linux
if platform.system() == "Darwin" and platform.machine() == "x86_64":  # macOS
    d = os.environ.get("HOME") + ("/Downloads/instantclient_19_8")
elif platform.system() == "Windows":
    d = r"D:\instantclient_11_2"
oracledb.init_oracle_client(lib_dir=d)



def pool():
    return oracledb.create_pool(
        user=load_oracle_user(),
        password=load_oracle_password(),
        dsn=load_oracle_dsn(),
        port=1521,
        min=1, max=1, increment=0)


pool = pool()


# Функция для поддержания коннекта с базой
def maintain_connection():
    with pool.acquire() as connection:
        cursor = connection.cursor()
        select = cursor.execute("SELECT to_char(SYSDATE, 'HH24:MI:SS | dd.mm.yyyy') FROM DUAL")
        return logger.info(f'ORACLE ANSWER RECEIVED: {[i for i in select][0][0]}')


# Функция "даты завтрашенего дня"
def date2():
    return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")


# Проверка соответствия введения формата даты при ручном запросе
def match_dates(date):
    match = re.fullmatch(r'\d\d\W\d\d\W\d\d\d\d', date)
    if match:
        return date


# функция лля запроса в БД Oracle с рабочими сменами по дате и табельному номеру работника
def get_shifts(date, tabel):
    with pool.acquire() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT AGENT, to_char(DT, 'dd.mm.yyyy'), GNAME, BEGIN1, DUR1, BREAK1, BEGIN2, DUR2, BREAK2, "
            "SIGN, SICK FROM "
            " t_graph_workday3 WHERE "
            "to_char(DT,'dd.mm.yyyy') ='{date_month}' AND AGENT = '{tabel}'"
            " AND STATUS = 1 ".format(date_month=date, tabel=tabel))
        return [i for i in cursor]


# Функция
def get_all_tabels():
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT AGENT FROM t_graph_workday3")
    return [i[0] for i in cursor]


# Функция для расшифровки времени начала рабочего дня, перерывов и конца рабочего дня из данных, полученных от БД Oracle
def read_shifts(results):
    try:
        shift = results[0][2]
        time_start1 = results[0][3]
        if time_start1 == 0:
            time_start1 = 0.00000001
        time_start2 = results[0][6]
        if time_start2 == 0:
            time_start2 = 0.00000001
        time_shift_dur1 = results[0][4]
        time_shift_dur2 = results[0][7]
        time_break1 = results[0][5]
        time_break2 = results[0][8]
        sign = results[0][9]
        sick = results[0][10]

        # Функция для определения типа смены взависимости от полученных ранее данных
        def shift_type():
            if not sick:
                if sign:
                    if sign == 'О':
                        smena = f'выходной - Вы в отпуске ✨ \nХорошего отдыха 🏖'
                        return smena
                    elif sign == 'А':
                        smena = f'нерабочий день - отпуск за свой счёт ✨'
                        return smena
                    else:
                        smena = 'Нерабочий день ✨'
                        return smena
                else:
                    if shift == 'У':
                        if time_start1 and not time_start2:
                            smena = 'утренняя смена ☀'
                            return f'{smena}\nc {time_converter(time_start1)} до {time_converter(shift_time_end1())}'
                        elif time_start1 and time_start2:
                            smena = 'смена утро-ночь ☀🌙'
                            return f'{smena}\nс {time_converter(time_start1)} до {time_converter(shift_time_end1())}\nи' \
                                   f' с {time_converter(time_start2)} до {time_converter(shift_time_end2())}'
                    elif shift == 'Н':
                        if time_start1 and time_start2:
                            smena = 'смена ночь-ночь 🌙🌙'
                            return f'{smena}\nc {time_converter(time_start1)} до {time_converter(shift_time_end1())}\nи ' \
                                   f'с {time_converter(time_start2)} до {time_converter(shift_time_end2())}'
                        elif not time_start1 and time_start2:
                            smena = 'ночная смена 🌙'
                            return f'{smena}\nс {time_converter(time_start2)} до {time_converter(shift_time_end2())}'
                        else:
                            smena = 'отсыпной 😴'
                            return f'{smena}\nпосле смены с {time_converter(time_start1)} ' \
                                   f'до {time_converter(shift_time_end1())}'
                    elif shift == 'Р':
                        smena = 'разрывная смена ⚡️'
                        return f'{smena}\nc {time_converter(time_start1)} до {time_converter(shift_time_end1())} \nи с ' \
                               f'{time_converter(time_start2)} до {time_converter(shift_time_end2())}'
                    elif shift == 'В':
                        smena = 'вечерняя смена 🌇'
                        return f'{smena}\nc {time_converter(time_start1)} до {time_converter(shift_time_end1())}'
                    else:
                        smena = f'выходной ✨\nХорошего отдыха 😉'
                        return smena
            else:
                smena = f'нерабочий день - Вы на больничном 🤒 \nПоправляйтесь скорее 🙏'
                return smena

    except IndexError:
        return f'неверно введена дата ⛔'

    # Функция определения конца рабочего дня для утренней и ночной смены
    def shift_time_end1():
        if time_break1:
            shift_end1 = time_start1 + time_shift_dur1 + time_break1 / 60
        else:
            shift_end1 = time_start1 + time_shift_dur1
        return shift_end1

    # Функция определения конца рабочего дня для разрывной смены
    def shift_time_end2():
        if time_break2:
            shift_end2 = time_start2 + time_shift_dur2 + time_break2 / 60
        else:
            shift_end2 = time_start2 + time_shift_dur2
        return shift_end2

    # Функция-конвертер времени из десятичных дробей в часы:минуты
    def time_converter(time):
        if time != 0:
            leftover_hours = int(time // 1)
            if leftover_hours == 0:
                leftover_hours = '0'
            elif leftover_hours == 24:
                leftover_hours = '0'
            leftover_minutes = math.ceil(float(time % 1 * 60))
            leftover = f'{leftover_hours}:{leftover_minutes:02d}'
            return leftover
    return shift_type()





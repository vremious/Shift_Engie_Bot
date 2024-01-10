import oracledb
import datetime
import re

oracledb.init_oracle_client(lib_dir=r"D:\instantclient_11_2")


def date2():
    return (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d.%m.%Y")


def match_dates(date):
    match = re.fullmatch(r'\d\d\W\d\d\W\d\d\d\d', date)
    if match:
        return date


def get_shifts(date, tabel):
    pool = oracledb.create_pool(
        user="TELCOMM",
        password='TELCOMM',
        dsn="10.3.1.20/ora11g",
        port=1521,
        min=1, max=5, increment=1,
        getmode=oracledb.POOL_GETMODE_NOWAIT)
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT AGENT, to_char(DT, 'dd.mm.yyyy'), GNAME, BEGIN1, DUR1, BREAK1, BEGIN2, DUR2, BREAK2, "
        "SIGN FROM "
        " t_graph_workday3 WHERE "
        "to_char(DT,'dd.mm.yyyy') ='{date_month}' AND AGENT = '{tabel}'"
        " AND STATUS = 1 ".format(date_month=date, tabel=tabel))
    return [i for i in cursor]


def get_all_tabels():
    pool = oracledb.create_pool(
        user="TELCOMM",
        password='TELCOMM',
        dsn="10.3.1.20/ora11g",
        port=1521,
        min=1, max=2, increment=1)
    connection = pool.acquire()
    cursor = connection.cursor()
    cursor.execute("SELECT DISTINCT AGENT FROM t_graph_workday3")
    return [i[0] for i in cursor]


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

        def shift_type():
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
            elif not shift and sign == 'О':
                smena = f'выходной - Вы в отпуске ✨ \nХорошего отдыха 🏖'
                return smena
            elif not shift and sign == 'ОЖ':
                smena = f'нерабочий день - Вы на больничном 🤒 \nПоправляйтесь скорее 🙏'
                return smena
            elif not shift and sign == 'Z':
                smena = f'нерабочий день \nВы уволены, либо только недавно приняты на работу 🗿' \
                        f'\n Уточните график у ответственного лица.'
                return smena
            else:
                smena = f'выходной ✨\nХорошего отдыха 😉'
                return smena
    except IndexError:
        return f'неверно введена дата ⛔'

    def shift_time_end1():
        if time_break1:
            shift_end1 = time_start1 + time_shift_dur1 + time_break1 / 60
        else:
            shift_end1 = time_start1 + time_shift_dur1
        return shift_end1

    def shift_time_end2():
        if time_break2:
            shift_end2 = time_start2 + time_shift_dur2 + time_break2 / 60
        else:
            shift_end2 = time_start2 + time_shift_dur2
        return shift_end2

    def time_converter(time):
        if time != 0:
            leftover_hours = int(time // 1)
            if leftover_hours == 0:
                leftover_hours = '0'
            elif leftover_hours == 24:
                leftover_hours = '0'
            leftover_minutes = int(time % 1 * 60)
            if leftover_minutes == 0:
                leftover_minutes = '00'

            leftover = f'{leftover_hours}:{leftover_minutes}'
            return leftover
        elif time == 0:
            return '0:00'

    return shift_type()

# print(read_shifts(get_shifts(date_tomorrow, 5028)))

# a,b,c = [int(input()) for i in range(3)]
# start_date = datetime.date(c, b, a)
# date_str = start_date.strftime('%d.%m.%Y')
#
# print(date_str)
#
# shifts = {}
# keys = {i[0] for i in get_shifts()}
# for i in keys:
#     values = []
#     for j in get_shifts():
#         if j[0] == i:
#             values.append(j[1:])
#     shifts.update({i: values})
#
# print(shifts)
#
# for tabel, data in shifts.items():
#     for date in data:
#         if tabel == 263 and date[0] == '26.12.2023':
#             print(f'{tabel} - {date}')
#
# redis = redis.Redis(host='10.248.38.211', decode_responses=True)

# def get_cache():
#     cache = redis.get(str(date_tomorrow))
#     if cache:
#         return cache
#     else:
#         redis.set(str(date_tomorrow), str(a))
#
#
# print(get_cache())


# connection.close()
# redis.close()

import sqlite3 as sq

# Определяем переменные для БД Sqlite3
db = sq.connect('tg.db')
cur = db.cursor()


# Создаём БД с таблицей (если БД не существует)
async def db_start():
    cur.execute("CREATE TABLE IF NOT EXISTS accounts("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "tg_id INTEGER, "
                "is_auth BOOL DEFAULT 0, "
                "name STRING,"
                "notifications BOOL DEFAULT 0,"
                "notif_time TEXT,"
                "tabel INTEGER)")

    db.commit()


# Функция для запроса данных пользователя по его telegram id. В случае если пользователя не сущестует - создаётся новая запись в таблицу (регистрация)
async def cmd_start_db(user_id):
    user = cur.execute("SELECT * FROM accounts WHERE tg_id == {key}".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO accounts (tg_id) VALUES ({key})".format(key=user_id))
        db.commit()


# Удалённый функционал, позволявший проверять авторизацию пользователя по паролю при первом запуске бота
async def cmd_authorize(user_id):
    cur.execute("UPDATE accounts SET is_auth = True WHERE tg_id == {key}".format(key=user_id))
    db.commit()


# Запись табельного номера пользователя (выполняется в машине состояний user handlers)
async def add_tabel(user_id, message):
    cur.execute("UPDATE accounts SET tabel=({tabel}) WHERE tg_id == {user_id}".format(tabel=message,
                                                                                      user_id=user_id))
    db.commit()


# Изменение состояния напоминаний (машина состояний в user handlers)
async def add_notifications(user_id, message):
    cur.execute("UPDATE accounts SET notifications=({notif}) WHERE tg_id == {user_id}".format(notif=message,
                                                                                              user_id=user_id))
    db.commit()


# Изменение времени напоминаний (машина состояний в user handlers)
async def add_notifications_time(user_id, message):
    cur.execute("UPDATE accounts SET notif_time='{time}' WHERE tg_id == {user_id}".format(time=message,
                                                                                          user_id=user_id))
    db.commit()

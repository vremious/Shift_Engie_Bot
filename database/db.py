import sqlite3 as sq

db = sq.connect('tg.db')
cur = db.cursor()


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


async def cmd_start_db(user_id):
    user = cur.execute("SELECT * FROM accounts WHERE tg_id == {key}".format(key=user_id)).fetchone()
    if not user:
        cur.execute("INSERT INTO accounts (tg_id) VALUES ({key})".format(key=user_id))
        db.commit()


async def cmd_authorize(user_id):
    cur.execute("UPDATE accounts SET is_auth = True WHERE tg_id == {key}".format(key=user_id))
    db.commit()


async def add_tabel(user_id, message):
    cur.execute("UPDATE accounts SET tabel=({tabel}) WHERE tg_id == {user_id}".format(tabel=message,
                                                                                      user_id=user_id))
    db.commit()


async def add_notifications(user_id, message):
    cur.execute("UPDATE accounts SET notifications=({notif}) WHERE tg_id == {user_id}".format(notif=message,
                                                                                              user_id=user_id))
    db.commit()


async def add_notifications_time(user_id, message):
    cur.execute("UPDATE accounts SET notif_time='{time}' WHERE tg_id == {user_id}".format(time=message,
                                                                                          user_id=user_id))
    db.commit()

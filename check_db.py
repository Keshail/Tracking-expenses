import sqlite3
#Скрипт для проверки БД
def check_db():
    conn = sqlite3.connect("expenses.db")
    cur = conn.cursor()
    print("Таблицы в БД:", cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
    print("\nКатегории:")
    for row in cur.execute("SELECT * FROM categories"):
        print(row)
    print("\nРасходы:")
    for row in cur.execute("SELECT * FROM expenses"):
        print(row)
    conn.close()

if __name__ == "__main__":
    check_db()
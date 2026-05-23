import sqlite3

def run_query(sql, params=()):
    conn = sqlite3.connect("expenses.db")
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows

# 1. Общая сумма расходов за май 2025 (измените месяц при необходимости)
total = run_query("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = '2026-05'")
print("1. Общая сумма за месяц:", total[0][0] if total[0][0] else 0)

# 2. Расходы по категориям за месяц
by_cat = run_query("""
    SELECT c.name, c.monthly_limit, SUM(e.amount) as total
    FROM expenses e
    JOIN categories c ON e.category_id = c.id
    WHERE strftime('%Y-%m', e.date) = '2026-05'
    GROUP BY c.id
""")
print("2. Расходы по категориям:")
for row in by_cat:
    print(f"   {row[0]}: лимит {row[1]}, потрачено {row[2]}")

# 3. Категории с превышением лимита
over = run_query("""
    SELECT c.name, c.monthly_limit, SUM(e.amount) as total
    FROM expenses e
    JOIN categories c ON e.category_id = c.id
    WHERE strftime('%Y-%m', e.date) = '2026-05'
    GROUP BY c.id
    HAVING SUM(e.amount) > c.monthly_limit
""")
print("3. Превышение лимита:")
for row in over:
    print(f"   {row[0]}: лимит {row[1]}, потрачено {row[2]}")

# 4. Топ-3 категории
top = run_query("""
    SELECT c.name, SUM(e.amount) as total
    FROM expenses e
    JOIN categories c ON e.category_id = c.id
    WHERE strftime('%Y-%m', e.date) = '2026-05'
    GROUP BY c.id
    ORDER BY total DESC
    LIMIT 3
""")
print("4. Топ-3 категории:")
for i, row in enumerate(top, 1):
    print(f"   {i}. {row[0]}: {row[1]} руб.")

# 5. Список расходов за период (весь май)
list_exp = run_query("""
    SELECT e.id, c.name, e.amount, e.date, e.note
    FROM expenses e
    JOIN categories c ON e.category_id = c.id
    WHERE e.date BETWEEN '2026-05-01' AND '2026-05-31'
    ORDER BY e.date DESC
""")
print("5. Список расходов за май:")
for row in list_exp:
    print(f"   ID {row[0]}: {row[1]}, {row[2]} руб., {row[3]}, {row[4]}")
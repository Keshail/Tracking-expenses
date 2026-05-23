-- Таблица категорий
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    monthly_limit REAL DEFAULT 0
);

-- Таблица расходов
CREATE TABLE expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    note TEXT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
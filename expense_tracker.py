import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, date
import calendar

DB_NAME = "expenses.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            monthly_limit REAL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            note TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
    """)
    # Добавим начальные категории, если таблица пуста
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO categories (name, monthly_limit) VALUES ('Еда', 15000), ('Транспорт', 5000), ('Кафе/кофе', 3000), ('Развлечения', 8000)")
    conn.commit()
    conn.close()

# ---------- Работа с категориями ----------
def add_category(name, limit):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name, monthly_limit) VALUES (?, ?)", (name, limit))
    conn.commit()
    conn.close()

def get_all_categories():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, name, monthly_limit FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

def update_category_limit(cat_id, new_limit):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE categories SET monthly_limit = ? WHERE id = ?", (new_limit, cat_id))
    conn.commit()
    conn.close()

def delete_category(cat_id):
    # Сначала переназначить расходы? По-простому: запретить удаление, если есть расходы.
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM expenses WHERE category_id = ?", (cat_id,))
    if cur.fetchone()[0] > 0:
        conn.close()
        return False
    cur.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return True

# ---------- Работа с расходами ----------
def add_expense(category_id, amount, date_str, note):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (category_id, amount, date, note) VALUES (?, ?, ?, ?)",
                (category_id, amount, date_str, note))
    conn.commit()
    conn.close()

def get_expenses(start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, c.name, e.amount, e.date, e.note
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.date BETWEEN ? AND ?
        ORDER BY e.date DESC
    """, (start_date, end_date))
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_expense(exp_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()

def get_monthly_summary(year_month):  # year_month в формате YYYY-MM
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.name, c.monthly_limit, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE strftime('%Y-%m', e.date) = ?
        GROUP BY c.id
        ORDER BY total DESC
    """, (year_month,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_total_for_month(year_month):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM expenses WHERE strftime('%Y-%m', date) = ?", (year_month,))
    total = cur.fetchone()[0]
    conn.close()
    return total if total else 0

def get_over_limit_categories(year_month):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.name, c.monthly_limit, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE strftime('%Y-%m', e.date) = ?
        GROUP BY c.id
        HAVING SUM(e.amount) > c.monthly_limit
    """, (year_month,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_top_categories(year_month, limit=3):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        SELECT c.name, SUM(e.amount) as total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE strftime('%Y-%m', e.date) = ?
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT ?
    """, (year_month, limit))
    rows = cur.fetchall()
    conn.close()
    return rows

# ---------- GUI приложение ----------
class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер расходов")
        self.root.geometry("900x600")
        self.root.resizable(True, True)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладки
        self.expenses_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.expenses_frame, text="Расходы")
        self.setup_expenses_tab()

        self.categories_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.categories_frame, text="Категории")
        self.setup_categories_tab()

        self.reports_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.reports_frame, text="Отчёты")
        self.setup_reports_tab()

        self.status = tk.Label(root, text="Готово", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        self.refresh_expenses()
        self.refresh_categories()

    # ---------- Вкладка "Расходы" ----------
    def setup_expenses_tab(self):
        btn_frame = ttk.Frame(self.expenses_frame)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Добавить расход", command=self.add_expense_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить выбранный", command=self.delete_expense).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_expenses).pack(side=tk.LEFT, padx=5)

        # Период фильтрации
        period_frame = ttk.Frame(self.expenses_frame)
        period_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        tk.Label(period_frame, text="Показать расходы за:").pack(side=tk.LEFT, padx=5)
        self.period_var = tk.StringVar(value="current_month")
        ttk.Radiobutton(period_frame, text="Текущий месяц", variable=self.period_var, value="current_month", command=self.refresh_expenses).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(period_frame, text="Произвольный месяц", variable=self.period_var, value="custom", command=self.refresh_expenses).pack(side=tk.LEFT, padx=5)
        self.custom_month_entry = tk.Entry(period_frame, width=10, state='disabled')
        self.custom_month_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(period_frame, text="Выбрать", command=self.refresh_expenses).pack(side=tk.LEFT, padx=5)

        columns = ("id", "category", "amount", "date", "note")
        self.expenses_tree = ttk.Treeview(self.expenses_frame, columns=columns, show="headings")
        self.expenses_tree.heading("id", text="ID")
        self.expenses_tree.heading("category", text="Категория")
        self.expenses_tree.heading("amount", text="Сумма")
        self.expenses_tree.heading("date", text="Дата")
        self.expenses_tree.heading("note", text="Примечание")
        self.expenses_tree.column("id", width=40)
        self.expenses_tree.column("category", width=150)
        self.expenses_tree.column("amount", width=100)
        self.expenses_tree.column("date", width=100)
        self.expenses_tree.column("note", width=200)
        scrollbar = ttk.Scrollbar(self.expenses_frame, orient=tk.VERTICAL, command=self.expenses_tree.yview)
        self.expenses_tree.configure(yscrollcommand=scrollbar.set)
        self.expenses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_expenses(self):
        for row in self.expenses_tree.get_children():
            self.expenses_tree.delete(row)
        year_month = self.get_selected_year_month()
        if not year_month:
            return
        start_date = year_month + "-01"
        last_day = calendar.monthrange(int(year_month[:4]), int(year_month[5:7]))[1]
        end_date = year_month + "-" + str(last_day)
        expenses = get_expenses(start_date, end_date)
        for exp in expenses:
            self.expenses_tree.insert("", tk.END, values=exp)

    def get_selected_year_month(self):
        if self.period_var.get() == "current_month":
            return datetime.now().strftime("%Y-%m")
        else:
            month_str = self.custom_month_entry.get().strip()
            try:
                datetime.strptime(month_str, "%Y-%m")
                return month_str
            except:
                messagebox.showwarning("Ошибка", "Введите месяц в формате ГГГГ-ММ, например 2025-03")
                return None

    def add_expense_dialog(self):
        categories = get_all_categories()
        if not categories:
            messagebox.showwarning("Нет категорий", "Сначала добавьте категории во вкладке «Категории».")
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление расхода")
        dialog.geometry("400x300")
        dialog.grab_set()

        tk.Label(dialog, text="Категория:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        cat_var = tk.StringVar()
        cat_combo = ttk.Combobox(dialog, textvariable=cat_var, width=30)
        cat_combo['values'] = [f"{c[0]} - {c[1]}" for c in categories]
        cat_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Сумма (руб):").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        entry_amount = tk.Entry(dialog)
        entry_amount.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        entry_date = tk.Entry(dialog)
        entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        entry_date.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Примечание:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        entry_note = tk.Entry(dialog, width=40)
        entry_note.grid(row=3, column=1, padx=5, pady=5)

        def save():
            cat_str = cat_var.get()
            amount_str = entry_amount.get()
            date_str = entry_date.get().strip()
            note = entry_note.get().strip()
            if not cat_str or not amount_str or not date_str:
                messagebox.showerror("Ошибка", "Заполните категорию, сумму и дату.")
                return
            try:
                cat_id = int(cat_str.split(" - ")[0])
                amount = float(amount_str)
                datetime.strptime(date_str, "%Y-%m-%d")
            except:
                messagebox.showerror("Ошибка", "Неверный формат числа или даты.")
                return
            add_expense(cat_id, amount, date_str, note)
            self.refresh_expenses()
            dialog.destroy()
            messagebox.showinfo("Успех", "Расход добавлен")
        tk.Button(dialog, text="Сохранить", command=save).grid(row=4, column=1, pady=10)
        tk.Button(dialog, text="Отмена", command=dialog.destroy).grid(row=4, column=0, pady=10)

    def delete_expense(self):
        selected = self.expenses_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите запись для удаления")
            return
        exp_id = self.expenses_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Удаление", "Удалить расход?"):
            delete_expense(exp_id)
            self.refresh_expenses()

    # ---------- Вкладка "Категории" ----------
    def setup_categories_tab(self):
        btn_frame = ttk.Frame(self.categories_frame)
        btn_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="Добавить категорию", command=self.add_category_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать лимит", command=self.edit_limit_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить категорию", command=self.delete_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_categories).pack(side=tk.LEFT, padx=5)

        columns = ("id", "name", "limit")
        self.categories_tree = ttk.Treeview(self.categories_frame, columns=columns, show="headings")
        self.categories_tree.heading("id", text="ID")
        self.categories_tree.heading("name", text="Категория")
        self.categories_tree.heading("limit", text="Месячный лимит")
        self.categories_tree.column("id", width=50)
        self.categories_tree.column("name", width=200)
        self.categories_tree.column("limit", width=150)
        scrollbar = ttk.Scrollbar(self.categories_frame, orient=tk.VERTICAL, command=self.categories_tree.yview)
        self.categories_tree.configure(yscrollcommand=scrollbar.set)
        self.categories_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def refresh_categories(self):
        for row in self.categories_tree.get_children():
            self.categories_tree.delete(row)
        cats = get_all_categories()
        for cat in cats:
            self.categories_tree.insert("", tk.END, values=cat)

    def add_category_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавление категории")
        dialog.geometry("300x150")
        dialog.grab_set()
        tk.Label(dialog, text="Название категории:").pack(pady=5)
        entry_name = tk.Entry(dialog, width=30)
        entry_name.pack(pady=5)
        tk.Label(dialog, text="Месячный лимит (руб):").pack(pady=5)
        entry_limit = tk.Entry(dialog, width=30)
        entry_limit.pack(pady=5)
        def save():
            name = entry_name.get().strip()
            limit_str = entry_limit.get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Введите название")
                return
            try:
                limit = float(limit_str) if limit_str else 0
            except:
                limit = 0
            add_category(name, limit)
            self.refresh_categories()
            dialog.destroy()
            messagebox.showinfo("Успех", "Категория добавлена")
        tk.Button(dialog, text="Сохранить", command=save).pack(pady=10)

    def edit_limit_dialog(self):
        selected = self.categories_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите категорию")
            return
        cat_id = self.categories_tree.item(selected[0])['values'][0]
        current_limit = self.categories_tree.item(selected[0])['values'][2]
        new_limit = simpledialog.askfloat("Лимит", f"Новый лимит для категории (текущий {current_limit}):", parent=self.root)
        if new_limit is not None:
            update_category_limit(cat_id, new_limit)
            self.refresh_categories()

    def delete_category(self):
        selected = self.categories_tree.selection()
        if not selected:
            messagebox.showwarning("Выбор", "Выберите категорию")
            return
        cat_id = self.categories_tree.item(selected[0])['values'][0]
        cat_name = self.categories_tree.item(selected[0])['values'][1]
        if messagebox.askyesno("Удаление", f"Удалить категорию '{cat_name}'? Все расходы с этой категорией будут удалены."):
            if delete_category(cat_id):
                self.refresh_categories()
                self.refresh_expenses()
                messagebox.showinfo("Успех", "Категория удалена")
            else:
                messagebox.showerror("Ошибка", "Невозможно удалить категорию, есть связанные расходы. Сначала удалите расходы.")

    # ---------- Вкладка "Отчёты" ----------
    def setup_reports_tab(self):
        notebook_reports = ttk.Notebook(self.reports_frame)
        notebook_reports.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Месячный отчёт
        month_frame = ttk.Frame(notebook_reports)
        notebook_reports.add(month_frame, text="Месячный отчёт")
        self.setup_monthly_report(month_frame)

        # Превышение лимитов
        limit_frame = ttk.Frame(notebook_reports)
        notebook_reports.add(limit_frame, text="Превышение лимитов")
        self.setup_limit_report(limit_frame)

    def setup_monthly_report(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(frame, text="Месяц (ГГГГ-ММ):").pack(side=tk.LEFT)
        self.report_month_entry = tk.Entry(frame, width=10)
        self.report_month_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Показать", command=self.generate_monthly_report).pack(side=tk.LEFT)

        # Текст для отчёта
        self.report_text = tk.Text(parent, wrap=tk.WORD, font=("Courier New", 10))
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scrollbar.set)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def generate_monthly_report(self):
        year_month = self.report_month_entry.get().strip()
        try:
            datetime.strptime(year_month, "%Y-%m")
        except:
            messagebox.showwarning("Ошибка", "Введите месяц в формате ГГГГ-ММ")
            return
        total = get_total_for_month(year_month)
        categories_summary = get_monthly_summary(year_month)
        top_cats = get_top_categories(year_month)
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, f"ОТЧЁТ ЗА {year_month}\n")
        self.report_text.insert(tk.END, f"Всего расходов: {total:.2f} руб.\n\n")
        self.report_text.insert(tk.END, "Расходы по категориям:\n")
        for row in categories_summary:
            name, limit, spent = row
            spent = spent if spent else 0
            self.report_text.insert(tk.END, f"{name}: {spent:.2f} руб. (лимит {limit:.2f})\n")
        self.report_text.insert(tk.END, f"\nТоп-3 категории:\n")
        for i, (name, spent) in enumerate(top_cats, 1):
            self.report_text.insert(tk.END, f"{i}. {name}: {spent:.2f} руб.\n")

    def setup_limit_report(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5, padx=5)
        tk.Label(frame, text="Месяц (ГГГГ-ММ):").pack(side=tk.LEFT)
        self.limit_month_entry = tk.Entry(frame, width=10)
        self.limit_month_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(frame, text="Показать превышения", command=self.show_over_limit).pack(side=tk.LEFT)

        self.limit_text = tk.Text(parent, wrap=tk.WORD, font=("Courier New", 10))
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.limit_text.yview)
        self.limit_text.configure(yscrollcommand=scrollbar.set)
        self.limit_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_over_limit(self):
        year_month = self.limit_month_entry.get().strip()
        try:
            datetime.strptime(year_month, "%Y-%m")
        except:
            messagebox.showwarning("Ошибка", "Введите месяц в формате ГГГГ-ММ")
            return
        over = get_over_limit_categories(year_month)
        self.limit_text.delete(1.0, tk.END)
        if not over:
            self.limit_text.insert(tk.END, "Нет категорий с превышением лимита.")
        else:
            self.limit_text.insert(tk.END, f"КАТЕГОРИИ С ПРЕВЫШЕНИЕМ ЛИМИТА ЗА {year_month}:\n\n")
            for name, limit, spent in over:
                self.limit_text.insert(tk.END, f"⚠ {name}: потрачено {spent:.2f} руб. при лимите {limit:.2f} руб.\n")
                self.limit_text.insert(tk.END, f"   Перерасход: {spent - limit:.2f} руб.\n\n")

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
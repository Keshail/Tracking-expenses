-- 1. Общая сумма расходов за месяц (например, май 2025)
SELECT SUM(amount)
FROM expenses
WHERE strftime('%Y-%m', date) = '2025-05';

-- 2. Расходы по категориям за месяц с лимитами
SELECT c.name, c.monthly_limit, SUM(e.amount) as total
FROM expenses e
    JOIN categories c ON e.category_id = c.id
WHERE strftime('%Y-%m', e.date) = '2025-05'
GROUP BY c.id;

-- 3. Категории с превышением лимита
SELECT c.name, c.monthly_limit, SUM(e.amount) as total
FROM expenses e
    JOIN categories c ON e.category_id = c.id
WHERE strftime('%Y-%m', e.date) = '2025-05'
GROUP BY c.id
HAVING SUM(e.amount) > c.monthly_limit;

-- 4. Топ-3 категории по затратам
SELECT c.name, SUM(e.amount) as total
FROM expenses e
    JOIN categories c ON e.category_id = c.id
WHERE strftime('%Y-%m', e.date) = '2025-05'
GROUP BY c.id
ORDER BY total DESC
LIMIT 3;

-- 5. Список расходов за период (весь месяц)
SELECT e.id, c.name, e.amount
, e.date, e.note
FROM expenses e
JOIN categories c ON e.category_id = c.id
WHERE e.date BETWEEN '2025-05-01' AND '2025-05-31'
ORDER BY e.date DESC;
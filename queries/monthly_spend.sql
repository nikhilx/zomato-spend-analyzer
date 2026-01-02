.headers on
.mode column
SELECT
    strftime('%Y-%m', order_date) AS month,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY month
ORDER BY month;

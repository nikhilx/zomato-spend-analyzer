.headers on
.mode column

SELECT
    strftime('%Y-%m', order_date) AS month,
    COUNT(*) AS orders
FROM orders
GROUP BY month
ORDER BY month;

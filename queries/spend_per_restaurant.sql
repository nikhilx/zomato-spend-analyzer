.headers on
.mode column

SELECT
    restaurant_name,
    SUM(total_amount) AS total_spent,
    COUNT(*) AS order_count,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
WHERE restaurant_name IS NOT NULL
GROUP BY restaurant_name
ORDER BY total_spent DESC;
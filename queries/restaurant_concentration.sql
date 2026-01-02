.headers on
.mode column

WITH ranked AS (
    SELECT
        restaurant_name,
        COUNT(*) AS orders
    FROM orders
    GROUP BY restaurant_name
),
totals AS (
    SELECT SUM(orders) AS total_orders FROM ranked
)
SELECT
    restaurant_name,
    orders,
    ROUND(orders * 100.0 / (SELECT total_orders FROM totals), 2)
        AS percentage_of_orders
FROM ranked
ORDER BY orders DESC
LIMIT 10;

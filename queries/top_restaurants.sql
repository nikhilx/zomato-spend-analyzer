.headers on
.mode column

SELECT
    restaurant_name,
    COUNT(*) AS orders
FROM orders
GROUP BY restaurant_name
ORDER BY orders DESC
LIMIT 10;

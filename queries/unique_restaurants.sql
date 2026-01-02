.headers on
.mode column

SELECT
    restaurant_name,
    COUNT(*) AS order_count
FROM orders
WHERE restaurant_name IS NOT NULL
GROUP BY restaurant_name
ORDER BY order_count DESC;

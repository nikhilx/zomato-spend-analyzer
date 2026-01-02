.headers on
.mode column

SELECT
    CASE
        WHEN strftime('%w', order_date) IN ('0','6') THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    COUNT(*) AS orders,
    SUM(total_amount) AS total_spent
FROM orders
GROUP BY day_type;

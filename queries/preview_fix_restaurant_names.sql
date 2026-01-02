.headers on
.mode column

SELECT
    id,
    restaurant_name AS old_name,
    TRIM(
        substr(
            restaurant_name,
            1,
            instr(restaurant_name, ' We hope you enjoyed your meal') - 1
        )
    ) AS fixed_name
FROM orders
WHERE restaurant_name LIKE '%We hope you enjoyed your meal%';

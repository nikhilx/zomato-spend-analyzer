UPDATE orders
SET restaurant_name = TRIM(
    substr(
        restaurant_name,
        1,
        instr(restaurant_name, ' We hope you enjoyed your meal') - 1
    )
)
WHERE restaurant_name LIKE '%We hope you enjoyed your meal%'
RETURNING id, restaurant_name;
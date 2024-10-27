WITH 
last_month_swaps as (
    SELECT
    Date_trunc('month',BLOCK_TIMESTAMP) as month,
    POOL_ADDRESS,
    abs(AMOUNT0_USD) as base_amount
    FROM ethereum.uniswapv3.ez_swaps
    WHERE BLOCKCHAIN = 'ethereum'
    AND AMOUNT0_USD IS NOT NULL
    AND BLOCK_TIMESTAMP <= DATEADD(month, -1, '2024-10-05')
                            ),
Top_pools_by30days_volume as (
    SELECT
    DISTINCT 
    month, 
    POOL_ADDRESS,
    SUM(base_amount) as Volume_30days
    FROM last_month_swaps
    GROUP BY 1,2
    ORDER BY 3 DESC
    
                            )
SELECT
DISTINCT
POOL_ADDRESS
FROM Top_pools_by30days_volume
LIMIT {NumberOfpools}
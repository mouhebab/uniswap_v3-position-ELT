SELECT
    DISTINCT 
    DECODED_LOG:pool as pool_address,
    DECODED_LOG:token0 as token0,
    DECODED_LOG:token1 as token1,
    DECODED_LOG:fee as fee,
    DECODED_LOG:tickSpacing as tickspacing
FROM ethereum.core.ez_decoded_event_logs 
WHERE TOPICS[0] = '0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118'
AND DECODED_LOG:pool IN {pool_address}
WITH LiquidityPools_Events as (
        SELECT 
        BLOCK_NUMBER ,
        BLOCK_TIMESTAMP,
        TX_HASH,
        EVENT_INDEX,
        CONTRACT_ADDRESS,
        ORIGIN_FROM_ADDRESS,
        ORIGIN_TO_ADDRESS,
        DATA,
        TOPICS[0] as topic0,
        TOPICS,
        CASE TOPICS[0]::STRING 
        WHEN '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c' THEN 'Burn'
        WHEN '0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde' THEN 'Mint'
        END AS Event_Name,
        '{pool_address}' as pool_address
        FROM ethereum.core.ez_decoded_event_logs log
        WHERE 
        CONTRACT_ADDRESS = lower('{pool_address}') 
        AND TOPICS[0]::STRING IN (
                    '0x0c396cd989a39f4459b5fa1aed6a9a8dcdbc45908acfd67e028cd568da98982c', -- Burn
                    '0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde' -- Mint
                )
        AND TX_STATUS = 'SUCCESS'
        AND EVENT_REMOVED = 'false'
        AND BLOCK_NUMBER > {block_number}
        --AND BLOCK_TIMESTAMP < '2024-10-05'
        ),
        NFTpositions_Events as (
        SELECT 
        BLOCK_NUMBER ,
        BLOCK_TIMESTAMP,
        TX_HASH,
        EVENT_INDEX,
        CONTRACT_ADDRESS,
        ORIGIN_FROM_ADDRESS,
        ORIGIN_TO_ADDRESS,
        DATA,
        TOPICS[0] as topic0,
        TOPICS,
        CASE TOPICS[0]::STRING 
        WHEN '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f' THEN 'IncreaseLiquidity'
        WHEN '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4' THEN 'DecreaseLiquidity'
        END AS Event_Name,
        '{pool_address}' as pool_address
        FROM ethereum.core.ez_decoded_event_logs log
        WHERE TOPICS[0]::STRING IN (
                    '0x3067048beee31b25b2f1681f88dac838c8bba36af25bfb2b7cf7473a5847e35f', -- IncreaseLiquidity
                    '0x26f6a048ee9138f2c0ce266f322cb99228e8d619ae2bff30c67f8dcf9d2377b4' -- DecreaseLiquidity
                )
        AND TX_STATUS = 'SUCCESS'
        AND EVENT_REMOVED = 'false' 
        AND TX_HASH IN (SELECT TX_HASH FROM LiquidityPools_Events)
        ),
        PositionData As (
        SELECT * FROM LiquidityPools_Events
        UNION ALL 
        SELECT * FROM NFTpositions_Events
        ),
    Final_agg as (
        SELECT 
        log.* ,
        tx.POSITION as TX_INDEX,
        tx.BLOCK_HASH as BLOCK_HASH
        From PositionData log
        LEFT JOIN (
            SELECT BLOCK_HASH,TX_HASH, POSITION
            FROM ethereum.core.fact_transactions
            WHERE TX_HASH IN (SELECT TX_HASH FROM LiquidityPools_Events)
                ) tx  ON (log.TX_HASH = tx.TX_HASH) 
        
                ), 
    Final as (
        SELECT 
        BLOCK_HASH,
        BLOCK_NUMBER ,
        TX_HASH,
        TX_INDEX,
        EVENT_INDEX,
        BLOCK_TIMESTAMP,
        CONTRACT_ADDRESS,
        ORIGIN_FROM_ADDRESS,
        ORIGIN_TO_ADDRESS,
        DATA,
        topic0,
        TOPICS,
        Event_Name,
        pool_address
        FROM Final_agg 
        )
    SELECT
    pool_address,
    BLOCK_HASH,  
    BLOCK_NUMBER,
    TX_HASH,
    TX_INDEX,
    CONTRACT_ADDRESS,
    EVENT_INDEX,
    BLOCK_TIMESTAMP,
    ORIGIN_FROM_ADDRESS,
    ORIGIN_TO_ADDRESS,
    TOPIC0,
    EVENT_NAME,
    TOPICS,
    DATA 
    FROM Final
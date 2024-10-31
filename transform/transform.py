from typing import Any, Dict, List
import logging
import time
from transform.transform_utils import *
import pandas as pd
from dotenv import load_dotenv
from load.mongodb_utils import load_mongo_collection,get_mongo_config




keys_path = get_path("secrets/.env.keys")
db_params_path = get_path("config/db_params.yaml")
contractsandtopics_path = get_path("input_params/contractsandtopics.yaml")

flipside_api_key, etherscan_api_key, postgres_key, bigquery_credentials = get_keys(keys_path)
db_configs = load_yaml_file(db_params_path)
contractsandtopics = load_yaml_file(contractsandtopics_path)

(mongo_host,mongo_dbname,
    raw_position_Data_Collection,raw_position_Data_primary_key,
        raw_poolinfo_Data_Collection,raw_poolinfo_Data__primary_key
    ) = get_mongo_config(db_configs)


(pool_contract_address,pool_contract_topics,
    nft_contract_address,nft_contract_topics) = get_contracts_params(contractsandtopics)



columns_dtypes = [
    (['blockhash', 'transactionhash', 'pool_address', 'owner', 'sender', 'pool_event', 'nft_event', 'token0', 'token1'], "string"),
    (['liquidity', 'amount0', 'amount1', 'ticklower', 'tickupper', 'fee', 'tickspacing', 'transactionindex', 'logindex', 'tokenId'], "int"),
    (["block_timestamp"], "timestamp")
]


def load_data(collection_name:str, host:str = mongo_host , database_name:str = mongo_dbname) -> pd.DataFrame:
    return load_mongo_collection(host, database_name, collection_name)

def decode_data(data:pd.DataFrame, UniswapV3Pool_contract_address:str, NonfungiblePositionManager_contract_address:str, 
                            UniswapV3Pool_topic0:List, NonfungiblePositionManager_topic0:List, api_key:str):
    try:
        data['log'] = data.apply(lambda row: aggregate_logs(
                                row,
                                data='data',
                                topics='topics',
                                event_index='event_index',
                                tx_index='tx_index',
                                tx_hash='tx_hash',
                                contract_address='contract_address',
                                block_hash='block_hash',
                                block_number='block_number'
                                ), axis=1)

        UniswapV3Pool_contract_instance = create_contract_instance(contract_address=UniswapV3Pool_contract_address,api_key=api_key)
        NonfungiblePositionManager_contract_instance = create_contract_instance(contract_address=NonfungiblePositionManager_contract_address,api_key=api_key)
        mask_pool = data['topic0'].isin(UniswapV3Pool_topic0)
        mask_nft = data['topic0'].isin(NonfungiblePositionManager_topic0)
        data.loc[mask_pool, "Processed_Log"] = data.loc[mask_pool].apply(lambda row: decode_event(row, UniswapV3Pool_contract_instance, 'event_name', 'log'), axis=1)
        data.loc[mask_nft, "Processed_Log"] = data.loc[mask_nft].apply(lambda row: decode_event(row, NonfungiblePositionManager_contract_instance, 'event_name', 'log'), axis=1)
        data['args'] = data['Processed_Log'].apply(lambda x: x.get('args'))
        logging.info("Data Decoded sucessfully!")
        return data
    except Exception as e:
        logging.error(f" Data decoding Error: {e}")

def get_pool_curated_data(positions_data_decoded,pool_topic0):
    pool_data = positions_data_decoded[positions_data_decoded['topic0'].isin(pool_topic0)][['block_timestamp',"pool_address",'Processed_Log']].reset_index(drop=True)
    normalized_processed_log_pool = pd.json_normalize(pool_data['Processed_Log'])
    normalized_processed_log_pool.columns = normalized_processed_log_pool.columns.str.replace(r'^args\.', '', regex=True)
    pool_normalized_data = pd.concat([pool_data[['block_timestamp',"pool_address"]], normalized_processed_log_pool], axis=1)
    pool_curated_data = pool_normalized_data[['block_timestamp','blockHash','transactionHash','blockNumber','transactionIndex','logIndex','pool_address','owner','sender','amount','amount0','amount1','event','tickLower','tickUpper']].rename(columns={"event": "pool_event",'amount':"liquidity"})
    return pool_curated_data

def get_nft_curated_data(positions_data_decoded,nft_topic0):
    nft_data = positions_data_decoded[positions_data_decoded['topic0'].isin(nft_topic0)][['block_timestamp',"pool_address",'Processed_Log']].reset_index(drop=True)
    normalized_processed_log_nft = pd.json_normalize(nft_data['Processed_Log'])
    normalized_processed_log_nft.columns = normalized_processed_log_nft.columns.str.replace(r'^args\.', '', regex=True)
    nft_normalized_data = pd.concat([nft_data[['block_timestamp',"pool_address"]], normalized_processed_log_nft], axis=1)
    nft_curated_data = nft_normalized_data[['blockHash','blockNumber','transactionHash','pool_address','liquidity','amount0','amount1','event','tokenId']].rename(columns={"event": "NFT_event"})
    return nft_curated_data

def get_position_curated_data(pool_curated_data, nft_curated_data,pool_info_data_raw,columns_dtypes):
    position_curated_data_prefinal = pool_curated_data.merge(nft_curated_data,how='left',left_on=['blockHash','blockNumber','transactionHash','pool_address','liquidity','amount0','amount1'],right_on=['blockHash','blockNumber','transactionHash','pool_address','liquidity','amount0','amount1'])
    pool_info_curated_data = pool_info_data_raw[['pool_address','token0','token1','fee','tickspacing']]
    position_curated_data = position_curated_data_prefinal.merge(pool_info_curated_data,how='left',left_on=['pool_address'],right_on=['pool_address'])
    position_curated_data.dropna(subset="tokenId",inplace=True)
    position_curated_data = lowercase_columns_df(position_curated_data)
    position_curated_data = enforce_data_type(position_curated_data,columns_dtypes)
    return position_curated_data



def main():
    positions_data_raw = load_data(collection_name=raw_position_Data_Collection)
    pool_info_data_raw = load_data(collection_name=raw_poolinfo_Data_Collection)
    positions_data_decoded = decode_data(data=positions_data_raw, 
                                                    UniswapV3Pool_contract_address=pool_contract_address, NonfungiblePositionManager_contract_address=nft_contract_address,
                                                        UniswapV3Pool_topic0= pool_contract_topics, NonfungiblePositionManager_topic0=nft_contract_topics,api_key=etherscan_api_key)
    
    pool_curated_data = get_pool_curated_data(positions_data_decoded=positions_data_decoded,pool_topic0=pool_contract_topics)
    nft_curated_data=get_nft_curated_data(positions_data_decoded=positions_data_decoded,nft_topic0=nft_contract_topics)
    position_curated_data = get_position_curated_data(pool_curated_data=pool_curated_data,nft_curated_data=nft_curated_data,pool_info_data_raw=pool_info_data_raw,columns_dtypes=columns_dtypes)
    
    return position_curated_data
if __name__ == "__main__":
    main()
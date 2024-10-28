import requests
import os
from flipside import Flipside
from io import StringIO
from typing import Any, Dict, List
import logging
import sys
import time
import yaml
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from extract.extract_utils import *
from extract.flipside_extract import extract_flipsidecrypto_data

keys_path = get_path("secrets/.env.keys")
pool_list_path = get_path('extract/input_params/pools.yaml')
prevous_blocknumber_path = get_path("extract/input_params/blocknumber.db")

flipside_api_key, etherscan_key, postgres_key, bigquery_credentials = get_keys(keys_path)

pool_addresses_list = load_yaml_file(pool_list_path)['Pools']


def get_keys():
    flipside_api_key= os.getenv("flipside_key")
    etherscan_key = os.getenv("etherscan_key")
    postgres_key = os.getenv("postgres_key")
    bigquery_credentials = os.getenv("bigquery_credentials")
    return flipside_api_key, etherscan_key, postgres_key, bigquery_credentials


queries_paths_path = r"extract/flipside_queries/queries_paths.yaml"
queries_paths = load_yaml_file(queries_paths_path)

position_data_query, pool_info_query, pool_search_query = get_flipside_queries(queries_paths)

def fetch_positionsData(pool_address:str, query:str, prevous_blocknumber_path:str,api_key=flipside_api_key) -> List:   
    try: 
        block_number = get_start_block_number(pool_address,prevous_blocknumber_path)
        logging.info(f"querying data for pool : {pool_address} starting from block number: {block_number}")
        params = {'pool_address': pool_address,'block_number':block_number} 
        position_data = extract_flipsidecrypto_data(query=query ,params = params, api_key=api_key)
        update_start_block_number(position_data,pool_address,prevous_blocknumber_path)
        logging.info(f"position data fetched successfully for pool {pool_address}, Rows Retrieved: {len(position_data)}")
    except Exception as e:
        logging.error(f"Error fetching position data for pool: {pool_address}: {e}")
    return position_data

def fetch_positionData_all_pools(pool_addresses:list,query:str,prevous_blocknumber_path:str) -> List:
    all_results = {}
    try:   
        with ThreadPoolExecutor() as executor:
            future_to_pool = {executor.submit(fetch_positionsData, pool,query,prevous_blocknumber_path): pool for pool in pool_addresses}
            for future in as_completed(future_to_pool):
                pool = future_to_pool[future]
                result = future.result()
                all_results[pool] = result
    except Exception as e:
        logging.error(f"error in  fetching  positionData: {e}")

    flattened_values = [item for sublist in all_results.values() for item in sublist]           
    return flattened_values



def fetch_poolsinfo(pools:List,query:str,api_key:str=flipside_api_key)->List:
    pools_list_tuple = normalize_pool_addresses(pools)
    params= {'pool_address': pools_list_tuple}
    pool_info_data = extract_flipsidecrypto_data(query, params=params, api_key=api_key)
    return pool_info_data



def main():

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    create_table(prevous_blocknumber_path)
    logging.info("Starting position data extraction for all pools.")
    positionData_results = fetch_positionData_all_pools(
        pool_addresses=pool_addresses_list,
        query=position_data_query,
        prevous_blocknumber_path=prevous_blocknumber_path
    )

    poolsinfo_results = fetch_poolsinfo(
        pool_addresses_list,pool_info_query)

if __name__ == "__main__":
    main()


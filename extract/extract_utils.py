import os
from typing import Any, List,Tuple
import logging
import json
import yaml
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

    

def get_db_connection(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    return conn


def create_table(file_path):
    try:
        conn = get_db_connection(file_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS block_numbers (
                pool TEXT PRIMARY KEY,
                block_number INTEGER
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error creating table: {e}")
    finally:
        conn.close()


def get_start_block_number(pool: str, file_path: str, default: int = 0) -> int:
    try:
        conn = get_db_connection(file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT block_number FROM block_numbers WHERE pool = ?", (pool,))
        result = cursor.fetchone()

        if result:
            return result[0]
        else:
            logging.warning(f"Pool '{pool}' not found. Returning default value: {default}")
            return default
    except sqlite3.Error as e:
        logging.error(f"Error reading block number for pool '{pool}': {e}")
        return default
    finally:
        conn.close()

def update_start_block_number(data: List, pool:str,file_path: str) -> None:
    try:
        conn = get_db_connection(file_path)
        cursor = conn.cursor()       
        if data:
            last_block_number = max(event['block_number'] for event in data)
            cursor.execute("""
                INSERT OR REPLACE INTO block_numbers (pool, block_number) 
                VALUES (?, ?)
            """, (pool, last_block_number))
            logging.debug(f"Block number for pool {pool} updated to {last_block_number}")
        else:
            logging.warning(f"No events found for pool {pool}, skipping.")

        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error updating block numbers: {e}")
    finally:
        conn.close()


def normalize_pool_addresses(pool_addresses_list:List) -> tuple:
    try:
        pool_addresses_tuple = tuple(pool_addresses_list)
        if len(pool_addresses_tuple) == 1:
            pool_addresses_tuple = (pool_addresses_tuple[0], pool_addresses_tuple[0])
        return pool_addresses_tuple
    except Exception as e:
        logging.error(f"Error Normalizing addresess list: {e}")


def env_variables(config_variable: str, field: str) -> str:
    config = json.loads(os.getenv(config_variable)) 
    return config[field] 

def load_yaml_file(file_path:str)->Any:
    with open(file_path, "r") as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data

def read_file(file_path:str)->str:
    with open(file_path, "r") as file:
        file_content = file.read()
    return file_content

def get_flipside_queries(queries_paths)-> Tuple:

    positions_query_path = queries_paths['positions_query']
    positions_query = read_file(positions_query_path)

    pool_info_query_path = queries_paths['pool_info_query']
    pool_info_query = read_file(pool_info_query_path)

    pool_search_query_path = queries_paths['pool_search_query']
    pool_search_query = read_file(pool_search_query_path)

    return positions_query, pool_info_query, pool_search_query


def get_path(relative_path: str) -> Path:
    PROJECT_ROOT = Path(__file__).parent.parent
    return PROJECT_ROOT.joinpath(relative_path)


def get_keys(keys_path:str)->Tuple:
    load_dotenv(keys_path)
    flipside_api_key= os.getenv("flipside_key")
    etherscan_key = os.getenv("etherscan_key")
    postgres_key = os.getenv("postgres_key")
    bigquery_credentials = os.getenv("bigquery_credentials")
    return flipside_api_key, etherscan_key, postgres_key, bigquery_credentials



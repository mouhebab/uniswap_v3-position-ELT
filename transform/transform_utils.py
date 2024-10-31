import os
from typing import Any, List,Tuple,Dict
import logging
import json
import yaml
import requests
from web3 import Web3
from web3.contract import Contract
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path


def load_yaml_file(file_path:str)->Any:
    with open(file_path, "r") as file:
        yaml_data = yaml.safe_load(file)
    return yaml_data


def get_ABI(contract_address:str, api_key:str) -> dict[str, any]:
    url = "https://api.etherscan.io/v2/api"
    params = {
        "chainid": 1,
        "module": "contract",
        "action": "getabi",
        "address": contract_address,
        "apikey": api_key
    }

    try:
        response = requests.get(url, params=params)
        return json.loads(response.json()['result'])
    except Exception as e:
        logging.error(f" request Error: {e}")


def create_contract_instance(contract_address:str,api_key:str)-> Contract:
    try:
        web3 = Web3()
        ABI = get_ABI(contract_address,api_key)
        logging.debug(f"contract ABI: {ABI}")
        contract_instance = web3.eth.contract(abi=ABI)
        logging.debug(f"contract instance: {contract_instance}")
        logging.info("contract instance created successfully")
        return contract_instance
    except Exception as e:
        logging.error(f" request Error: {e}")


def aggregate_logs(df:pd.DataFrame, data:str, topics:str, event_index:int, tx_index:int, tx_hash:str, contract_address:str, block_hash:str, block_number:int) -> dict:
    try:
        log = {
        'data': df[str(data)],
        'topics': df[str(topics)],
        'logIndex': df[event_index],
        'transactionIndex': df[tx_index],
        'transactionHash': df[tx_hash],
        'address': df[str(contract_address)],
        'blockHash': df[str(block_hash)],
        'blockNumber': df[block_number]
                }
        logging.debug('logs aggregated sucessfully!')
        return log
    except Exception as e:
        logging.error(f"Error in log aggregation: {e}")

def decode_event(df:pd.DataFrame, contract_instance:Contract, event_column:str, log_column:str)->dict:
    try:
        event = getattr(contract_instance.events, df[event_column])()
        processed_log = event.process_log(df[log_column])
        logging.debug('log processed sucessfully!')
        return processed_log
    except AttributeError:
        logging.error(f"Error: Event {df[event_column]} does not exist.")
    except Exception as e:
        logging.error(f"Error processing log for event {df[event_column]}: {e}")

def lowercase_columns_df(data:pd.DataFrame) -> pd.DataFrame:
    df = data.copy()
    df.columns = df.columns.str.lower()
    return df

def enforce_data_type(data: pd.DataFrame, columns_and_types: list[tuple[list[str], str]]) -> pd.DataFrame:
    df = data.copy()
    for columns, dtype in columns_and_types:
        for column in columns:
            if column in df.columns:
                if dtype == "timestamp":
                    df[column] = pd.to_datetime(df[column], utc=True)
                else:
                    df[column] = df[column].astype(dtype)
    return df


def get_contracts_params(contracts_params: Dict) -> Tuple:
     
        UniswapV3Pool_address = contracts_params['UniswapV3Pool']['address']
        UniswapV3Pool_topics = contracts_params['UniswapV3Pool']['topics']
        NonfungiblePositionManager_address= contracts_params['NonfungiblePositionManager']['address']
        NonfungiblePositionManager_topics = contracts_params['NonfungiblePositionManager']['topics']

        return UniswapV3Pool_address,UniswapV3Pool_topics,NonfungiblePositionManager_address,NonfungiblePositionManager_topics

def get_keys(keys_path:str)->Tuple:
    load_dotenv(keys_path)
    flipside_api_key= os.getenv("flipside_key")
    etherscan_key = os.getenv("etherscan_key")
    postgres_key = os.getenv("postgres_key")
    bigquery_credentials = os.getenv("bigquery_credentials")
    return flipside_api_key, etherscan_key, postgres_key, bigquery_credentials


def get_path(relative_path: str) -> Path:
    PROJECT_ROOT = Path(__file__).parent.parent
    return PROJECT_ROOT.joinpath(relative_path)
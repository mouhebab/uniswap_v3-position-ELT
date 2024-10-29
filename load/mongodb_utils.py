from pymongo import MongoClient, UpdateOne
import logging
import pandas as pd
import numpy as np
from typing import Any, Dict, List,Tuple
import requests


def get_mongo_config(db_configs: Dict) -> Tuple:
    try:
        mongo = db_configs['Mongo']
        mongo_host = mongo["Mongo_Config"]['host_url']
        mongo_dbname = mongo["Mongo_Config"]['db_name']
        raw_position_Data_Collection = mongo["Mongo_Collections"]["raw_position_Data_Collection"]['collection_name']
        raw_position_Data_primary_key = mongo["Mongo_Collections"]["raw_position_Data_Collection"]['primary_key']
        raw_poolinfo_Data_Collection = mongo["Mongo_Collections"]["raw_poolinfo_Data_Collection"]['collection_name']
        raw_poolinfo_Data__primary_key = mongo["Mongo_Collections"]["raw_poolinfo_Data_Collection"]['primary_key']
        return mongo_host,mongo_dbname,raw_position_Data_Collection, raw_position_Data_primary_key,raw_poolinfo_Data_Collection,raw_poolinfo_Data__primary_key
    except Exception as e:
        logging.error(f"Mongo Config Error: {e}")

def initialize_mongo_db(host:str, database_name:str):
    try:
        client = MongoClient(host)
        db = client[database_name]
    except Exception as e:
        logging.error(f"Error in initiating Mongo client: {e}")    
    return client,db


def bulk_upsert_mongodb(host:str, database_name:str, collection_name:str, data:List, unique_keys:List) -> Any:
    try:
        client, db = initialize_mongo_db(host, database_name)
        if client is None or db is None:
            logging.error("Failed to connect to MongoDB.")
            return None
        else: 
            logging.debug('Connected to mongoDB successfully')
            

        collection = db[collection_name]

        
        bulk_operations = [
            UpdateOne(
                {key: record[key] for key in unique_keys if key in record}, 
                {"$setOnInsert": record},
                upsert=True
            )
            for record in data
        ]

        result = None
        if bulk_operations:
            result = collection.bulk_write(bulk_operations, ordered=False)
            logging.debug(f"Inserted: {result.upserted_count}")
            if result.upserted_count > 0:
                logging.info("Mongodb: Data inserted successfully!")
            else: 
                logging.info("Mongodb: No new data to be inserted!")
        return result
    
            
    
    except Exception as e:
        logging.error(f"Error in bulk upsert operation: {e}")
        return None

    finally:
        if client:
            client.close()
            logging.debug("MongoDB: Client closed!") 


def load_mongo_collection(host:str, database_name:str, collection_name:str) -> pd.DataFrame:
    try:
        client, db = initialize_mongo_db(host, database_name)
        if client is None or db is None:
            logging.error("Failed to connect to MongoDB.")
            return None
        else: 
            logging.debug('Connected to mongoDB successfully')
            

        collection = db[collection_name]

        collection_data_df = pd.DataFrame(list(collection.find()))

        return collection_data_df

    except Exception as e:
        logging.error(f"Error in loading data from mongo: {e}")
        return None
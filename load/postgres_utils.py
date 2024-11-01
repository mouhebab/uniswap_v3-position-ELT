import psycopg2
from psycopg2.extras import execute_values
import logging
import pandas as pd
import numpy as np
from typing import Any, Dict, List,Tuple
import requests
from io import StringIO
import yaml
import os

pg_table_query_path= r"load\pg_queries\positions_data_table_creation_query.sql"

def format_query(query_path: str, params: Dict) -> str:
    try:
        with open(query_path, "r") as file:
            query = file.read()
        formatted_query = query.format(**params)
        return formatted_query
    except Exception as e:
        raise ValueError(f"format query error: {e}")


def get_postgres_config(db_configs: Dict,postgres_key:str) -> Tuple:
    try:
        pg_config= db_configs['postgres']['postgres_config']
        pg_table= db_configs['postgres']['postgres_table']
        pg_host = pg_config['host']
        pg_port = pg_config['port']
        pg_user = pg_config['user']
        pg_dbname= pg_config['db_name']
        pg_table_name = pg_table['table_name']
        return postgres_key,pg_host,pg_port,pg_user,pg_dbname,pg_table_name
    except Exception as e:
        logging.error(f"postgres config error: {e}")


def initiate_connection_postgres(dbname:str,password:str,user:str,host:str,port:str) -> tuple[psycopg2.extensions.connection, psycopg2.extensions.cursor] | None:
    try:
        connection = psycopg2.connect(
        dbname= dbname ,
        user= user ,
        password= password ,
        host= host ,
        port= port 
                        )
        cursor = connection.cursor()
        logging.info("Postgres connection initiated")
        return connection,cursor
    
    except Exception as e:
        logging.error(f"initiate_connection_postgres: Error: {e}")
        return None
    

def create_postgrestable(connection, cursor ,query):
    try:
        cursor.execute(query)
        connection.commit()
        print("create_postgrestable: Table created successfully.")
    except Exception as e:
        print(f" create_postgrestable: Error: {e}")
        return None
    

def load_data_to_postgres(df, table_name,connection,cursor):
    try:
        buffer = StringIO()
        df.to_csv(buffer, index=False, header=False, sep='\t')
        buffer.seek(0)
        cursor.copy_from(buffer, table_name, sep='\t', null="NULL", columns=list(df.columns))
        connection.commit()
        print("Postgres: Data inserted successfully!")
    except Exception as e:
        connection.rollback()
        print(f"Error: {e}")
    return None

def load_to_postgres(data:pd.DataFrame,table_name:str,dbname:str,postgres_password:str,user:str,host:str,port:str,table_query_path:str = pg_table_query_path)->None:
    connextion, cursor =  initiate_connection_postgres(dbname,postgres_password,user,host,port)
    params= {'table': table_name}
    table_query = format_query(table_query_path, params)
    create_postgrestable(connextion, cursor, table_query)
    load_data_to_postgres(data, table_name ,connextion,cursor)
    return None


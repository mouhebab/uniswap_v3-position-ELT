from google.cloud import bigquery
from google.oauth2 import service_account
import logging
import pandas as pd
import numpy as np
from typing import Any, Dict, List,Tuple
import requests
import os
import json


def get_biqguery_config(db_configs: Dict,bigquery_credentials:str) -> Tuple:
    try:
        bigquery_credentials_json = json.loads(bigquery_credentials)
        credentials = service_account.Credentials.from_service_account_info(bigquery_credentials_json)
        bg_configs= db_configs['bigquery']
        bg_table_id = bg_configs["table_id"]
        return credentials,bg_table_id
    except Exception as e:
        logging.error(f"BG config error: {e}")

def load_to_bg(df:pd.DataFrame,credentials:Any,table_id:str) -> None:
    try:
        client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        job = client.load_table_from_dataframe(df, table_id)
        logging.debug(f'Load to BG job result:{job.result()}')
        logging.info(f'data loaded to BG sucessfully!')
        return None
    except Exception as e:
        logging.error(f"BG loading error: {e}")
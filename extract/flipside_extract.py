import requests
from flipside import Flipside
from typing import Any, Dict, List
import logging
import time



def createQueryRun(query : str, api_key:str) -> str :
    
    
    url = "https://api-v2.flipsidecrypto.xyz/json-rpc"

    
    headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
        }

    
    payload = {
        "jsonrpc": "2.0",
        "method": "createQueryRun",
        "params": [
            {
                "resultTTLHours": 1,
                "maxAgeMinutes": 0,
                "sql": query ,
                "tags": {
                    "source": "postman-demo",
                    "env": "test"
                },
                "dataSource": "snowflake-default",
                "dataProvider": "flipside"
            }
        ],
        "id": 1
    }

    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            logging.info("Query run created successfully!")
            logging.debug(response.json())  
            return  response.json()['result']['queryRequest']['queryRunId']
        else:
            raise requests.exceptions.HTTPError(
                f"Unexpected status code: {response.status_code}. Details: {response.text}" )
    except Exception as e:
        logging.error(f" createQueryRun Error: {e}")


def getQueryRun(queryRunId:str , api_key:str) -> str:
    
    url = "https://api-v2.flipsidecrypto.xyz/json-rpc"


    headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key
        }
    
    payload = {
    "jsonrpc": "2.0",
    "method": "getQueryRun",
    "params": [
        {
            "queryRunId": queryRunId
        }
    ],
    "id": 1
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        logging.debug(f'getQueryRun state {response.json()['result']['queryRun']['state']}')
        return response.json()['result']['queryRun']['state']
        
    except Exception as e:
        logging.error(f" getQueryRun Error: {e}")

def queryresult_Pagination(queryRunId:str, api_key:str ,page_size:int = 70000) -> List:
    flipside_instance = Flipside(api_key, "https://api-v2.flipsidecrypto.xyz")   
    current_page_number = 1
    total_pages = 3

    all_rows = []

    while current_page_number <= total_pages:

        try:
            results = flipside_instance.get_query_results(
                queryRunId,
                page_number=current_page_number,
                page_size=page_size         
            )
       
            if results.records:
                total_pages = results.page.totalPages
                all_rows.extend(results.records)
                logging.debug(f"Current page number: {current_page_number} Total Pages: {total_pages}, Rows Retrieved: {len(results.records)}")
            else: 
                logging.warning('No record')
                break

        except Exception as e:
            logging.error(f" Pagination Error: {e}")
            return None
        
        current_page_number += 1

    logging.info(f"Total Pages: {total_pages}, Rows Retrieved: {len(all_rows)}")
        
        
    return all_rows

def format_query(query: str, params: Dict) -> str:
    try:
        formatted_query = query.format(**params)
        return formatted_query
    except Exception as e:
        raise ValueError(f"format query error: {e}")
    


def extract_flipsidecrypto_data(query:str, params: Dict , api_key:str, retry_time:int = 90 ,timeout:int = 600 ) -> List:
    
    try:
        logging.info(f'Start query with params:{params}')
        query = format_query(query,params)
        queryRunId = createQueryRun(query,api_key)

        state = None
        start_time = time.time()

        while state != 'QUERY_STATE_SUCCESS':
            
            state = getQueryRun(queryRunId,api_key)

            if state == 'QUERY_STATE_SUCCESS':
                 break 

            elif state in ['QUERY_STATE_FAILED', 'QUERY_STATE_CANCELED']:
                raise RuntimeError(f"Query execution failed or was canceled. State: {state}")
            
            elif state in ['QUERY_STATE_STREAMING_RESULTS', 'QUERY_STATE_RUNNING', 'QUERY_STATE_READY']:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Query execution exceeded timeout limit.")
                
                logging.info(f"Wainting query excution")
                logging.debug(f"retry after {retry_time} sec")

                time.sleep(retry_time)

            else: raise ValueError(f"Unexpected query state: {state}")

            
        result = queryresult_Pagination(queryRunId,api_key)

    except TimeoutError as e:
        logging.error(f"Timeout Error: {e}")
        return None
    except RuntimeError as e:
        logging.error(f"Runtime Error: {e}")
        return None
    except Exception as e:
        logging.error(f" state Error: {e}")
        return None
    
                
    return result



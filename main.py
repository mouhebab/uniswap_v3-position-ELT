import logging
from extract.extract import main as extract_main

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s — %(levelname)s — %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

def main():
    setup_logging()
    logging.info("ETL Pipeline Started")
    try:
        logging.info("Starting Extraction Step")
        extract_main()
        logging.info("Extraction Completed")


    except Exception as e:
        logging.exception(f"ETL Pipeline Failed: {e}")

if __name__ == "__main__":
    main()
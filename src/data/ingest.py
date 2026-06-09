import logging
from src.core.config import config
from src.core.db import DuckDBEngine

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def ingest_raw_logs():
    """Registers raw .gz telemetry logs as a lazy-evaluated DuckDB view."""
    logging.info("Registering raw logs into DuckDB warehouse...")

    query_raw_view = f"""
    CREATE OR REPLACE VIEW raw_pageviews_with_file AS
    SELECT *, filename
    FROM read_csv(
        '{config.RAW_PATTERN}',
        delim=' ', header=False,
        columns={{
            'project': 'VARCHAR', 'page_title': 'VARCHAR',
            'views': 'BIGINT', 'bytes': 'BIGINT'
        }},
        quote='', escape='', compression='gzip', filename=true, ignore_errors=true
    );
    """

    with DuckDBEngine(read_only=False) as db:
        db.execute(query_raw_view)
    logging.info("Raw logs successfully registered as view.")

if __name__ == "__main__":
    ingest_raw_logs()
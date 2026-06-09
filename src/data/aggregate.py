import logging
from src.core.db import DuckDBEngine

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def build_aggregations():
    """Builds hourly, monthly, and global aggregation tables from the raw view."""
    logging.info("Building hourly project views (Heavy execution)...")
    query_hourly_project = """
    CREATE TABLE IF NOT EXISTS hourly_project_views AS
    SELECT
        project,
        SUBSTR(filename, LENGTH(filename)-15, 10) AS hour_id,
        SUM(views) AS total_views
    FROM raw_pageviews_with_file
    GROUP BY project, hour_id;
    """

    logging.info("Building monthly project traffic table...")
    query_monthly_project = """
    CREATE TABLE IF NOT EXISTS hourly_project_traffic AS
    SELECT project, SUM(total_views) AS total_views
    FROM hourly_project_views
    GROUP BY project;
    """

    logging.info("Building global hourly stability table...")
    query_global_views = """
    CREATE TABLE IF NOT EXISTS hourly_global_views AS
    SELECT hour_id, SUM(total_views) AS global_views
    FROM hourly_project_views
    GROUP BY hour_id
    ORDER BY hour_id;
    """

    with DuckDBEngine(read_only=False) as db:
        db.execute(query_hourly_project)
        db.execute(query_monthly_project)
        db.execute(query_global_views)

    logging.info("Aggregation tables materialized successfully.")

if __name__ == "__main__":
    build_aggregations()
import duckdb
import pandas as pd
from typing import Optional
from src.core.config import config

class DuckDBEngine:
    """
    Context manager for safe, reproducible DuckDB database transactions.
    Automatically handles connecting and closing the database file.
    """
    def __init__(self, db_path: str = str(config.DB_PATH), read_only: bool = False):
        self.db_path = db_path
        self.read_only = read_only
        self.con: Optional[duckdb.DuckDBPyConnection] = None

    def __enter__(self):
        """Establish the database connection when entering the 'with' block."""
        self.con = duckdb.connect(self.db_path, read_only=self.read_only)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure the connection is cleanly closed when exiting the block."""
        if self.con:
            self.con.close()

    def execute(self, query: str) -> None:
        """Executes a SQL query without returning data (e.g., CREATE TABLE)."""
        if not self.con:
            raise ConnectionError("Not connected. Use 'with DuckDBEngine() as db:'")
        self.con.execute(query)

    def fetch_df(self, query: str) -> pd.DataFrame:
        """Executes a SQL query and returns the results as a Pandas DataFrame."""
        if not self.con:
            raise ConnectionError("Not connected. Use 'with DuckDBEngine() as db:'")
        return self.con.execute(query).fetchdf()
"""
DuckDB utility functions.
These include querying DuckDB and listing tables.
"""

import duckdb
import pandas as pd
from pathlib import Path


def duckdb_query(db_path: str, sql: str):
    """
    Execute a query on a DuckDB database and return a standardized result format.

    Args:
        db_path (str): Path to the .duckdb file.
        sql (str): SQL query to execute.

    Returns:
        dict: {
            "success": True, "data": DataFrame
        } or {
            "success": False, "error": error message
        }
    """
    db_file = Path(db_path)
    if not db_file.exists():
        return {
            "success": False,
            "error": f"DuckDB file not found: {db_path}"
        }

    try:
        conn = duckdb.connect(database=str(db_file))
        df = conn.execute(sql).fetchdf()
        conn.close()
        return {
            "success": True,
            "data": df
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }



def list_tables(db_path: str) -> pd.DataFrame:
    """
    List all tables in a DuckDB database.

    Args:
        db_path (str): Path to the .duckdb file.

    Returns:
        pd.DataFrame: DataFrame with a single column 'table_name' listing all tables.
    """
    sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'main';
    """
    return duckdb_query(db_path, sql)

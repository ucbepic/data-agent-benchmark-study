"""
SQLite utility functions.
Provides query interface to SQLite databases and returns pandas DataFrame.
"""

import sqlite3
import pandas as pd
from common_scaffold.config import SQLITE_PATH


def sqlite_query(sql: str, db_path: str = None):
    """
    Execute an SQL query on a SQLite database and return standardized result format.

    Args:
        sql (str): SQL query to execute.
        db_path (str, optional): Path to the SQLite database file.
                                 Defaults to config.SQLITE_PATH.

    Returns:
        dict: {
            "success": True, "data": DataFrame
        } or {
            "success": False, "error": error message
        }
    """

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return {"success": True, "data": df}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}
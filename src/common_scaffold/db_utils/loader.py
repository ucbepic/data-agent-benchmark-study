"""
Unified database loader and query interface.
Provides unified methods to:
  - Ensure database exists (if needed)
  - List tables/collections
  - Query data and return pandas DataFrame
"""

from .mongo_utils import (
    mongo_query,
    ensure_mongo_data,
    list_collections
)
from .sqlite_utils import sqlite_query
from .duckdb_utils import duckdb_query, list_tables
from .mysql_utils import mysql_query, ensure_mysql_data
from .postgres_utils import postgres_query, ensure_postgres_data



def query_db(db_type, **kwargs):
    """
    Query a database and return result as pandas DataFrame.

    Args:
        db_type (str): Database type ('mongo', 'sqlite', 'duckdb', 'mysql', 'postgres')
        kwargs: Database-specific arguments

    Returns:
        pandas.DataFrame
    """
    if db_type == "mongo":
        return mongo_query(**kwargs)
    elif db_type == "sqlite":
        return sqlite_query(**kwargs)
    elif db_type == "duckdb":
        return duckdb_query(**kwargs)
    elif db_type == "mysql":
        return mysql_query(**kwargs)
    elif db_type == "postgres":
        return postgres_query(
            sql=kwargs["sql"],
            db_name=kwargs["db_name"],
            params=kwargs.get("params")
        )
    else:
        return {"success": False, "error": f"Unsupported db_type: {db_type}"}


def ensure_db(db_type, **kwargs):
    """
    Ensure the specified database exists and is initialized.
    Currently implemented for 'mongo', 'mysql', and 'postgres'.

    Args:
        db_type (str): Database type ('mongo', 'mysql', 'postgres')
        kwargs: Database-specific arguments
            For MySQL/Postgres: db_name + sql_file
            For Mongo: db_name + dump_folder
    """
    if db_type == "mongo":
        return ensure_mongo_data(**kwargs)
    elif db_type == "mysql":
        return ensure_mysql_data(**kwargs)
    elif db_type == "postgres":
        return ensure_postgres_data(**kwargs)
    else:
        print(f"✅ No ensure step needed for db_type: {db_type}")



def list_entities(db_type, **kwargs):
    """
    List tables or collections in the specified database.

    Args:
        db_type (str): Database type ('mongo', 'sqlite', 'duckdb', 'mysql', 'postgres')
        kwargs: Database-specific arguments

    Returns:
        pandas.DataFrame or list: Names of tables/collections
    """
    if db_type == "mongo":
        result = list_collections(**kwargs)
    elif db_type == "duckdb":
        result = list_tables(**kwargs)
    elif db_type == "sqlite":
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        result = sqlite_query(sql=sql, **kwargs)
    elif db_type == "mysql":
        sql = "SHOW TABLES;"
        result = mysql_query(sql=sql, **kwargs)
    elif db_type == "postgres":
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        result = postgres_query(sql=sql, **kwargs)
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    if isinstance(result, dict):
        if result.get("success", False):
            return result["data"]
        else:
            raise RuntimeError(f"Query failed in list_entities: {result.get('error')}")

    return result  # e.g., for Mongo or others that return list directly
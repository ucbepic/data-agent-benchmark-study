"""
MySQL utility functions.
These include ensuring the database exists and is populated,
querying MySQL using SQLAlchemy, and checking database existence & tables.
"""

from sqlalchemy import create_engine
import mysql.connector
import pandas as pd
from pathlib import Path
import re
from common_scaffold import config
from dotenv import load_dotenv
import os
MYSQL_CLIENT = os.getenv("MYSQL_CLIENT", "mysql")  
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")

load_dotenv()
def mysql_query(sql: str, db_name: str = None):
    """
    Execute a MySQL query and return standardized result format.

    Args:
        sql (str): SQL query to execute.
        db_name (str): Database name. If None, use config.MYSQL_DB.

    Returns:
        dict: {
            "success": True, "data": DataFrame
        } or {
            "success": False, "error": error message
        }
    """
    db_name = db_name or config.MYSQL_DB

    uri = (
        f"mysql+mysqlconnector://{config.MYSQL_USER}:{config.MYSQL_PASSWORD}"
        f"@{config.MYSQL_HOST}:{config.MYSQL_PORT}/{db_name}"
    )
    engine = create_engine(uri)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(sql, conn)
        return {"success": True, "data": df}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


def database_exists(db_name: str) -> bool:
    """
    Check if a MySQL database exists.

    Args:
        db_name (str): Target database name.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        port=config.MYSQL_PORT
    )
    cursor = conn.cursor()
    cursor.execute("SHOW DATABASES;")
    dbs = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return db_name in dbs


def database_has_tables(db_name: str) -> bool:
    """
    Check if a MySQL database has at least one table.

    Args:
        db_name (str): Target database name.

    Returns:
        bool: True if the database has at least one table, False otherwise.
    """
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        port=config.MYSQL_PORT,
        database=db_name
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    return len(tables) > 0


import subprocess
from pathlib import Path

def import_sql_to_mysql(sql_file: str, db_name: str):
    """
    Import a .sql file into MySQL using the mysql CLI.
    Creates the database if it does not exist.

    Args:
        sql_file (str): Path to the .sql file.
        db_name (str): Target database name.
    """
    conn = mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        port=config.MYSQL_PORT
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
    cursor.close()
    conn.close()

    cmd = [
        MYSQL_CLIENT,
        f"-h{config.MYSQL_HOST}",
        f"-u{config.MYSQL_USER}",
        f"-p{config.MYSQL_PASSWORD}",
        "--default-character-set=utf8mb4",
        db_name
    ]

    print(f"▶️ Importing `{sql_file}` into `{db_name}`...")
    try:
        subprocess.run(cmd, stdin=open(sql_file, 'rb'), check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Import failed: {e}")
        raise
    else:
        print(f"🎉 Successfully imported `{sql_file}` into `{db_name}`.")



def ensure_mysql_data(db_name: str, sql_file: str):
    """
    Ensure that the MySQL database exists and is populated.
    If it does not exist or is empty, import it from the provided .sql file.

    Args:
        db_name (str): Target database name.
        sql_file (str): Path to the .sql file.
    """
    if not database_exists(db_name):
        print(f"⚠️ Database '{db_name}' not found. Importing from '{sql_file}'...")
        import_sql_to_mysql(sql_file, db_name)
    elif not database_has_tables(db_name):
        print(f"⚠️ Database '{db_name}' is empty. Importing from '{sql_file}'...")
        import_sql_to_mysql(sql_file, db_name)
    else:
        print(f"✅ Database '{db_name}' already exists and has tables. No action needed.")

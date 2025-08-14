"""
PostgreSQL utility functions.
These include ensuring the database exists and is populated,
querying PostgreSQL using SQLAlchemy, and checking database existence & tables.
"""

from sqlalchemy import create_engine
from sqlalchemy import text
import psycopg2
import pandas as pd
from pathlib import Path
from common_scaffold import config
import os
import subprocess

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()


def postgres_query(sql: str, db_name: str = None, params: dict = None):
    """
    Execute a PostgreSQL query and return standardized result format.

    Args:
        sql (str): SQL query to execute.
        db_name (str): Database name. If None, use config.PG_DB.
        params (dict, optional): Optional SQL parameters.

    Returns:
        dict: {
            "success": True, "data": DataFrame
        } or {
            "success": False, "error": error message
        }
    """
    db_name = db_name or config.PG_DB

    uri = (
        f"postgresql+psycopg2://{config.PG_USER}:{config.PG_PASSWORD}"
        f"@{config.PG_HOST}:{config.PG_PORT}/{db_name}"
    )
    engine = create_engine(uri)

    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn, params=params)
        return {"success": True, "data": df}
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


###
#def postgres_query(sql: str, db_name: str = None) -> pd.DataFrame:
    db_name = db_name or config.PG_DB
    conn = psycopg2.connect(
        dbname=db_name,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        port=config.PG_PORT
    )
    try:
        df = pd.read_sql(sql, conn)
    finally:
        conn.close()
    return df

###

def database_exists(db_name: str) -> bool:
    """
    Check if a PostgreSQL database exists.

    Args:
        db_name (str): Target database name.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    conn = psycopg2.connect(
        dbname="postgres",  # 连接到系统库
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        port=config.PG_PORT,
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (db_name,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists


def database_has_tables(db_name: str) -> bool:
    """
    Check if a PostgreSQL database has at least one table.

    Args:
        db_name (str): Target database name.

    Returns:
        bool: True if the database has at least one table, False otherwise.
    """
    conn = psycopg2.connect(
        dbname=db_name,
        user=config.PG_USER,
        password=config.PG_PASSWORD,
        host=config.PG_HOST,
        port=config.PG_PORT,
    )
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
    )
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count > 0


def import_sql_to_postgres(sql_file: str, db_name: str):
    """
    Import a .sql file into PostgreSQL using the psql CLI.
    Creates the database if it does not exist.

    Args:
        sql_file (str): Path to the .sql file.
        db_name (str): Target database name.
    """
    # 确保数据库存在
    if not database_exists(db_name):
        print(f"▶️ Creating database '{db_name}'...")
        conn = psycopg2.connect(
            dbname="postgres",
            user=config.PG_USER,
            password=config.PG_PASSWORD,
            host=config.PG_HOST,
            port=config.PG_PORT,
        )
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(
            f'CREATE DATABASE "{db_name}" WITH ENCODING = \'UTF8\' LC_COLLATE=\'C\' LC_CTYPE=\'C\' TEMPLATE=template0;'
        )
        cursor.close()
        conn.close()

    cmd = [
        config.PG_CLIENT,
        f"-h{config.PG_HOST}",
        f"-U{config.PG_USER}",
        "-d", db_name,
        "-f", sql_file
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = config.PG_PASSWORD
    env["PGCLIENTENCODING"] = "UTF8"

    print(f"▶️ Importing `{sql_file}` into `{db_name}`...")
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Import failed: {e}")
        raise
    else:
        print(f"🎉 Successfully imported `{sql_file}` into `{db_name}`.")


def ensure_postgres_data(db_name: str, sql_file: str):
    """
    Ensure that the PostgreSQL database exists and is populated.
    If it does not exist or is empty, import it from the provided .sql file.

    Args:
        db_name (str): Target database name.
        sql_file (str): Path to the .sql file.
    """
    if not database_exists(db_name):
        print(f"⚠️ Database '{db_name}' not found. Importing from '{sql_file}'...")
        import_sql_to_postgres(sql_file, db_name)
    elif not database_has_tables(db_name):
        print(f"⚠️ Database '{db_name}' is empty. Importing from '{sql_file}'...")
        import_sql_to_postgres(sql_file, db_name)
    else:
        print(f"✅ Database '{db_name}' already exists and has tables. No action needed.")

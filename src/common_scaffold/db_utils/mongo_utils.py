"""
MongoDB utility functions.
These include ensuring the database is imported from a dump,
listing collections, and querying collections into a pandas DataFrame.
"""

from pymongo import MongoClient
import pandas as pd
from pathlib import Path
import subprocess
from common_scaffold import config
import json


def database_exists(db_name: str) -> bool:
    """
    Check if a MongoDB database exists.

    Args:
        db_name (str): Target database name.

    Returns:
        bool: True if the database exists, False otherwise.
    """
    client = MongoClient(config.MONGO_URI)
    dbs = client.list_database_names()
    client.close()
    return db_name in dbs


def import_bson_to_mongo(dump_folder: str, db_name: str):
    """
    Import a MongoDB dump folder into the specified database.

    Args:
        dump_folder (str): Path to the dump folder containing .bson and metadata files.
        db_name (str): Target database name.
    """
    dump_path = Path(dump_folder).resolve()
    if not dump_path.exists():
        raise FileNotFoundError(f"Dump folder not found: {dump_folder}")

    print(f"▶️ Importing MongoDB dump from: {dump_path}")
    subprocess.run(
        ["mongorestore", f"--nsInclude={db_name}.*", str(dump_path)],
        check=True
    )
    print(f"🎉 MongoDB dump imported into database '{db_name}'.")


def ensure_mongo_data(db_name: str, dump_folder: str):
    """
    Ensure that the MongoDB database exists and is populated.
    If it does not exist, import it from the provided dump folder.

    Args:
        db_name (str): Target database name.
        dump_folder (str): Path to the dump folder.
    """
    if database_exists(db_name):
        print(f"✅ MongoDB database '{db_name}' already exists. No action needed.")
    else:
        print(f"⚠️ MongoDB database '{db_name}' not found. Importing from '{dump_folder}'...")
        import_bson_to_mongo(dump_folder, db_name)


def mongo_query(
    db_name: str,
    collection: str,
    query: dict = None,
    projection: dict = None,
    limit: int = None
):
    """
    Execute a query on a MongoDB collection and return standardized result format.

    Args:
        db_name (str): Target database name.
        collection (str): Collection name to query.
        query (dict): MongoDB query filter. Default is empty (all documents).
        projection (dict): MongoDB projection fields. Default is None (all fields).
        limit (int): Maximum number of documents to return. Default is None (no limit).

    Returns:
        dict: {
            "success": True, "data": DataFrame
        } or {
            "success": False, "error": error message
        }
    """
    query = query or {}

    try:
        client = MongoClient(config.MONGO_URI)
        db = client[db_name]

        cursor = db[collection].find(query, projection)
        if limit is not None:
            cursor = cursor.limit(limit)

        data = list(cursor)
        client.close()

        if not data:
            return {"success": True, "data": pd.DataFrame()} 

        df = pd.DataFrame(data)
        return {"success": True, "data": df}

    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


def list_collections(db_name: str) -> list:
    """
    List all collections in the specified MongoDB database.

    Args:
        db_name (str): Target database name.

    Returns:
        list: List of collection names.
    """
    client = MongoClient(config.MONGO_URI)
    db = client[db_name]
    collections = db.list_collection_names()
    client.close()
    return collections

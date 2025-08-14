import json

def transform_tool_args(tool_args: dict, db_clients: dict) -> dict:
    """
    Transform LLM-provided tool_args into concrete arguments
    for query_db, based on db_clients config.

    Args:
        tool_args (dict): Original arguments from LLM.
        db_clients (dict): Logical name → db config.

    Returns:
        dict: Transformed arguments suitable for query_db.
    """
    db_name = tool_args["db_name"]
    sql = tool_args.get("sql")
    client = db_clients.get(db_name)

    if not client:
        return {"success": False, "error": f"Unknown db_name: {db_name}"}

    db_type = client["db_type"]

    if db_type == "mysql":
        return {
            "db_type": "mysql",
            "sql": sql,
            "db_name": client["db_name"]
        }
    
    elif db_type == "postgres":
        return {
            "db_type": "postgres",
            "sql": sql,
            "db_name": client["db_name"]
        }

    elif db_type == "sqlite":
        if not client.get("db_path"):
            raise ValueError(f"SQLite db_path missing for {db_name}")
        return {
            "db_type": "sqlite",
            "sql": sql,
            "db_path": client["db_path"]
        }

    elif db_type == "duckdb":
        if not client.get("db_path"):
            raise ValueError(f"DuckDB db_path missing for {db_name}")
        return {
            "db_type": "duckdb",
            "sql": sql,
            "db_path": client["db_path"]
        }

    elif db_type == "mongo":
        try:
            query_json = json.loads(tool_args["sql"])
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid Mongo JSON query: {e}"
            }
        
        return {
            "db_type": "mongo",
            "db_name": client["db_name"],
            "collection": query_json["collection"],
            "query": query_json.get("filter", {}),
            "projection": query_json.get("projection"),
            "limit": query_json.get("limit", 5)
        }

    else:
        return {"success": False, "error": f"Unsupported db_type: {db_type}"}

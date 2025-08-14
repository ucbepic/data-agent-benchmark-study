import re
from uuid import uuid4

def sanitize_name(name: str) -> str:
    """
    Sanitize a string to be a valid Python identifier component.
    Replaces invalid characters with underscores.
    """
    name = name.strip("`;,")
    name = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    return name

def extract_table_name(sql: str) -> str:
    """
    Extract table name from SQL string.
    Falls back to 'result' if not found.
    """
    match = re.search(r'from\s+([a-zA-Z0-9_`]+)', sql, re.IGNORECASE)
    if match:
        return sanitize_name(match.group(1))
    return "result"

def generate_var_name(tool_name: str, tool_args: dict, step: int | None = None) -> str:
    """
    Generate a unique variable name for a given tool call.

    Args:
        tool_name (str): Name of the tool (query_db, list_dbs, execute_python, etc.)
        tool_args (dict): Arguments passed to the tool.
        step (int, optional): Current step in the agent loop.

    Returns:
        str: Valid Python variable name.
    """
    suffix = f"_step{step}" if step is not None else f"_{uuid4().hex[:6]}"

    if tool_name == "query_db":
        db_type = tool_args.get("db_type", "")
        sql_or_query = tool_args.get("sql", "") or tool_args.get("query", "")

        if db_type in {"mysql", "sqlite", "duckdb"}:
            sql = sql_or_query.lower()
            table = extract_table_name(sql)
            return f"df_{table}{suffix}"

        elif db_type == "mongo":
            collection = tool_args.get("collection", "mongo")
            collection = sanitize_name(collection)
            return f"df_{collection}{suffix}"

        else:
            return f"df_result{suffix}"

    elif tool_name == "list_dbs":
        db_name = sanitize_name(tool_args.get("db_name", "db"))
        return f"tables_{db_name}{suffix}"

    elif tool_name == "execute_python":
        return f"exec_result{suffix}"

    else:
        return f"result{suffix}"

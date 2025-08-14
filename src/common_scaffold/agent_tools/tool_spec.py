def get_tools_spec() -> list[dict]:
    """
    Return the list of available tools (functions) specification
    for the LLM agent.

    Returns:
        list[dict]: tools_spec compatible with OpenAI functions.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "query_db",
                "description": "Execute a query (SQL or Mongo) on a specific database and return the result as a dataframe.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "db_name": {
                            "type": "string",
                            "description": "Logical name of the database, e.g., review_dataset, business_dataset."
                        },
                        "db_type": {
                            "type": "string",
                            "enum": ["mysql", "sqlite", "duckdb", "mongo", "postgres"],
                            "description": "The type/format of the database, which you can infer from the database description."
                        },
                        "sql": {
                            "type": "string",
                            "description": (
                                "For SQL databases: the SQL query string to execute."
                                "For PostgreSQL, remember that unquoted column names are folded to lowercase, so if the column name contains uppercase letters or mixed case, wrap it in double quotes. "
                                "For MongoDB: a JSON string describing the query, including `collection`, `filter`, `projection`, and optional `limit`."
                            )
                        }
                    },
                    "required": ["db_name", "db_type", "sql"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_dbs",
                "description": "List tables or collections in a specific database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "db_name": {
                            "type": "string",
                            "description": "Logical name of the database you want to inspect."
                        }
                    },
                    "required": ["db_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_python",
                "description": (
                    "Execute a Python snippet to process or combine the dataframes already loaded in memory. "
                    "The code MUST use existing variable names and assign the result to a variable named `result`, e.g., "
                    "`result = pd.merge(df_foo, df_bar, on='id')`."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": (
                                "Python code to execute in the context of already loaded dataframes. "
                                "You MUST assign the final output to a variable named `result`."
                            )
                        }
                    },
                    "required": ["code"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "return_answer",
                "description": "Return the final answer to the user and stop the task.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "The final answer to the query."
                        }
                    },
                    "required": ["answer"]
                }
            }
        }
    ]

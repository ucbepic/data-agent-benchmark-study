import json
import argparse
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Any

from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common_scaffold.db_utils.loader import ensure_db, query_db, list_entities
#from execute_python import execute_python

query_dir = Path(__file__).parent / "query2"
deployment_name = "o3"

load_dotenv()

with open(query_dir / "query.json") as f:
    query_content = json.load(f)

if isinstance(query_content, str):
    user_query = query_content
elif isinstance(query_content, dict) and "query" in query_content:
    user_query = query_content["query"]
else:
    raise ValueError("query.json wrong format")


with open("db_description.txt") as f:
    db_description = f.read()

current_project = os.getenv("CURRENT_PROJECT", "GOOGLELOCAL").upper()
mysql_db_name = os.getenv(f"{current_project}_MYSQL_DB_NAME")
mysql_sql_file = os.getenv(f"{current_project}_MYSQL_SQL_FILE", "query_dataset/business_description.sql")

print(f"\n=== 🔗 MySQL: Ensuring database `{mysql_db_name}` is initialized ===")
ensure_db(
    db_type="mysql",
    db_name=mysql_db_name,
    sql_file=mysql_sql_file
)

db_clients = {
    "business_dataset": {
        "db_type": "mysql",
        "db_name": mysql_db_name
    },
    "review_dataset": {
        "db_type": "sqlite",
        "db_path": os.getenv(f"{current_project}_SQLITE_DB_PATH")
    }
}

print(f"\n✅ DB connections ready: {db_clients.keys()}")

def list_dbs(db_name):
    info = db_clients.get(db_name)
    if not info:
        raise ValueError(f"Unknown db_name: {db_name}")
    db_type = info["db_type"]

    if db_type == "mysql":
        tables_df = list_entities(db_type, db_name=info["db_name"])
    elif db_type == "sqlite":
        tables_df = list_entities(db_type, db_path=info["db_path"])
    elif db_type == "duckdb":
        tables_df = list_entities(db_type, db_path=info["db_path"])
    elif db_type == "mongo":
        tables_df = list_entities(db_type, db_name=info["db_name"])
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")

    tables = tables_df.iloc[:, 0].tolist() if isinstance(tables_df, pd.DataFrame) else tables_df

    return {
        "db_name": db_name,
        "db_type": db_type,
        "tables": tables
    }


def transform_tool_args(tool_args, db_clients):
    db_name = tool_args["db_name"]
    sql = tool_args.get("sql")
    client = db_clients.get(db_name)
    if not client:
        raise ValueError(f"Unknown db_name: {db_name}")

    db_type = client["db_type"]

    if db_type == "mysql":
        return {
            "db_type": "mysql",
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
        return {
            "db_type": "mongo",
            "db_name": client["db_name"],
            "collection": tool_args["collection"],
            "query": tool_args.get("query", {}),
            "limit": tool_args.get("limit", 5)
        }

    else:
        raise ValueError(f"Unsupported db_type: {db_type}")


from uuid import uuid4

def generate_var_name(tool_name, tool_args, step=None):
    if tool_name == "query_db":
        db_name = tool_args.get("db_name", "").lower()
        sql_or_query = tool_args.get("sql", "") or tool_args.get("query", "")

        # SQL
        if tool_args.get("db_type") in {"mysql", "sqlite", "duckdb"} or \
           (isinstance(sql_or_query, str) and sql_or_query.strip().lower().startswith(("select", "with"))):
            sql = sql_or_query.lower()
            if "from" in sql:
                table = sql.split("from")[1].split()[0].strip("`").strip()
                if step is not None:
                    return f"df_{table}_step{step}"
                else:
                    return f"df_{table}_{uuid4().hex[:6]}"
            else:
                return f"df_result_{uuid4().hex[:6]}"

        # MongoDB
        elif tool_args.get("db_type") == "mongo":
            collection = tool_args.get("collection")
            if collection:
                if step is not None:
                    return f"df_{collection}_step{step}"
                else:
                    return f"df_{collection}_{uuid4().hex[:6]}"
            else:
                return f"df_mongo_result_{uuid4().hex[:6]}"

        else:
            return f"df_result_{uuid4().hex[:6]}"

    elif tool_name == "list_dbs":
        db_name = tool_args.get("db_name", "").lower()
        if step is not None:
            return f"tables_{db_name}_step{step}"
        else:
            return f"tables_{db_name}_{uuid4().hex[:6]}"


    elif tool_name == "execute_python":
        if step is not None:
            return f"exec_result_step{step}"
        else:
            return f"exec_result_{uuid4().hex[:6]}"

    else:
        return f"result_{uuid4().hex[:6]}"


def execute_python(code: str) -> pd.DataFrame | Any:
    """
    Execute LLM-provided Python code in the context of _vars.
    LLM 必须把结果赋值给 result.
    """
    safe_globals = {"pd": pd}
    local_vars = _vars.copy()  # 提供当前变量上下文

    try:
        exec(code, safe_globals, local_vars)
    except Exception as e:
        raise RuntimeError(f"Error executing code: {e}")
    
    _vars.update(local_vars)
    # 如果 LLM 按约定写在 result 里，就取出来
    if "result" in local_vars:
        _vars["result"] = local_vars["result"]
        return local_vars["result"]

    # 如果没写 result，也返回整个上下文
    return _vars


def return_answer(answer: str):
    print(f"\n✅ Final Answer: {answer}")
    # 这里可以调用 validate_answer(answer) 或其他逻辑
    # validate_answer(answer)
    sys.exit(0)

def validate_answer(answer: str):
    # TODO: implement validation logic here
    pass


client = AzureOpenAI(
    api_key=os.getenv("AZURE_API_KEY_o3"),
    api_version=os.getenv("AZURE_API_VERSION_o3", "2023-05-15"),
    azure_endpoint=os.getenv("AZURE_API_BASE_o3")
)

messages = [
    {
        "role": "system",
        "content": """
You are a data analysis agent.

You have access to the following tools, which I (the system) will execute for you:
- query_db: execute a SQL or Mongo query on the specified database and return a dataframe.
- list_dbs: list all available databases and their tables/collections.
- execute_python: execute a snippet of Python code to process or combine the dataframes already loaded in memory.
- return_answer: return the final answer to the user and stop.

### Rules you MUST follow:
✅ You MUST always include all required arguments for the tool you call.  
✅ When using `query_db`, you MUST specify the `db_name`, the `sql` query, and the `db_type` (which you can infer from the DB description above). You can find the database formats (MySQL, SQLite, MongoDB, DuckDB) from the DB Description. 
✅ When using `list_dbs`, you MUST specify the `db_name` of the database you want to inspect. The `db_name` is a logical name which you can infer from the DB Description above. 
✅ You do NOT need to know or provide any `db_path` or actual file paths — you only use `db_name` returned by `list_dbs`.  
✅ All database connection details and paths are handled by the system. You only work with logical names (`db_name`, `table`) returned by `list_dbs`.
✅ If data has already been queried and stored in a variable, you MUST use that variable directly for further computations. If you really need to re-query to get complete or updated data, you MAY re-query.
✅ If you want to join, merge, filter, or process previously queried dataframes, you MUST use the `execute_python` tool and write Python code that explicitly uses those variable names (e.g., `result = pd.merge(df_foo, df_bar, on='id')`).
✅ You MUST use the exact variable names listed in the previous step(s) when writing execute_python code. Do NOT invent new variable names unless you explicitly assign them.

---

### Example of `list_dbs` call:
{"tool": "list_dbs", "args": {"db_name": "google_dataset"}}

---

### Example of `query_db` call:
{"tool": "query_db", "args": {"db_name": "googlelocal_db", "sql": "SELECT * FROM businesses LIMIT 5;"}}

---

### Stopping the task:
✅ When you have determined the final answer and wish to end the task, you MUST output:
{"tool": "return_answer", "args": {"answer": "…your answer here…"}}

If you cannot proceed, also use `return_answer` with an appropriate message.

---

⚠️ You MUST NOT output any explanation, reasoning, comments, or natural language outside of the JSON.
⚠️ Never wrap the JSON in code fences (e.g., ```json … ```), never output multiple lines, and never include any text before or after the JSON.
⚠️ Never output just {"answer": "..."} — always wrap your final answer in the required {"tool": "return_answer", "args": {...}} format.
Only output a single valid JSON object that I can parse and execute.

"""
    },
    {
        "role": "user",
        "content": f"Query: {user_query}\n\nDB Description:\n{db_description}"
    }
]

TOOLS = {
    "query_db": query_db,
    "list_dbs": list_dbs,
    "execute_python": lambda code: execute_python(code),
    "return_answer": lambda **kwargs: return_answer(**kwargs)
}


tools_spec = [
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
                        "enum": ["mysql", "sqlite", "duckdb", "mongo"],
                        "description": "The type/format of the database, which you can infer from the database description."
                    },
                    "sql": {
                        "type": "string",
                        "description": "The SQL query string to execute (or Mongo query if db_type is mongo)."
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



def call_llm(messages):
    resp = client.chat.completions.create(
        model=deployment_name,
        messages=messages,
        tools=tools_spec
    )
    assistant_msg = resp.choices[0].message
    print(f"\n💬 LLM response:\n{assistant_msg}\n")

    # ✅ 优先走 tool_calls
    if assistant_msg.tool_calls:
        tool_call = assistant_msg.tool_calls[0]
        tool_call_id = tool_call.id
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        return assistant_msg, tool_call_id, tool_name, tool_args

    # ✅ fallback: 直接 JSON 内容
    if assistant_msg.content:
        try:
            obj = json.loads(assistant_msg.content)
            if isinstance(obj, dict) and obj.get("tool") == "return_answer" and "args" in obj:
                return assistant_msg, None, "return_answer", obj["args"]
        except Exception:
            pass

    # ❌ 都没有满足格式
    raise ValueError("❌ LLM did not return any tool_calls or valid return_answer.")



step = 1
_vars = {}
while True:
    print(f"=== 🔄 Step {step} ===")
    assistant_msg, tool_call_id, tool_name, tool_args = call_llm(messages)

    print(f"🤖 Agent chose tool: {tool_name}")
    print(f"🔷 Args: {tool_args}")

    if tool_name == "return_answer":
        print(f"\n✅ Final Answer: {tool_args['answer']}")
        break

    if tool_name not in TOOLS:
        raise ValueError(f"❌ Unknown tool: {tool_name}")
    
    if tool_name == "query_db":
        tool_args = transform_tool_args(tool_args, db_clients)

    # 执行工具
    result = TOOLS[tool_name](**tool_args)

    # 生成变量名
    var_name = generate_var_name(tool_name, tool_args, step)
    _vars[var_name] = result

    print(f"📄 Tool result stored in `{var_name}`")

    # 格式化 preview，尽可能接近 10k chars
    if isinstance(result, pd.DataFrame):
        # 尽量多展示一些行，但不超过10k
        preview = result.head(100).to_markdown()
        if len(preview) > 9500:
            preview = preview[:9500] + "\n... (truncated)"
    elif isinstance(result, (dict, list)):
        preview = json.dumps(result, indent=2)
        if len(preview) > 9500:
            preview = preview[:9500] + "\n... (truncated)"
    else:
        preview = str(result)
        if len(preview) > 9500:
            preview = preview[:9500] + "\n... (truncated)"

    # 把assistant消息和tool消息都存入messages
    messages.append(assistant_msg)

    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "name": tool_name,
        "content": (
            f"✅ Result of `{tool_name}` is stored in variable `{var_name}`.\n"
            f"Available variables: {list(_vars.keys())}\n\n"
            f"Here is a preview (up to 10,000 chars):\n\n{preview}"
        )
    })

    print(f"📄 Preview sent to LLM:\n{preview[:10000]}...\n")

    step += 1

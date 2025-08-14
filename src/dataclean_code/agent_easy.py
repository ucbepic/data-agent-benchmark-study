import json
import argparse
import os
import sys
from pathlib import Path
import pandas as pd

from dotenv import load_dotenv
from openai import AzureOpenAI

sys.path.append(str(Path(__file__).resolve().parents[1]))

from common_scaffold.db_utils.loader import ensure_db, query_db, list_entities
#from execute_python import execute_python

query_dir = Path(__file__).parent / "query1"
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
    "googlelocal_db": {
        "db_type": "mysql",
        "db_name": mysql_db_name
    },
    "review_dataset": {
        "db_type": "sqlite",
        "db_path": os.getenv(f"{current_project}_SQLITE_DB_PATH")
    }
}

print(f"\n✅ DB connections ready: {db_clients.keys()}")

def list_dbs():
    result = []
    for db_name, info in db_clients.items():
        db_type = info["db_type"]
        if db_type == "mysql":
            tables_df = list_entities(db_type, db=info["db_name"])
        elif db_type == "sqlite":
            tables_df = list_entities(db_type, db_path=info["db_path"])
        # …other type, write later
        else:
            continue
        
        tables = tables_df.iloc[:, 0].tolist() if isinstance(tables_df, pd.DataFrame) else tables_df
        result.append({
            "db_name": db_name,
            "db_type": db_type,
            "tables": tables
        })
    return result

def generate_var_name(tool_name, tool_args):
    if tool_name == "query_db":
        db_name = tool_args.get("db_name", "").lower()
        sql_or_query = tool_args.get("sql", "") or tool_args.get("query", "")

        # SQL 
        if db_name in {"mysql", "sqlite", "duckdb"} or sql_or_query.strip().lower().startswith(("select", "with")):
            sql = sql_or_query.lower()
            if "from" in sql:
                table = sql.split("from")[1].split()[0].strip("`").strip()
                return f"df_{table}"
            else:
                return f"df_result"

        # MongoDB
        elif db_name == "mongodb" or isinstance(sql_or_query, dict):
            collection = tool_args.get("collection")
            if collection:
                return f"df_{collection}"
            else:
                return "df_mongo_result"

        else:
            return "df_result"

    elif tool_name == "list_dbs":
        return "db_summary"

    elif tool_name == "execute_python":
        return "exec_result"

    else:
        return "result"


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
- execute_python: execute a snippet of Python code.
- return_answer: return the final answer to the user and stop.

### Rules you MUST follow:
✅ You MUST always include all required arguments for the tool you call.  
✅ When using `query_db`, you MUST specify the `db_name` and the `sql` query.  
✅ When using `list_dbs`, you do NOT need to provide any arguments — just send an empty args `{}`.  
✅ You do NOT need to know or provide any `db_path` or actual file paths — you only use `db_name` returned by `list_dbs`.  
✅ All database connection details and paths are handled by the system. You only work with logical names (`db_name`, `table`) returned by `list_dbs`.

---

### Example of `list_dbs` call:
{"tool": "list_dbs", "args": {}}

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
    #"execute_python": execute_python
}

tools_spec = [
    {
        "type": "function",
        "function": {"name": "query_db"}
    },
    {
        "type": "function",
        "function": {"name": "list_dbs"}
    },
    {
        "type": "function",
        "function": {"name": "execute_python"}
    },
    {
        "type": "function",
        "function": {"name": "return_answer"}
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

    if not assistant_msg.tool_calls:
        raise ValueError("❌ LLM did not return any tool_calls.")

    tool_call = assistant_msg.tool_calls[0]
    tool_call_id = tool_call.id
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    return assistant_msg, tool_call_id, tool_name, tool_args


step = 1
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

    # 执行工具
    result = TOOLS[tool_name](**tool_args)

    # 生成变量名
    var_name = generate_var_name(tool_name, tool_args)

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
            f"Here is a preview (up to 10,000 chars):\n\n{preview}"
        )
    })

    print(f"📄 Preview sent to LLM:\n{preview[:500]}...\n")

    step += 1

import os
import json
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import subprocess

# 加载 .env
load_dotenv()

PG_USER = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = "ucb_db"  # 👈 这里改成你想用的数据库名
DB_NAME_DEFAULT = os.getenv("PG_DB")
if not DB_NAME:  # 如果上面留空，就用 .env 里的
    DB_NAME = DB_NAME_DEFAULT

if not DB_NAME:
    raise ValueError("❌ 没有找到数据库名，请在代码里设置 DB_NAME 或 .env 中设置 DB_NAME！")

# 创建 Postgres 连接
engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{DB_NAME}"
)

table_name = "books_info"
json_file_path = "../query_bookreview/origin_dataset/books_info_remapped.json"

# 读取数据
df = pd.read_json(json_file_path, lines=True)

# 将列表/字典列转成 JSON 字符串
def safe_json_stringify(x):
    if isinstance(x, (list, dict)):
        return json.dumps(x, ensure_ascii=False)
    return str(x) if x is not None else None

json_like_fields = ['author', 'features', 'description', 'categories', 'details']

for col in json_like_fields:
    if col in df.columns:
        df[col] = df[col].apply(safe_json_stringify)

# 写入 PostgreSQL
df.to_sql(name=table_name, con=engine, if_exists="replace", index=False)

print(f"✅ 成功写入 PostgreSQL 表 `{table_name}`，共 {len(df)} 行")

# 导出 SQL 文件
sql_file = "books_info.sql"
env = os.environ.copy()
env["PGPASSWORD"] = PG_PASSWORD

cmd = [
    r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
    "-h", PG_HOST,
    "-U", PG_USER,
    "-d", DB_NAME,
    "-t", table_name,
    "-F", "p",  # plain text
    "-f", sql_file
]

try:
    subprocess.run(cmd, check=True, env=env)
    print(f"🎉 已导出 PostgreSQL 表 `{table_name}` 到 SQL 文件 `{sql_file}`")
except subprocess.CalledProcessError as e:
    print(f"⚠️ 导出 SQL 失败: {e}")

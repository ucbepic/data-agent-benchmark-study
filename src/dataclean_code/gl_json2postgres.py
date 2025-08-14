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
DB_NAME_DEFAULT = os.getenv("PG_DB")
PG_CLIENT = os.getenv("PG_CLIENT", "psql")

# ✅ 如果你想在代码里直接指定一个 db_name，请填在这里
DB_NAME = "ucb_db"  # 👈 这里改成你想用的数据库名

if not DB_NAME:  # 如果上面留空，就用 .env 里的
    DB_NAME = DB_NAME_DEFAULT

if not DB_NAME:
    raise ValueError("❌ 没有找到数据库名，请在代码里设置 DB_NAME 或 .env 中设置 DB_NAME！")
# 构造连接字符串
# 构造连接字符串
engine = create_engine(
    f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{DB_NAME}"
)

# 1️⃣ 读取 JSONL
data = []
with open("../query_googlelocal/origi_dataset/light_meta_LLM_tt.json", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

df = pd.DataFrame(data)

# 2️⃣ 序列化复杂列
def serialize_complex(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value

for col in df.columns:
    df[col] = df[col].apply(serialize_complex)

# 3️⃣ 写入 PostgreSQL
table_name = "business_description"
df.to_sql(table_name, engine, if_exists="replace", index=False)

print(f"✅ 已将数据导入 PostgreSQL 表 `{table_name}` 中，共导入 {len(df)} 条记录。")

# 4️⃣ 用 pg_dump 导出 SQL 文件
sql_file = "business_description.sql"
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

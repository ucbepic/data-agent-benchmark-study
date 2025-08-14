import pandas as pd
import sqlite3

# 1️⃣ 读取 CSV
df_meta = pd.read_csv("../query_stockmarket/origin_dataset/stockinfo_query.csv")

# 2️⃣ 连接（或创建）SQLite 数据库
db_path = "stockinfo_query.db"
conn = sqlite3.connect(db_path)

# 3️⃣ 写入数据库，表名为 stockinfo
df_meta.to_sql("stockinfo", conn, if_exists="replace", index=False)

print(f"✅ 已将 stockinfo.csv 写入 {db_path}，表名：stockinfo")

# 4️⃣ 关闭连接
conn.close()

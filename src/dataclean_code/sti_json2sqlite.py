import pandas as pd
import sqlite3

# 读取 JSON 文件（按行读取，每行为一个对象）
df_info = pd.read_json("../query_stockindex/original_dataset/indexInfo_query.json", lines=True)

# 连接 SQLite 数据库，文件名为 indexInfo.db
conn = sqlite3.connect("indexInfo.db")

# 写入数据到 index_info 表
df_info.to_sql("index_info", conn, if_exists="replace", index=False)

# 可选：预览前几行
print(pd.read_sql("SELECT * FROM index_info LIMIT 5", conn))

conn.close()

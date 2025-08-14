import os
import duckdb
import pandas as pd

# 定义路径
db_path = "stocktrade_query.db"
folders = [
    "../query_stockmarket/origin_dataset/etfs",
    "../query_stockmarket/origin_dataset/stocks"
]

# 建立连接
con = duckdb.connect(db_path)

# 遍历两个文件夹
for folder in folders:
    for file in os.listdir(folder):
        if not file.endswith(".csv"):
            continue

        file_path = os.path.join(folder, file)
        table_name = os.path.splitext(file)[0]  # 去掉 .csv

        try:
            # 读取 CSV
            df = pd.read_csv(file_path)

            # 写入 duckdb（覆盖同名表）
            con.execute(f"DROP TABLE IF EXISTS \"{table_name}\";")
            con.execute(f"CREATE TABLE \"{table_name}\" AS SELECT * FROM df")

            print(f"✅ 写入表: {table_name}")

        except Exception as e:
            print(f"❌ 失败: {file} - {e}")

# 关闭连接
con.close()

print("🎉 所有文件写入完成！")

import duckdb

# 连接 DuckDB 数据库（如果文件不存在会自动创建）
con = duckdb.connect("indexTrade.db")

# 创建表并导入 CSV 数据
con.execute("""
    CREATE OR REPLACE TABLE index_trade AS
    SELECT * FROM read_csv_auto('../query_stockindex/original_dataset/indexTrade_query.csv')
""")

# 可选：查看前几行
print(con.execute("SELECT * FROM index_trade LIMIT 5").fetchdf())

# 关闭连接
con.close()

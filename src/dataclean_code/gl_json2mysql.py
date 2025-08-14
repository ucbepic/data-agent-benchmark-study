import json
import pandas as pd
from sqlalchemy import create_engine, types

# MySQL 配置
password = "20041025"  # 替换为你的密码
db_name = "ucb_db"
table_name = "business_description"
json_file_path = "../query_googlelocal/origi_dataset/light_meta_LLM_tt.json"  # 替换为实际路径

# 创建连接
engine = create_engine(f"mysql+pymysql://root:{password}@localhost:3306/{db_name}")

# 读取 JSONL 数据
df = pd.read_json(json_file_path, lines=True)

# 将 list/dict 类型字段转为 JSON 字符串
json_like_fields = ['hours', 'MISC']
for col in json_like_fields:
    if col in df.columns:
        df[col] = df[col].apply(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else None)

# 字段类型定义
dtype_map = {
    "name": types.Text(),
    "gmap_id": types.Text(),
    "description": types.Text(),
    "num_of_reviews": types.Integer(),
    "hours": types.Text(),
    "MISC": types.Text(),
    "state": types.Text()
}

# 写入 MySQL
df.to_sql(name=table_name, con=engine, if_exists="replace", index=False, dtype=dtype_map)

print(f"✅ 成功写入 `{table_name}` 表，共 {len(df)} 行")
# mysqldump -u root -p --databases ucb_db --tables business_description > business_description.sql

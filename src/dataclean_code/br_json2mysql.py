import pandas as pd
import json
from sqlalchemy import create_engine, types

# 设置数据库信息
password = "20041025"
db_name = "ucb_db"
table_name = "books_info"
json_file_path = "../query_bookreview/original_dataset/books_info_remapped.json"

# 创建连接
engine = create_engine(f"mysql+pymysql://root:{password}@localhost:3306/{db_name}")

# 读取数据
df = pd.read_json(json_file_path, lines=True)

# 将列表/字典列统一转为 JSON 字符串，防止语法错误
def safe_json_stringify(x):
    if isinstance(x, (list, dict)):
        return json.dumps(x, ensure_ascii=False)
    return str(x) if x is not None else None

# 需要处理的字段
json_like_fields = ['author', 'features', 'description', 'categories', 'details']

for col in json_like_fields:
    if col in df.columns:
        df[col] = df[col].apply(safe_json_stringify)

# 字段类型映射（全部改为 Text）
dtype_map = {
    "title": types.Text(),
    "subtitle": types.Text(),
    "author": types.Text(),
    "rating_number": types.Integer(),
    "features": types.Text(),
    "description": types.Text(),
    "price": types.Float(),
    "store": types.Text(),
    "categories": types.Text(),
    "details": types.Text(),
    "book_id": types.Text()
}

# 写入 MySQL
df.to_sql(name=table_name, con=engine, if_exists="replace", index=False, dtype=dtype_map)

print(f"✅ 成功写入表 `{table_name}`，共 {len(df)} 行")

import pandas as pd
import json
from pathlib import Path

# === 路径设置 ===
input_path = Path("../query_yelp/light_dataset")
output_path = Path("../query_yelp/remapped_dataset")
output_path.mkdir(parents=True, exist_ok=True)

# === 读取5个子集 ===
df_business = pd.read_json(input_path / "yelp_business_light.json", lines=True)
df_checkin = pd.read_json(input_path / "yelp_checkin_light.json", lines=True)
df_review = pd.read_json(input_path / "yelp_review_light.json", lines=True)
df_tip = pd.read_json(input_path / "yelp_tip_light.json", lines=True)
df_user = pd.read_json(input_path / "yelp_user_light.json", lines=True)

# === 创建映射表 ===
business_ids = sorted(df_business["business_id"].unique())
user_ids = sorted(df_user["user_id"].unique())
review_ids = sorted(df_review["review_id"].unique())

business_map = {old: f"businessid_{i+1}" for i, old in enumerate(business_ids)}
user_map = {old: f"userid_{i+1}" for i, old in enumerate(user_ids)}
review_map = {old: f"reviewid_{i+1}" for i, old in enumerate(review_ids)}

# === 替换 ID ===
def replace_ids(df, col_name, id_map):
    if col_name in df.columns:
        df[col_name] = df[col_name].map(id_map)
    return df

df_business["business_id"] = df_business["business_id"].map(business_map)
df_checkin = replace_ids(df_checkin, "business_id", business_map)
df_review = replace_ids(df_review, "business_id", business_map)
df_review = replace_ids(df_review, "user_id", user_map)
df_review = replace_ids(df_review, "review_id", review_map)
df_tip = replace_ids(df_tip, "business_id", business_map)
df_tip = replace_ids(df_tip, "user_id", user_map)
df_user = replace_ids(df_user, "user_id", user_map)

# === 保存重编码后的文件 ===
df_business.to_json(output_path / "yelp_business_remapped.json", orient="records", lines=True, force_ascii=False)
df_checkin.to_json(output_path / "yelp_checkin_remapped.json", orient="records", lines=True, force_ascii=False)
df_review.to_json(output_path / "yelp_review_remapped.json", orient="records", lines=True, force_ascii=False)
df_tip.to_json(output_path / "yelp_tip_remapped.json", orient="records", lines=True, force_ascii=False)
df_user.to_json(output_path / "yelp_user_remapped.json", orient="records", lines=True, force_ascii=False)

# === 构造映射总表：businessid -> reviewid[] + userid[] ===
mapping_df = df_review.groupby("business_id").agg({
    "review_id": lambda x: list(x),
    "user_id": lambda x: list(pd.unique(x))
}).reset_index()

mapping_df.columns = ["business_id", "review_ids", "user_ids"]

# === 显示或保存该表（可选）===
print(mapping_df.head(10))  # 可根据需要改为 .to_csv(...) 保存

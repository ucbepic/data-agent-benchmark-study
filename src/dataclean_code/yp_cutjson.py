import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# ========== 参数 ==========
num_business = 100
review_user_limit = 2000
per_business_limit = 50

base_path = Path("../query_yelp/origin_dataset")
output_path = Path("../query_yelp/light_dataset")
output_path.mkdir(parents=True, exist_ok=True)

# ========== 抽样 business ==========
df_business = pd.read_json(base_path / "yelp_academic_dataset_business.json", lines=True)
df_business_sample = df_business.sample(n=num_business, random_state=42)
business_ids = set(df_business_sample["business_id"])

# ========== checkin ==========
df_checkin = pd.read_json(base_path / "yelp_academic_dataset_checkin.json", lines=True)
df_checkin_sample = df_checkin[df_checkin["business_id"].isin(business_ids)].copy()

# ========== review ==========
df_review = pd.read_json(base_path / "yelp_academic_dataset_review.json", lines=True)
df_review = df_review[df_review["business_id"].isin(business_ids)].copy()

# 按 business_id 分组并限制每个 business 最多 50 条
review_list = []
user_ids_set = set()

grouped_reviews = df_review.groupby("business_id")
for bid in business_ids:
    group = grouped_reviews.get_group(bid)
    n = min(per_business_limit, len(group))
    sampled = group.sample(n=n, random_state=42)
    review_list.append(sampled)
    user_ids_set.update(sampled["user_id"].tolist())

df_review_sample = pd.concat(review_list)
# 若总量超过限制，再次采样
if len(df_review_sample) > review_user_limit:
    df_review_sample = df_review_sample.sample(n=review_user_limit, random_state=42)
    user_ids_set = set(df_review_sample["user_id"])

# ========== tip ==========
df_tip = pd.read_json(base_path / "yelp_academic_dataset_tip.json", lines=True)
df_tip_sample = df_tip[df_tip["business_id"].isin(business_ids)].copy()
tip_user_ids = set(df_tip_sample["user_id"])

# ========== user ==========
total_user_ids = list(user_ids_set.union(tip_user_ids))
if len(total_user_ids) > review_user_limit:
    total_user_ids = total_user_ids[:review_user_limit]

df_user = pd.read_json(base_path / "yelp_academic_dataset_user.json", lines=True)
df_user_sample = df_user[df_user["user_id"].isin(total_user_ids)].copy()

# ========== 输出统计 ==========
print(f"采样 business 数量: {len(df_business_sample)}")
print(f"对应 checkin 数量: {len(df_checkin_sample)}")
print(f"对应 review 数量: {len(df_review_sample)}")
print(f"对应 tip 数量: {len(df_tip_sample)}")
print(f"对应 user 数量: {len(df_user_sample)}")

# ========== 保存 ==========
df_business_sample.to_json(output_path / "yelp_business_light.json", orient="records", lines=True, force_ascii=False)
df_checkin_sample.to_json(output_path / "yelp_checkin_light.json", orient="records", lines=True, force_ascii=False)
df_review_sample.to_json(output_path / "yelp_review_light.json", orient="records", lines=True, force_ascii=False)
df_tip_sample.to_json(output_path / "yelp_tip_light.json", orient="records", lines=True, force_ascii=False)
df_user_sample.to_json(output_path / "yelp_user_light.json", orient="records", lines=True, force_ascii=False)

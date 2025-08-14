import json

# 文件路径
review_path = "../amazonreview_query/origin_dataset/light_meta.json"
meta_path = "../amazonreview_query/origin_dataset/Books.jsonl"
output_meta_path = "../amazonreview_query/origin_dataset/light_review.json"

# 读取light_meta中的 parent_asin
parent_asins = set()
with open(review_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line)
            parent_asins.add(entry["parent_asin"])
        except:
            continue

print(f"✅ 从 light_meta 中提取了 {len(parent_asins)} 个唯一 parent_asin")

# 遍历 Books.jsonl 并匹配 parent_asin
matched_reviews = []
with open(meta_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line)
            if entry.get("parent_asin") in parent_asins:
                matched_reviews.append(line)
                # 可选提前退出（如果你确认每个 asin 只有一条记录）
                # if len(matched_reviews) >= len(parent_asins):
                #     break
        except:
            continue

# 保存结果
with open(output_meta_path, "w", encoding="utf-8") as f:
    f.writelines(matched_reviews)

print(f"✅ 已将匹配的 {len(matched_reviews)} 条 review 数据保存到 {output_meta_path}")


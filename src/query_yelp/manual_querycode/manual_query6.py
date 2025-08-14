import duckdb
import pandas as pd
from pymongo import MongoClient
from openai import AzureOpenAI
import json

# === Step 0: Setup Connections ===
con_duck = duckdb.connect("../query_dataset/yelp_user.db")
client_mongo = MongoClient("mongodb://localhost:27017/")
biz_collection = client_mongo["yelp_business"]["business"]

import os
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"
# === Step 1: Load review table and business_refs ===
df_review = con_duck.execute("SELECT * FROM review").fetchdf()
unique_business_refs = df_review["business_ref"].dropna().unique().tolist()

# === Step 2: Load business_id + name + description + attributes from Mongo ===
business_docs = list(biz_collection.find({}, {
    "business_id": 1,
    "name": 1,
    "description": 1,
    "attributes": 1
}))
all_business_ids = [doc["business_id"] for doc in business_docs if "business_id" in doc]

# === Step 3: GPT infer mapping rule ===
def get_mapping_rule(business_ids, business_refs):
    prompt = (
        "You are given two complete ID columns from two different datasets:\n"
        f"- The first column is `business_ref` from a review dataset: {json.dumps(business_refs, indent=2)}\n"
        f"- The second column is `business_id` from a business metadata dataset: {json.dumps(business_ids, indent=2)}\n\n"
        "Each business_ref corresponds to a business_id, but the mapping rule is not provided.\n"
        "Determine the mapping relationship between the two sets of IDs.\n"
        "Please respond with:\n"
        "1. The exact mapping rule in plain English\n"
        "2. An explanation of why you think this rule holds."
    )
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a data engineer analyzing ID columns from different datasets to infer a mapping rule."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

mapping_rule_explanation = get_mapping_rule(all_business_ids, unique_business_refs)
print("\n🧠 GPT-inferred mapping rule:\n", mapping_rule_explanation)

# === Step 4: Resolve business_ref → business_id ===
def resolve_ref_to_id(business_ref):
    prompt = (
        f"The inferred mapping rule is:\n\n{mapping_rule_explanation}\n\n"
        f"Now determine the business_id for:\n"
        f"- business_ref: {business_ref}\n\n"
        "Only respond with the business_id (e.g., 'biz_001')."
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a data assistant mapping business_ref to business_id."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error on {business_ref}: {e}")
        return None

ref_to_id_map = {}
predicted_business_ids = []

for i, row in df_review.iterrows():
    business_ref = row["business_ref"]
    if pd.isna(business_ref):
        predicted_business_ids.append(None)
        continue

    if business_ref not in ref_to_id_map:
        ref_to_id_map[business_ref] = resolve_ref_to_id(business_ref)

    business_id = ref_to_id_map[business_ref]
    predicted_business_ids.append(business_id)
    print(f"[{i}] business_ref = {business_ref} → business_id = {business_id}")

df_review["business_id"] = predicted_business_ids

# === Step 3: Filter Jan–Jun 2016 reviews and group ===
df_review["date"] = pd.to_datetime(df_review["date"], unit="ms", errors="coerce")
df_filtered = df_review[
    (df_review["date"] >= "2016-01-01") & (df_review["date"] <= "2016-06-30")
].copy()

df_grouped = df_filtered.groupby("business_id").agg(
    avg_rating=("rating", "mean"),
    num_reviews=("rating", "count")
).reset_index()

df_top = df_grouped[df_grouped["num_reviews"] >= 5].sort_values(by="avg_rating", ascending=False)

if df_top.empty:
    print("❗ No business has >=5 reviews in the first half of 2016.")
    exit()

best_biz_id = df_top.iloc[0]["business_id"]

# === Step 4: Extract name + category from description ===
def extract_categories(description):
    prompt = (
        "Based on the following business description, identify one or more likely business categories.\n"
        "Respond with a comma-separated list (e.g., 'Nail Salon, Spa').\n\n"
        f"Description: {description}"
    )
    try:
        res = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You extract business categories."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=30
        )
        return res.choices[0].message.content.strip()
    except:
        return "Unknown"

biz_doc = next((b for b in business_docs if b.get("business_id") == best_biz_id), {})
biz_name = biz_doc.get("name", "Unknown")
desc = biz_doc.get("description", "")
category_str = extract_categories(desc) if desc else "Unknown"

# === Step 5: Final result ===
avg_rating = df_top.iloc[0]["avg_rating"]
num_reviews = df_top.iloc[0]["num_reviews"]

print("\n Highest-rated business (Jan–Jun 2016, >=5 reviews):")
print(f" Business Name: {biz_name}")
print(f" Average Rating: {avg_rating} (from {num_reviews} reviews)")
print(f" Categories: {category_str}")
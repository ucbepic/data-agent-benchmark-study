import json
import duckdb
import pandas as pd
from pymongo import MongoClient
from openai import AzureOpenAI

# ========== Step 1: Setup MongoDB and DuckDB ==========
client_mongo = MongoClient("mongodb://localhost:27017/")
biz_collection = client_mongo["yelp_business"]["business"]

con_duck = duckdb.connect("../query_dataset/yelp_user.db")

import os

# ==== Step 0: Setup ====
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"

# ========== Step 3: Load business_ref and review table ==========
df_review = con_duck.execute("SELECT * FROM review").fetchdf()
unique_business_refs = df_review["business_ref"].dropna().unique().tolist()

# ========== Step 4: Load business_id and attributes from MongoDB ==========
biz_cursor = biz_collection.find({}, {"business_id": 1, "attributes": 1})
business_docs = list(biz_cursor)
all_business_ids = [doc["business_id"] for doc in business_docs if "business_id" in doc]

# ========== Step 5: GPT - Infer business_ref → business_id mapping ==========
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
print("\n🧠 Inferred Mapping Rule:\n", mapping_rule_explanation)

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

# Map all business_refs in review table
ref_to_id_map = {}
predicted_business_ids = []

for i, row in df_review.iterrows():
    business_ref = row["business_ref"]
    if pd.isna(business_ref):
        predicted_business_ids.append(None)
        continue
    if business_ref not in ref_to_id_map:
        ref_to_id_map[business_ref] = resolve_ref_to_id(business_ref)
    predicted_business_ids.append(ref_to_id_map[business_ref])
    print(f"[{i}] {business_ref} → {ref_to_id_map[business_ref]}")

df_review["business_id"] = predicted_business_ids

# ========== Step 6: GPT - Determine which businesses offer parking ==========
def offers_any_parking(attributes):
    prompt = (
    "Given the following business attributes, does the business offer either Business Parking or Bike Parking?\n"
    "Business Parking is considered available if **any** of the following are True: garage, street, validated, lot, valet.\n"
    "Respond only with 'yes' or 'no'.\n\n"
    "Note: BusinessParking may be a dictionary encoded as a string. Parse it before making a decision.\n\n"
    f"Attributes: {json.dumps(attributes, indent=2)}"
    )

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You check whether businesses offer parking from attributes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower() == "yes"
    except Exception as e:
        print(f"❌ GPT error on attributes: {e}")
        return False

parking_business_ids = []
for i, biz in enumerate(business_docs):
    biz_id = biz.get("business_id")
    attrs = biz.get("attributes", {})
    if not isinstance(attrs, dict):
        continue
    if offers_any_parking(attrs):
        parking_business_ids.append(biz_id)
        print(f"✅ [{i}] {attrs} → offers Parking")
    else:
        print(f"❌ [{i}] {attrs} → no Parking")

# ========== Step 7: Filter reviews from 2018 ==========
def is_in_2018_by_gpt(time_str, client, deployment_name):
    prompt = (
        "Given the following timestamp, determine whether it falls within the year 2018 — "
        "specifically, between January 1, 2018 (inclusive) and January 1, 2019 (exclusive).\n"
        "Only answer with 'yes' or 'no'.\n\n"
        f"Timestamp: {time_str}"
    )

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies timestamps by date ranges."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        raw_reply = response.choices[0].message.content.strip()
        return raw_reply.lower().startswith("yes")

    except Exception as e:
        print(f"❌ GPT error on '{time_str}': {e}")
        return False

# ========== Step 7: Use GPT to filter reviews in 2018 ==========
in_2018_mask = []
for i, row in df_review.iterrows():
    time_str = row["date"]
    if pd.isna(time_str):
        in_2018_mask.append(False)
        continue
    result = is_in_2018_by_gpt(time_str, client, deployment_name)
    in_2018_mask.append(result)
    print(f"[{i}] {time_str} → {'✅ in 2018' if result else '❌ not in 2018'}")

df_2018 = df_review[in_2018_mask].copy()


# ========== Step 8: Answer query ==========
df_2018_with_parking = df_2018[df_2018["business_id"].isin(parking_business_ids)]
num_businesses = df_2018_with_parking["business_id"].nunique()

print(f"\n In 2018, number of businesses reviewed that offered Business or Bike Parking: {num_businesses}")


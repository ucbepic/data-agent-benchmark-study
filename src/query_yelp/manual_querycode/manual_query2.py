import json
import duckdb
import pandas as pd
import os
from pymongo import MongoClient
from openai import AzureOpenAI  # or: from openai import OpenAI

# ==== Step 0: Setup ====
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"

con_duck = duckdb.connect("../query_dataset/yelp_user.db")
client_mongo = MongoClient("mongodb://localhost:27017/")
biz_collection = client_mongo["yelp_business"]["business"]

# ========== Step 1: Load business_ref and review data ==========
df_review = con_duck.execute("SELECT * FROM review").fetchdf()
unique_business_refs = df_review["business_ref"].dropna().unique().tolist()

# ========== Step 2: Load business_id and description from MongoDB ==========
business_docs = list(biz_collection.find({}, {"business_id": 1, "description": 1}))
all_business_ids = [doc["business_id"] for doc in business_docs if "business_id" in doc]

# ========== Step 3: Infer mapping rule between business_ref → business_id ==========
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
            {"role": "system", "content": "You are a data engineer analyzing two ID columns from different datasets to infer a mapping rule."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

mapping_rule_explanation = get_mapping_rule(all_business_ids, unique_business_refs)
print("\n🧠 GPT-inferred mapping rule:\n")
print(mapping_rule_explanation)

# ========== Step 4: Resolve business_ref → business_id ==========
def resolve_ref_to_id(business_ref):
    prompt = (
        f"The previously inferred mapping rule is:\n\n{mapping_rule_explanation}\n\n"
        f"Now, based on this rule, please determine the corresponding `business_id` for the following `business_ref`:\n"
        f"- business_ref: {business_ref}\n\n"
        "Respond only with the `business_id`, e.g., 'biz_123'."
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a data assistant that maps review business_refs to business_ids using the inferred rule."},
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

# ========== Step 5: Extract U.S. state from business descriptions ==========
def extract_us_state(description):
    prompt = (
        "Based on the following business description, identify the U.S. state where this business is most likely located.\n"
        "Only respond with the full state name (e.g., 'California', 'Texas', 'New York'). If uncertain, respond with 'Unknown'.\n\n"
        f"Description: {description}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts U.S. state names from business descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error on state extraction: {e}")
        return "Unknown"

state_records = []
for i, doc in enumerate(business_docs):
    desc = doc.get("description", "")
    if not desc:
        continue
    state = extract_us_state(desc)
    biz_id = doc.get("business_id")
    state_records.append({"business_id": biz_id, "state": state})
    print(f"[{i}] {biz_id} → {state}")

df_state_map = pd.DataFrame(state_records)

# ========== Step 6: Merge and Analyze ==========
df_merged = pd.merge(df_review, df_state_map, on="business_id", how="left")
df_merged = df_merged.dropna(subset=["state", "rating"])

df_state_summary = df_merged.groupby("state").agg(
    num_reviews=("rating", "count"),
    avg_rating=("rating", "mean")
).reset_index()

df_state_summary = df_state_summary.sort_values(by="num_reviews", ascending=False)
top_state = df_state_summary.iloc[0]

print(f"\nState with most reviews: {top_state['state']}")
print(f" Number of reviews: {top_state['num_reviews']}")
print(f" Average rating: {top_state['avg_rating']}")

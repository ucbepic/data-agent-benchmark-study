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

# ==== Step 1: Load business_ref from DuckDB ====
con_duck = duckdb.connect("../query_dataset/yelp_user.db")
business_refs = con_duck.execute("SELECT DISTINCT business_ref FROM review").fetchdf()["business_ref"].dropna().tolist()

# ==== Step 2: Load business_ids and descriptions from MongoDB ====
client_mongo = MongoClient("mongodb://localhost:27017/")
biz_collection = client_mongo["yelp_business"]["business"]
business_docs = list(biz_collection.find({}, {"business_id": 1, "description": 1}))

# ==== Step 3: GPT to infer mapping rule ====
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

business_ids = [doc["business_id"] for doc in business_docs if "business_id" in doc]
mapping_rule_explanation = get_mapping_rule(business_ids, business_refs)
print("\n🧠 GPT-inferred mapping rule:\n")
print(mapping_rule_explanation)

# ==== Step 4: Resolve business_ref → business_id ====
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
                {"role": "system", "content": "You are a data assistant that maps review business_refs to true business_ids using the inferred rule."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error on {business_ref}: {e}")
        return None

df_review = con_duck.execute("SELECT * FROM review").fetchdf()
predicted_business_ids = []

for i, row in df_review.iterrows():
    business_ref = row["business_ref"]
    business_id = resolve_ref_to_id(business_ref)
    predicted_business_ids.append(business_id)
    print(f"[{i}] business_ref = {business_ref} → business_id = {business_id}")

df_review["business_id"] = predicted_business_ids

# ==== Step 5: Use GPT to detect if description indicates Indianapolis ====
def is_located_in_indianapolis(description):
    prompt = (
        f"Does the following business description clearly indicate that the business is located in Indianapolis?\n\n"
        f"Description: {description}\n\n"
        "Please answer only 'yes' or 'no'."
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that determines the city location of a business from its description."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower() == "yes"
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return False

indianapolis_businesses = []

for i, biz in enumerate(business_docs):
    desc = biz.get("description", "")
    if not desc:
        continue
    if is_located_in_indianapolis(desc):
        indianapolis_businesses.append(biz)
        print(f"✅ Found: Business #{i} → Indianapolis")
    else:
        print(f"❌ Skip: Business #{i} → Not in Indianapolis")

df_ind_biz = pd.DataFrame(indianapolis_businesses)
ind_biz_ids = df_ind_biz["business_id"].tolist()

# ==== Step 6: Filter Indianapolis reviews and calculate average rating ====
df_ind_reviews = df_review[df_review["business_id"].isin(ind_biz_ids)].copy()

if "rating" in df_ind_reviews.columns:
    avg_rating = df_ind_reviews["rating"].mean()
    print(f"\n Average rating for Indianapolis businesses: {avg_rating}")
else:
    print(" Column 'rating' not found in review data.")

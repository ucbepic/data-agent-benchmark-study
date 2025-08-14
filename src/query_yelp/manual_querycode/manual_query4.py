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
business_refs = df_review["business_ref"].dropna().unique().tolist()

# === Step 2: Load business_id, description, attributes from MongoDB ===
biz_cursor = biz_collection.find({}, {"business_id": 1, "description": 1, "attributes": 1})
business_docs = list(biz_cursor)
business_ids = [b["business_id"] for b in business_docs if "business_id" in b]

# === Step 3: GPT infer business_ref → business_id mapping ===
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

mapping_rule_explanation = get_mapping_rule(business_ids, business_refs)
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
                {"role": "system", "content": "You map business_ref to business_id using the inferred rule."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
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
    predicted_business_ids.append(ref_to_id_map[business_ref])
    print(f"[{i}] {business_ref} → {ref_to_id_map[business_ref]}")
df_review["business_id"] = predicted_business_ids

# === Step 4: GPT extract business categories ===
def extract_categories(description):
    prompt = (
        "Based on the following business description, identify one or more likely business categories.\n"
        "Respond with a comma-separated list of categories (e.g., 'Nail Salon, Spa', 'Bar, Restaurant').\n\n"
        f"Description: {description}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You extract business categories from descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=30
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Unknown"

category_records = []
for i, biz in enumerate(business_docs):
    desc = biz.get("description", "")
    if not desc:
        continue
    biz_id = biz.get("business_id")
    cat_str = extract_categories(desc)
    categories = [c.strip() for c in cat_str.split(",") if c.strip()]
    for cat in categories:
        category_records.append({"business_id": biz_id, "category": cat})
    print(f"[{i}] {desc}... → {cat_str}")

df_category_map = pd.DataFrame(category_records)

# === Step 5: GPT determine if business accepts credit cards ===
def accepts_credit_card(attributes):
    prompt = (
        "Given the following attributes of a business, does the business accept credit card payments?\n"
        "Respond only with 'yes' or 'no'.\n\n"
        f"Attributes: {json.dumps(attributes, indent=2)}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You decide if the business accepts credit cards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower() == "yes"
    except Exception:
        return False

credit_card_flags = []
for biz in business_docs:
    biz_id = biz.get("business_id")
    attrs = biz.get("attributes", {})
    credit_card_flags.append({
        "business_id": biz_id,
        "accepts_credit_card": accepts_credit_card(attrs)
    })

df_credit_card = pd.DataFrame(credit_card_flags)

# === Step 6: category + credit card + rating ===
# Merge category info
df_merged = pd.merge(df_category_map, df_credit_card, on="business_id", how="inner")
df_merged = pd.merge(df_merged, df_review[["business_id", "rating"]], on="business_id", how="inner")

# Filter only those that accept credit cards
df_merged = df_merged[df_merged["accepts_credit_card"] == True]

# === Step 7:  category count avg_rating ===
df_category_stats = df_merged.groupby("category").agg(
    num_businesses=("business_id", "nunique"),
    avg_rating=("rating", "mean")
).reset_index()

# Sort by number of businesses accepting credit cards
df_category_stats = df_category_stats.sort_values(by="num_businesses", ascending=False)
top_category = df_category_stats.iloc[0]

print(f"\n Category with most businesses accepting credit cards: {top_category['category']}")
print(f" Number of businesses: {top_category['num_businesses']}")
print(f" Average user rating: {top_category['avg_rating']}")
print(" Top 10 categories with businesses that accept credit cards:\n")
print(df_category_stats.head(10))

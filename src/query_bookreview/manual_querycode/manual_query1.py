import pandas as pd
import mysql.connector
import sqlite3
import json
import os
from sqlalchemy import create_engine
from openai import AzureOpenAI
from dotenv import load_dotenv

# ========== Configuration ========== #
user = os.getenv("MYSQL_USER", "root")
password = os.getenv("MYSQL_PASSWORD", "")
host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
database = "ucb_db"
mysql_table = "books_info"

client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"

# ========== Step 1: Fetch books from MySQL ========== #
def fetch_books():
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {mysql_table}")
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return []

books = fetch_books()
print(f"✅ Total {len(books)} books")

# ========== Step 2: Infer decade for each book ========== #
def get_decade_by_llm(details):
    prompt = (
        "Given the following book details, extract the decade in which the book was first published.\n"
        "Respond with a single answer in the format like '1980s', '2000s', etc. If uncertain because no year information is included in the book details, just answer Uncertain.\n\n"
        f"Details: {details}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts publishing decades from book descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return "Unknown"

for i, book in enumerate(books):
    details = book.get("details", "")
    if not details.strip():
        book["decade"] = "Unknown"
        print(f"❌ [{i}] Unknown")
        continue
    decade = get_decade_by_llm(details)
    book["decade"] = decade
    print(f"✅ [{i}] {book.get('title', 'Untitled')} → {decade}")

book_id_to_decade = {b["book_id"]: b["decade"] for b in books}
df_books = pd.DataFrame(books)
print(df_books["decade"].value_counts())

# ========== Step 3: Load reviews from SQLite ========== #
def fetch_reviews():
    try:
        conn = sqlite3.connect("../query_dataset/review_query.db")
        query = "SELECT * FROM review"
        df = pd.read_sql(query, conn)
        conn.close()
        print(f"✅ Loaded {len(df)} reviews")
        return df
    except Exception as e:
        print(f"❌ SQLite load failed: {e}")
        return pd.DataFrame()

df_review = fetch_reviews()

# ========== Step 4: Infer purchase_id → book_id mapping rule ========== #
def get_mapping_rule(book_ids, purchase_ids):
    prompt = (
        "You are given two complete ID columns from two different datasets:\n"
        f"- The first column is `purchase_id`: {json.dumps(purchase_ids, indent=2)}\n"
        f"- The second column is `book_id`: {json.dumps(book_ids, indent=2)}\n\n"
        "Each purchase_id corresponds to a book_id, but the mapping rule is not provided.\n"
        "Determine the mapping relationship between the two sets of IDs.\n"
        "Please respond with:\n"
        "1. The exact mapping rule in plain English \n"
        "2. An explanation of why you think this rule holds."
    )
    response = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {"role": "system", "content": "You are a data engineer analyzing two columns of IDs for structural relationships."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

book_ids = [b["book_id"] for b in books]
purchase_ids = df_review["purchase_id"].drop_duplicates().tolist()
mapping_rule_explanation = get_mapping_rule(book_ids, purchase_ids)
print("\n GPT-inferred mapping rule:\n")
print(mapping_rule_explanation)

# ========== Step 5: Apply rule to each review ========== #
def resolve_purchase_to_book(purchase_id):
    prompt = (
        f"The previously inferred mapping rule is:\n\n{mapping_rule_explanation}\n\n"
        f"Now, based on this rule, please determine the corresponding `book_id` for the following `purchase_id`:\n"
        f"- purchase_id: {purchase_id}\n\n"
        "Respond only with the `book_id`, e.g., 'bookid_88'."
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a data assistant that maps purchase IDs to book IDs using a known rule."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ GPT error on {purchase_id}: {e}")
        return None

predicted_book_ids = []
for i, row in df_review.iterrows():
    purchase_id = row["purchase_id"]
    book_id = resolve_purchase_to_book(purchase_id)
    predicted_book_ids.append(book_id)
    print(f"[{i}] purchase_id = {purchase_id} → book_id = {book_id}")

df_review["book_id"] = predicted_book_ids

# ========== Step 6: Analyze ratings by decade ========== #
df_review["decade"] = df_review["book_id"].map(book_id_to_decade)
df_review["rating"] = pd.to_numeric(df_review["rating"], errors="coerce")
df_review = df_review[df_review["rating"].notnull() & df_review["decade"].notnull() & (df_review["decade"] != "Unknown")]

df_result = (
    df_review.groupby("decade")
    .agg(
        num_books=("book_id", "nunique"),
        avg_rating=("rating", "mean")
    )
    .reset_index()
)

df_filtered = df_result[df_result["num_books"] >= 10]
top_decade = df_filtered.sort_values(by="avg_rating", ascending=False).head(1)

print("\n Aggregated results by decade (≥10 distinct books):")
print(df_filtered.sort_values(by="avg_rating", ascending=False))

print("\n Top-rated decade:")
print(top_decade)
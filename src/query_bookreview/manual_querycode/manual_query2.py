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
mysql_password = os.getenv("MYSQL_PASSWORD", "")
host = os.getenv("MYSQL_HOST", "localhost")
port = os.getenv("MYSQL_PORT", "3306")
mysql_db = "ucb_db"
mysql_table = "books_info"

client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"

# ========== Step 1: Load book metadata from MySQL ========== #
def fetch_business_data():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=mysql_password,
            database=mysql_db
        )
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {mysql_table}")
        column_names = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(column_names, row)) for row in rows]
    except Exception as e:
        print(f"\u274c MySQL connection failed: {e}")
        return []

books = fetch_business_data()
print(f"\u2705 Total {len(books)} books")

# ========== Step 2: Use GPT to filter English Literature & Fiction books ========== #
def is_qualified_book(details, categories, client, deployment_name):
    prompt = (
        "You're given a book's description and category field.\n"
        "Determine if this book is written in English and belongs to the 'Literature & Fiction' category.\n\n"
        "If both conditions are true, answer with 'yes'. If either is false, answer with 'no'.\n\n"
        f"Description:\n{details}\n\n"
        f"Categories:\n{categories}\n\n"
        "Just answer 'yes' or 'no'.\n\n"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that filters books by language and category."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower() == "yes"
    except Exception as e:
        print(f"\u274c GPT error: {e}")
        return False

qualified_books = []
for i, book in enumerate(books):
    details = book.get("details", "")
    categories = book.get("categories", "")
    if not details.strip():
        print(f"\u274c [{i}] No details")
        continue
    if is_qualified_book(details, categories, client, deployment_name):
        qualified_books.append(book)
        print(f"\u2705 [{i}] Matched: {book.get('title', 'Untitled')}, {categories}")
    else:
        print(f"\u274c [{i}] Not matched")

df_qualified = pd.DataFrame(qualified_books)
print(f"\nRetained {len(df_qualified)} English Literature & Fiction books")

# ========== Step 3: Load reviews from SQLite ========== #
def fetch_reviews():
    try:
        conn = sqlite3.connect("../query_dataset/review_query.db")
        df = pd.read_sql("SELECT * FROM review", conn)
        conn.close()
        print(f"\u2705 Loaded {len(df)} reviews")
        return df
    except Exception as e:
        print(f"\u274c SQLite load failed: {e}")
        return pd.DataFrame()

df_review = fetch_reviews()

# ========== Step 4: Infer purchase_id → book_id rule ========== #
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
print("\n\U0001f9e0 GPT-inferred mapping rule:\n")
print(mapping_rule_explanation)

# ========== Step 5: Apply rule to assign book_id to each review ========== #
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
        print(f"\u274c GPT error on {purchase_id}: {e}")
        return None

predicted_book_ids = []
for i, row in df_review.iterrows():
    purchase_id = row["purchase_id"]
    book_id = resolve_purchase_to_book(purchase_id)
    predicted_book_ids.append(book_id)
    print(f"[{i}] purchase_id = {purchase_id} → book_id = {book_id}")

df_review["book_id"] = predicted_book_ids

# ========== Step 6: Filter and aggregate review ratings ========== #
df_review["rating"] = pd.to_numeric(df_review["rating"], errors="coerce")
df_review = df_review[df_review["rating"].notnull()]
df_filtered = df_review[df_review["book_id"].isin(set(df_qualified["book_id"]))].copy()

df_grouped = (
    df_filtered.groupby("book_id")
    .agg(avg_rating=("rating", "mean"), num_reviews=("rating", "count"))
    .reset_index()
)
df_perfect = df_grouped[df_grouped["avg_rating"] == 5.0].copy()

# ========== Step 7: Join book metadata and verify categories ========== #
df_result = df_perfect.merge(
    df_qualified[["book_id", "title", "categories"]], on="book_id", how="left"
)
df_result = df_result[df_result["categories"].str.contains("Literature & Fiction", case=False, na=False)]

# ========== Step 8: Print result ========== #
print("English Literature & Fiction books with perfect average rating of 5.0 (verified categories):")
print(df_result[["title", "categories"]])

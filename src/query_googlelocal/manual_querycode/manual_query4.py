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
mysql_table = "business_description"

client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )
deployment_name = "gpt-4o-mini"

# === Step 1: GPT function to determine if a timestamp is in 2019 ===
def is_in_2019_by_gpt(time_str, client, deployment_name):
    prompt = (
        "Given the following timestamp, determine whether it falls within the year 2019 — "
        "specifically, between January 1, 2019 (inclusive) and January 1, 2020 (exclusive).\n"
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
        print(f"❌ GPT error: {e}")
        return False

# === Step 2: Load review data from SQLite ===
conn = sqlite3.connect("../query_dataset/review_query.db")
query = "SELECT gmap_id, rating, time, text FROM review"
cursor = conn.cursor()
cursor.execute(query)
rows = cursor.fetchall()
column_names = [desc[0] for desc in cursor.description]

# === Step 3: Filter reviews by GPT judgement on timestamp ===
filtered_reviews = []

for i, row in enumerate(rows):
    record = dict(zip(column_names, row))
    time_str = record.get("time", "")

    if time_str:
        result = is_in_2019_by_gpt(time_str, client, deployment_name)
        if result:
            filtered_reviews.append(record)
            print(f"✅ [{i}] Review in 2019: Raw time: {time_str}, {record.get('text', '')}")
        else:
            print(f"❌ [{i}] Not in 2019")

print(f"\n Total review numbers in 2019: {len(filtered_reviews)}")

# === Step 4: Filter for rating >= 4.5 ===
df_2019 = pd.DataFrame(filtered_reviews)
df_high = df_2019[df_2019["rating"] >= 4.5].copy()

# === Step 5: Count high ratings per business ===
grouped = df_high.groupby("gmap_id").size().reset_index(name="high_rating_count")

# === Step 6: Load business names from MySQL ===
conn_mysql = mysql.connector.connect(
    host="localhost",
    user="root",
    password= mysql_password,  # ✅ Replace with your actual password
    database=mysql_db
)
cursor_mysql = conn_mysql.cursor(dictionary=True)
cursor_mysql.execute("SELECT gmap_id, name FROM business_description")
business_rows = cursor_mysql.fetchall()
df_business = pd.DataFrame(business_rows)

# === Step 7: Join and show top 3 ===
df_merged = grouped.merge(df_business, on="gmap_id", how="left")
top3 = df_merged.sort_values(by="high_rating_count", ascending=False).head(3)

# === Step 8: Display final result ===
print("\n Top 3 businesses with the most 4.5+ reviews in 2019:")
print(top3[["name", "gmap_id", "high_rating_count"]])
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
# ========== Step 1: Load all business descriptions from MySQL ========== #
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
        return rows, column_names
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        return [], []

# ========== Step 2: GPT-based filter for Massage Therapist businesses ========== #
def is_massage_therapist(description, client, deployment_name):
    prompt = (
        "Based on the following business description, determine whether it refers to a massage therapist.\n"
        "Only answer with 'yes' or 'no'.\n\n"
        f"Description: {description}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that identifies massage therapist businesses from descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower().startswith("yes")
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return False

# ========== Step 3: Run GPT filter ========== #
rows, column_names = fetch_business_data()
massage_data = []

for i, row in enumerate(rows):
    record = dict(zip(column_names, row))
    description = record.get("description", "")
    if description and is_massage_therapist(description, client, deployment_name):
        massage_data.append(record)
        print(f"✅ [{i}] is Massage therapist: {description}")
    else:
        print(f"❌ [{i}] is not Massage therapist")

print(f"\n🎯 Total Massage therapist businesses retained: {len(massage_data)}")

# ========== Step 4: Compute average rating from review_query.db ========== #
massage_df = pd.DataFrame(massage_data)
gmap_ids = massage_df["gmap_id"].tolist()

review_conn = sqlite3.connect("../query_dataset/review_query.db")
placeholder = ','.join('?' for _ in gmap_ids)
query = f"""
    SELECT gmap_id, rating
    FROM review
    WHERE gmap_id IN ({placeholder})
"""
review_df = pd.read_sql_query(query, review_conn, params=gmap_ids)

avg_rating = review_df.groupby("gmap_id")["rating"].mean().reset_index()
avg_rating.rename(columns={"rating": "avg_rating"}, inplace=True)

massage_with_rating = massage_df.merge(avg_rating, on="gmap_id", how="left")
qualified_massage = massage_with_rating[massage_with_rating["avg_rating"] >= 4.0].copy()
qualified_massage = qualified_massage.sort_values(by="avg_rating", ascending=False)

# ========== Step 5: Output result ========== #
print("\n Massage Therapist businesses with rating >= 4.0:\n")
print(qualified_massage)

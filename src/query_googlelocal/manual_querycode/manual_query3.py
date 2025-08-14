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

# ========== Step 1: Load business descriptions from MySQL ========== #
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

# ========== Step 2: Use GPT to determine if open after 6PM ========== #
def is_open_after_6pm_by_gpt(hours_string, client, deployment_name):
    prompt = (
        "Based on the weekly business hours provided below, determine whether this business is open after 6PM on any day.\n"
        "Only answer with 'yes' or 'no'.\n\n"
        f"Hours: {hours_string}"
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that reads weekly business hours and identifies late openings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower().startswith("yes")
    except Exception as e:
        print(f"❌ GPT error: {e}")
        return False

# ========== Step 3: Apply GPT filter to business data ========== #
def filter_late_open_businesses(rows, column_names, client, deployment_name):
    open_late_data = []
    for i, row in enumerate(rows):
        record = dict(zip(column_names, row))
        hours = record.get("hours", "")
        if hours and is_open_after_6pm_by_gpt(hours, client, deployment_name):
            open_late_data.append(record)
            print(f"✅ [{i}] Open after 6PM: {hours}")
        else:
            print(f"❌ [{i}] Not open after 6PM")
    return open_late_data

# ========== Step 4: Compute average ratings and rank top 5 ========== #
def rank_top5_by_rating(business_data, review_db_path):
    df = pd.DataFrame(business_data)
    gmap_ids = df["gmap_id"].tolist()

    # Connect to review database
    conn = sqlite3.connect(review_db_path)
    placeholder = ','.join(['?'] * len(gmap_ids))
    query = f"""
        SELECT gmap_id, rating
        FROM review
        WHERE gmap_id IN ({placeholder})
    """
    review_df = pd.read_sql_query(query, conn, params=gmap_ids)

    # Compute average ratings
    avg_rating = review_df.groupby("gmap_id")["rating"].mean().reset_index()
    avg_rating.rename(columns={"rating": "avg_rating"}, inplace=True)

    # Merge with business data
    df_with_rating = df.merge(avg_rating, on="gmap_id", how="left")

    # Sort and select top 5
    top5 = df_with_rating.sort_values(by="avg_rating", ascending=False).head(5)
    return top5[["name", "hours", "avg_rating"]]

# ========== Main Execution ========== #
if __name__ == "__main__":
    # Step 1: Fetch all business descriptions
    rows, column_names = fetch_business_data()

    # Step 2: Filter businesses open after 6PM
    open_late_data = filter_late_open_businesses(rows, column_names, client, deployment_name)
    print(f"\n Total businesses open after 6PM: {len(open_late_data)}")

    # Step 3: Compute top 5 by rating
    top5_results = rank_top5_by_rating(open_late_data, "../query_dataset/review_query.db")

    # Step 4: Display result
    print("\n Top 5 businesses open after 6PM by average rating:\n")
    print(top5_results)

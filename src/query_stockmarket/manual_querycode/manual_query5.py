import sqlite3
import pandas as pd
import duckdb
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI

import os
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )

deployment_name = "gpt-4o"

# === Step 1: Load stock info dataset ===
sqlite_path = r"..\query_dataset\stockinfo_query.db"

def load_stock_info(sqlite_path):
    """
    Load stock info data from SQLite database into a DataFrame.
    """
    conn = sqlite3.connect(sqlite_path)
    table_name = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).iloc[0, 0]
    df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    conn.close()
    return df

df_all = load_stock_info(sqlite_path)
print(f"✅ Loaded {len(df_all)} rows from stock info dataset.")


# === Step 2: LLM to check if Market Category is Capital Market ===
def ask_llm_if_capital_market(category_code):
    """
    Use LLM to determine if the Market Category code corresponds to NASDAQ Capital Market (S).
    """
    prompt = f"""
Here is the mapping rule for NASDAQ market categories:
Q = NASDAQ Global Select Market
G = NASDAQ Global Market
S = NASDAQ Capital Market

Given a security with Market Category code: `{category_code}`  
Does this correspond to NASDAQ Capital Market (S)?  
Reply only with `Yes` or `No`.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who checks if a security belongs to NASDAQ Capital Market."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5
        )
        return response.choices[0].message.content.strip().lower().startswith("yes")
    except Exception as e:
        print(f"[ERROR] LLM call failed for Market Category {category_code}: {e}")
        return False


# === Step 3: Parallel LLM check for Capital Market ===
def parallel_check_with_batches(df, func, column, batch_size=50):
    """
    Run LLM checks in batches in parallel for the given column of a DataFrame.
    """
    total_rows = len(df)
    indices = list(range(total_rows))
    batches = [indices[i:i+batch_size] for i in range(0, total_rows, batch_size)]
    results = [False] * total_rows

    print(f"🚀 Checking [{column}] in {len(batches)} batches...")

    for batch_indices in tqdm(batches, desc=f"Checking {column}"):
        with ThreadPoolExecutor(max_workers=len(batch_indices)) as executor:
            futures = {
                executor.submit(func, str(df.iloc[idx][column]).strip()): idx
                for idx in batch_indices
            }
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"❌ Row {idx} failed: {e}")
                    results[idx] = False
    return results


# === Step 4: Filter Capital Market companies ===
flags_capital = parallel_check_with_batches(df_all, ask_llm_if_capital_market, "Market Category", batch_size=50)
df_all["is_capital"] = flags_capital
df_capital = df_all[df_all["is_capital"]].copy()
print(f"✅ Found {len(df_capital)} companies listed on NASDAQ Capital Market.")


# === Step 5: Count days in 2019 with (High-Low)/Low > 20% ===
duckdb_path = r"..\query_dataset\stocktrade_query.db"
con = duckdb.connect(duckdb_path, read_only=True)

def count_intraday_range_days_2019(symbol):
    """
    Query DuckDB to count the number of days in 2019 where (High - Low)/Low > 20%.
    """
    try:
        query = f"""
        SELECT COUNT(*) 
        FROM "{symbol}"
        WHERE DATE >= '2019-01-01' AND DATE <= '2019-12-31'
          AND ("High" - "Low") / "Low" > 0.2
        """
        result = con.execute(query).fetchone()
        if result and result[0] > 0:
            return result[0]
        else:
            return None  # skip if no data or zero
    except Exception as e:
        print(f"[ERROR] DuckDB query failed for symbol {symbol}: {e}")
        return None


# === Step 6: Iterate and calculate counts ===
range_data = []

for idx, row in tqdm(df_capital.iterrows(), total=len(df_capital), desc="Calculating 2019 intraday >20% days"):
    symbol = row["Symbol"]
    company_desc = row["Company Description"]
    count_days = count_intraday_range_days_2019(symbol)
    if count_days is None:
        continue
    range_data.append((symbol, company_desc, count_days))


# === Step 7: Sort and pick top 5 ===
df_range = pd.DataFrame(range_data, columns=["Symbol", "CompanyDescription", "DaysOver20Pct"])
df_range_sorted = df_range.sort_values(by="DaysOver20Pct", ascending=False).head(5).reset_index(drop=True)

print("\n🎯 Top 5 NASDAQ Capital Market companies with most >20% intraday range days in 2019 (before name cleanup):")
print(df_range_sorted)


# === Step 8: LLM to extract clean company names ===
def extract_company_name(description):
    """
    Use LLM to extract clean company name from its description.
    """
    prompt = f"""
You are given the following company description:
\"\"\"{description}\"\"\"

Your task is to extract the **official company name** from this description.
Output only the company name, nothing else.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who extracts company names from descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] LLM call failed for description: {e}")
        return None


# === Step 9: Apply name cleanup ===
company_names = []
for desc in tqdm(df_range_sorted["CompanyDescription"], desc="Extracting company names"):
    name = extract_company_name(desc)
    company_names.append(name)

df_range_sorted["CompanyName"] = company_names


# === Step 10: Final output ===
print("\n Final Top 5 NASDAQ Capital Market companies:")
print(df_range_sorted[["Symbol", "CompanyName", "DaysOver20Pct"]])



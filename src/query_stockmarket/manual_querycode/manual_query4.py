import sqlite3
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI
import duckdb

import os
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )

deployment_name = "gpt-4o"

sqlite_path = r"..\query_dataset\stockinfo_query.db"

def get_all_rows(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    table_name = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).iloc[0, 0]
    df = pd.read_sql(f"SELECT * FROM [{table_name}]", conn)
    conn.close()
    return df

df_all = get_all_rows(sqlite_path)
print(f"✅ Loaded {len(df_all)} rows from stock info dataset.")

def ask_llm_if_nyse(listing_exchange_code):
    """
    Use LLM to determine if the Listing Exchange code corresponds to NYSE (N).
    """
    prompt = f"""
Here is the mapping rule for exchanges:
A = NYSE MKT
N = New York Stock Exchange (NYSE)
P = NYSE ARCA
Z = BATS Global Markets (BATS)
V = Investors' Exchange, LLC (IEXG)
Q = NASDAQ Global Select Market (top-tier NASDAQ market)

Given a security with Listing Exchange code: `{listing_exchange_code}`  
Does this correspond to New York Stock Exchange (N)?  
Reply only with `Yes` or `No`.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who checks if a security is listed on NYSE."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5
        )
        output = response.choices[0].message.content.strip().lower()
        return output.startswith("yes")
    except Exception as e:
        print(f"[ERROR] LLM call failed for Listing Exchange {listing_exchange_code}: {e}")
        return False

def parallel_check_with_batches(df, func, column, batch_size=50):
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
                    res = future.result()
                    results[idx] = res
                except Exception as e:
                    print(f"❌ Row {idx} failed: {e}")
                    results[idx] = False
    return results

flags_nyse = parallel_check_with_batches(df_all, ask_llm_if_nyse, "Listing Exchange", batch_size=50)
df_all["is_nyse"] = flags_nyse

# Filter: NYSE and not ETF
df_filtered = df_all[(df_all["is_nyse"]) & (df_all["ETF"] != "Y")].copy()
print(f"✅ Found {len(df_filtered)} non-ETF stocks listed on NYSE.")

duckdb_path = r"..\query_dataset\stocktrade_query.db"
con = duckdb.connect(duckdb_path, read_only=True)

def count_up_down_days_2017(symbol):
    """
    Query DuckDB to count up & down days in 2017 for a given symbol.
    If no data is found, return None.
    """
    try:
        query = f"""
        SELECT
            SUM(CASE WHEN "Close" > "Open" THEN 1 ELSE 0 END) AS up_days,
            SUM(CASE WHEN "Close" < "Open" THEN 1 ELSE 0 END) AS down_days
        FROM "{symbol}"
        WHERE DATE >= '2017-01-01' AND DATE <= '2017-12-31'
        """
        result = con.execute(query).fetchone()
        if result:
            up = result[0] if result[0] is not None else 0
            down = result[1] if result[1] is not None else 0
            # if both are 0, assume no data
            if up == 0 and down == 0:
                return None
            return up, down
        else:
            return None
    except Exception as e:
        print(f"[ERROR] DuckDB query failed for symbol {symbol}: {e}")
        return None

up_down_data = []

# iterate over filtered rows and calculate up/down days
for idx, row in tqdm(df_filtered.iterrows(), total=len(df_filtered), desc="Calculating up-down days"):
    symbol = row["Symbol"]
    company_desc = row["Company Description"]
    result = count_up_down_days_2017(symbol)
    if result is None:
        # skip if no data
        continue
    up, down = result
    diff = up - down
    up_down_data.append((symbol, company_desc, up, down, diff))

# create dataframe
df_updown = pd.DataFrame(up_down_data, columns=["Symbol", "CompanyDescription", "UpDays", "DownDays", "Diff"])

# get top5 by Diff
df_updown_sorted = df_updown.sort_values(by="Diff", ascending=False).head(5).reset_index(drop=True)

# LLM function to extract clean company name
def extract_company_name(description):
    """
    Use LLM to extract clean Security Name from its description.
    """
    prompt = f"""
You are given the following company description:
\"\"\"{description}\"\"\"

Your task is to extract the **official Security Name** from this description.
Output only the Security Name, nothing else.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who extracts Security Name from descriptions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=20
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] LLM call failed for description: {e}")
        return None

# extract clean names for top5
from tqdm import tqdm

company_names = []
for desc in tqdm(df_updown_sorted["CompanyDescription"], desc="Extracting company names"):
    name = extract_company_name(desc)
    company_names.append(name)

df_updown_sorted["CompanyName"] = company_names

# final output
print("\n Top 5 non-ETF NYSE stocks with clean company names and highest (UpDays - DownDays) in 2017:")
print(df_updown_sorted[["Symbol", "CompanyName", "UpDays", "DownDays", "Diff"]])


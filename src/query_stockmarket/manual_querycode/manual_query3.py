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

# === Load stock info ===
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
print(f"✅ Found {len(df_all)} rows in stock info dataset.")

def ask_llm_if_nasdaq_q(listing_exchange_code):
    """
    Ask LLM whether this listing exchange code corresponds to NASDAQ Global Select Market (Q).
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
Does this correspond to NASDAQ Global Select Market (Q)?  
Reply only with `Yes` or `No`.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who maps exchange codes to their full names and checks if it is NASDAQ Global Select Market."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5
        )
        output = response.choices[0].message.content.strip().lower()
        return output.startswith("yes")
    except Exception as e:
        print(f"[ERROR] LLM call failed for Listing Exchange {listing_exchange_code}: {e}")
        return None
    
def ask_llm_if_troubled(financial_status_code):
    """
    Ask LLM whether this financial status code means the company is financially troubled.
    """
    prompt = f"""
Here is the mapping rule for financial status codes:
D = Deficient: Issuer Failed to Meet NASDAQ Continued Listing Requirements
E = Delinquent: Issuer Missed Regulatory Filing Deadline
Q = Bankrupt: Issuer Has Filed for Bankruptcy
N = Normal (Default): Issuer Is NOT Deficient, Delinquent, or Bankrupt.
G = Deficient and Bankrupt
H = Deficient and Delinquent
J = Delinquent and Bankrupt
K = Deficient, Delinquent, and Bankrupt

A company is considered financially troubled if it is deficient, delinquent, or both.

Given a security with Financial Status code: `{financial_status_code}`  
Is this company financially troubled?  
Reply only with `Yes` or `No`.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who maps financial status codes to their meaning and checks if company is financially troubled."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5
        )
        output = response.choices[0].message.content.strip().lower()
        return output.startswith("yes")
    except Exception as e:
        print(f"[ERROR] LLM call failed for Financial Status {financial_status_code}: {e}")
        return None

def process_batch(batch_indices, df, func, column):
    batch_results = {}
    with ThreadPoolExecutor(max_workers=len(batch_indices)) as executor:
        futures = {
            executor.submit(func, str(df.iloc[idx][column]).strip()): idx
            for idx in batch_indices
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                res = future.result()
                batch_results[idx] = res
            except Exception as e:
                print(f"❌ Row {idx} failed during batch: {e}")
                batch_results[idx] = None
    return batch_results

def parallel_check_with_batches(df, func, column, batch_size=50):
    total_rows = len(df)
    indices = list(range(total_rows))
    batches = [indices[i:i+batch_size] for i in range(0, total_rows, batch_size)]

    results = [None] * total_rows
    failed_batches = []

    print(f"🚀 Processing {len(batches)} batches of up to {batch_size} each for column [{column}]...")

    for i, batch_indices in enumerate(tqdm(batches, desc=f"Checking {column}")):
        batch_results = process_batch(batch_indices, df, func, column)
        for idx, res in batch_results.items():
            if res is None:
                failed_batches.append(idx)
            results[idx] = res

    if failed_batches:
        print(f"\n🔁 Retrying {len(failed_batches)} failed rows...")
        retry_results = process_batch(failed_batches, df.loc[failed_batches], func, column)
        for idx, res in retry_results.items():
            results[idx] = res if res is not None else False

    return results

# === Check Listing Exchange ===
flags_q = parallel_check_with_batches(df_all, ask_llm_if_nasdaq_q, "Listing Exchange", batch_size=50)
df_all["is_nasdaq_q"] = [bool(flag) for flag in flags_q]
filtered_q_df = df_all[df_all["is_nasdaq_q"]].copy()
print(f"✅ Found {len(filtered_q_df)} rows listed on NASDAQ Global Select Market.")

# === Check Financial Status ===
flags_troubled = parallel_check_with_batches(filtered_q_df, ask_llm_if_troubled, "Financial Status", batch_size=50)
filtered_q_df["is_troubled"] = [bool(flag) for flag in flags_troubled]
final_df = filtered_q_df[filtered_q_df["is_troubled"]].copy()

print(f"✅ Found {len(final_df)} financially troubled companies listed on NASDAQ Q.")

symbols = final_df["Symbol"].tolist()

print(f"Total financially troubled NASDAQ Q companies: {len(symbols)}")

duckdb_path = r"..\query_dataset\stocktrade_query.db"
con = duckdb.connect(duckdb_path, read_only=True)

def get_avg_volume_2008(symbol):
    """
    Query DuckDB to compute average daily trading volume in 2008 for a given symbol.
    If no data is found, return None.
    """
    try:
        query = f"""
        SELECT AVG(Volume) 
        FROM "{symbol}"
        WHERE DATE >= '2008-01-01' AND DATE <= '2008-12-31'
        """
        result = con.execute(query).fetchone()
        # If no data exists, return None
        if result and result[0] is not None:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"[ERROR] DuckDB query failed for symbol {symbol}: {e}")
        return None


volume_data = []

for symbol in tqdm(symbols, desc="Calculating avg daily volume in 2008"):
    avg_vol = get_avg_volume_2008(symbol)
    if avg_vol is not None:
        volume_data.append((symbol, avg_vol))
df_volume = pd.DataFrame(volume_data, columns=["Symbol", "AvgDailyVolume2008"])

print(f"Financially troubled NASDAQ Q companies with average daily volume in 2008:")
print(df_volume)
print(f"✅ Total {len(df_volume)} companies found")
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

# === Step 1: Load ETF=Y rows from SQLite ===
sqlite_path = r"..\query_dataset\stockinfo_query.db"

def get_etf_rows(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    table_name = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';", conn
    ).iloc[0, 0]
    df = pd.read_sql(f"SELECT * FROM [{table_name}] WHERE ETF = 'Y'", conn)
    conn.close()
    return df

df_etf = get_etf_rows(sqlite_path)
print(f"✅ Found {len(df_etf)} ETF rows.")

# === Step 2: LLM to check if Listing Exchange is NYSE Arca ===
def ask_llm_if_nyse_arca(listing_exchange_code):
    """
    Ask LLM whether this listing exchange code corresponds to NYSE Arca.
    Return True if Yes, False otherwise.
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
Does this correspond to NYSE Arca (P)?  
Reply only with `Yes` or `No`.
"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who maps exchange codes to their full names and checks if it is NYSE Arca."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=5
        )
        output = response.choices[0].message.content.strip().lower()
        return output.startswith("yes")
    except Exception as e:
        print(f"[ERROR] LLM call failed for code {listing_exchange_code}: {e}")
        return None

def process_batch(batch_indices, df):
    """
    Process one batch of rows by submitting each to LLM in parallel.
    """
    batch_results = {}
    with ThreadPoolExecutor(max_workers=len(batch_indices)) as executor:
        futures = {
            executor.submit(ask_llm_if_nyse_arca, str(df.iloc[idx]["Listing Exchange"]).strip()): idx
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

def parallel_check_with_batches(df, batch_size=50):
    """
    Run the checks in batches. Retry failed batches at the end.
    """
    total_rows = len(df)
    indices = list(range(total_rows))
    batches = [indices[i:i+batch_size] for i in range(0, total_rows, batch_size)]

    results = [None] * total_rows
    failed_batches = []

    print(f"🚀 Processing {len(batches)} batches of up to {batch_size} each...")

    for i, batch_indices in enumerate(tqdm(batches, desc="Main batches")):
        batch_results = process_batch(batch_indices, df)
        for idx, res in batch_results.items():
            if res is None:
                failed_batches.append(idx)
            results[idx] = res

    if failed_batches:
        print(f"\n🔁 Retrying {len(failed_batches)} failed rows...")
        retry_results = process_batch(failed_batches, df)
        for idx, res in retry_results.items():
            results[idx] = res if res is not None else False

    return results

yes_no_flags = parallel_check_with_batches(df_etf, batch_size=50)

df_etf["is_nyse_arca"] = [bool(flag) for flag in yes_no_flags]
filtered_df = df_etf[df_etf["is_nyse_arca"]].copy()

print(f"✅ Found {len(filtered_df)} ETF rows listed on NYSE Arca.")

# === Step 3: Filter those with Adj Close > 200 in 2015 ===
duckdb_path = r"..\query_dataset\stocktrade_query.db"
con = duckdb.connect(duckdb_path, read_only=True)

def had_adj_close_above_200_2015(symbol):
    """
    Check if the given symbol's table has any row in 2015 with Adj Close > 200.
    """
    try:
        query = f"""
        SELECT 1
        FROM "{symbol}"
        WHERE DATE >= '2015-01-01' AND DATE <= '2015-12-31'
          AND "Adj Close" > 200
        LIMIT 1
        """
        result = con.execute(query).fetchone()
        return result is not None
    except Exception as e:
        print(f"[ERROR] Checking symbol {symbol}: {e}")
        return False

qualified_symbols = []

for symbol in tqdm(filtered_df["Symbol"], desc="Checking Adj Close > 200 in 2015"):
    if had_adj_close_above_200_2015(symbol):
        qualified_symbols.append(symbol)

print(f"✅ Found {len(qualified_symbols)} symbols with Adj Close > 200 in 2015.")

final_df = filtered_df[filtered_df["Symbol"].isin(qualified_symbols)].copy()
print(f"📄 Final dataset has {len(final_df)} rows.")

# === Step 4: Extract company names ===
def extract_company_name(description):
    """
    Ask LLM to extract the company name from the description.
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
        output = response.choices[0].message.content.strip()
        return output
    except Exception as e:
        print(f"[ERROR] LLM call failed for description: {e}")
        return None

company_names = []

for desc in tqdm(final_df["Company Description"], desc="Extracting company names"):
    name = extract_company_name(desc)
    company_names.append(name)

final_df["Company Name"] = company_names

# === Final Output ===
print(f"🎯 Found {len(final_df)} companies matching all criteria:")
for name in final_df["Company Name"]:
    print(f"- {name}")

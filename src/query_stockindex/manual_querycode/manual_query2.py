import pandas as pd
import sqlite3
import duckdb
import json
import re
import ast
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import AzureOpenAI

# ========= Step 1: Load index_info from SQLite ==========
conn_info = sqlite3.connect("../query_dataset/indexInfo_query.db")
df_info = pd.read_sql("SELECT * FROM index_info", conn_info)
conn_info.close()

# ========= Step 2: Setup Azure OpenAI Client ==========
import os
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )

deployment_name = "gpt-4o"

# ========= Step 3: Define LLM inference function ==========
def infer_region_and_symbol(exchange_name, client, deployment_name):
    prompt = (
         f"""You are given the name of a stock exchange: '{exchange_name}'.
            Please answer the following two fields:
            - Region: The global region it belongs to (e.g., Asia, Europe, North America).
            - Index Symbol: The exact symbol used in financial datasets or APIs (e.g., from Yahoo Finance, TradingView, Bloomberg).

            Important:
            - The Index Symbol must be the actual code used in trading data (e.g., in Yahoo Finance).
            - Do NOT return descriptive names like “KOSPI” or “JSE All Share Index”.
            - Return only the standard **index code** used in market data feeds.

            Format:
            Region: <region>  
            Index Symbol: <symbol>"""
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant that maps stock exchanges to their global region and index symbol."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        output = response.choices[0].message.content.strip().split("\n")
        region = output[0].replace("Region:", "").strip()
        index_symbol = output[1].replace("Index Symbol:", "").strip()
        return region, index_symbol
    except Exception as e:
        print(f"[ERROR] {exchange_name}: {e}")
        return None, None

# ========= Step 4: Apply LLM to get region and symbol ==========
df_info["region"] = ""
df_info["index_symbol"] = ""

for i, row in tqdm(df_info.iterrows(), total=len(df_info)):
    exchange = row.get("Exchange", "")
    if not exchange:
        continue
    region, symbol = infer_region_and_symbol(exchange, client, deployment_name)
    df_info.at[i, "region"] = region
    df_info.at[i, "index_symbol"] = symbol
    print(f"[{i}] Exchange: {exchange} | Region: {region} | Symbol: {symbol}")

# ========= Step 5: Load index_trade from DuckDB ==========
con_trade = duckdb.connect("../query_dataset/indexTrade_query.db")
df_trade = con_trade.execute("SELECT * FROM index_trade").fetchdf()
con_trade.close()

# ========= Step 6: Extract unique symbols ==========
index_symbol_list = sorted(df_info["index_symbol"].dropna().unique().tolist())
index_list = sorted(df_trade["Index"].dropna().unique().tolist())

# ========= Step 7: Build and send prompt for mapping ==========
def build_single_mapping_prompt(index_symbol, index_list):
    return (
        f"You are given an index symbol from metadata: '{index_symbol}'.\n"
        "You are also given a list of index symbols from trading data:\n"
        f"{json.dumps(index_list, indent=2)}\n\n"
        "Find the exact or closest semantically equivalent symbol from the list.\n"
        "Respond ONLY with the corresponding symbol from the list (no explanation, no markdown, no quotes)."
    )

index_symbol_to_index = {}

for symbol in tqdm(index_symbol_list, desc="🔁 Mapping index symbols one-by-one"):
    prompt = build_single_mapping_prompt(symbol, index_list)
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial data assistant matching index symbols across datasets."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=20
        )
        mapped_symbol = response.choices[0].message.content.strip()
        if mapped_symbol in index_list:
            index_symbol_to_index[symbol] = mapped_symbol
            print(f"✅ {symbol} → {mapped_symbol}")
        else:
            index_symbol_to_index[symbol] = None
            print(f"⚠️ GPT replied with unknown symbol for {symbol}: {mapped_symbol}")
    except Exception as e:
        print(f"❌ GPT mapping failed for {symbol}: {e}")
        index_symbol_to_index[symbol] = None

# ========= Step 8: Merge metadata and trade data ==========
df_info["index_mapped"] = df_info["index_symbol"].map(index_symbol_to_index)
df_joined = pd.merge(df_info, df_trade, left_on="index_mapped", right_on="Index", how="inner")

# ========= Step 9: Filter North America region ==========
df_na = df_joined[df_joined["region"] == "North America"].copy()
date_list = df_na["Date"].tolist()

# ========= Step 10: Normalize date strings with GPT ==========
def normalize_batch_dates(dates):
    prompt = (
        "You are given a list of date strings in natural language format.\n"
        "Convert each of them into ISO format (yyyy-mm-dd).\n"
        "If any date is invalid, return 'None' for that entry.\n\n"
        "Input:\n"
        + json.dumps(dates, indent=2) + "\n\n"
        "Output:\n"
        "**Only return a plain Python list of ISO-formatted date strings in same order**, no explanation, no variable assignments, and no markdown (no ```python)."
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You convert a list of messy human-readable dates into ISO 8601 format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=500
        )
        text = response.choices[0].message.content.strip()
        match = re.search(r"\[(.*?)\]", text, re.DOTALL)
        if match:
            parsed_list = ast.literal_eval("[" + match.group(1) + "]")
        else:
            parsed_list = ast.literal_eval(text)
        return parsed_list
    except Exception as e:
        print(f"❌ GPT error on batch: {e}")
        print("Raw reply:\n", response.choices[0].message.content if 'response' in locals() else "")
        return [None] * len(dates)

# ========= Step 11: Parallel processing for batch conversion ==========
def parallel_date_normalization(date_list, batch_size=50, max_workers=32):
    batches = [date_list[i:i + batch_size] for i in range(0, len(date_list), batch_size)]
    normalized = [None] * len(date_list)
    failed_batches = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for idx, batch in enumerate(batches):
            future = executor.submit(normalize_batch_dates, batch)
            futures[future] = idx

        for future in tqdm(as_completed(futures), total=len(futures)):
            idx = futures[future]
            try:
                result = future.result()
                normalized[idx * batch_size : idx * batch_size + len(result)] = result
            except Exception as e:
                print(f"❌ Batch {idx} failed during main thread: {e}")
                failed_batches[idx] = batch

    if failed_batches:
        print(f"\n🔁 Retrying {len(failed_batches)} failed batches (after main run)...")
        for idx, batch in failed_batches.items():
            try:
                result = normalize_batch_dates(batch)
                normalized[idx * batch_size : idx * batch_size + len(result)] = result
                print(f"✅ Retry batch {idx} succeeded")
            except Exception as e:
                print(f"❌ Retry batch {idx} failed again: {e}")
                continue

    return normalized

standardized_dates = parallel_date_normalization(date_list)
df_na["parsed_date"] = pd.to_datetime(standardized_dates, errors="coerce")

# ========= Step 12: Filter data for year 2018 ==========
df_filtered = df_na[df_na["parsed_date"].dt.year == 2018].copy()

# ========= Step 13: Count days where Close > Open ==========
df_filtered["is_up_day"] = df_filtered["Close"] > df_filtered["Open"]
df_filtered["is_down_day"] = df_filtered["Close"] < df_filtered["Open"]

up_down_counts = (
    df_filtered.groupby("Index")[["is_up_day", "is_down_day"]]
    .sum()
    .assign(net_up_days=lambda x: x["is_up_day"] - x["is_down_day"])
    .sort_values(by="net_up_days", ascending=False)
)

print("\n North American indices with more up days than down days in 2018:")
print(up_down_counts.head(10))

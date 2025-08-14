import sqlite3
import duckdb
import pandas as pd

from openai import AzureOpenAI       
import os
client = AzureOpenAI(
        api_key=os.getenv("AZURE_API_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_API_BASE")
    )

deployment_name = "gpt-4o"

# Step 1: Extract all unique symbols from SQLite
def get_all_symbols(sqlite_path):
    conn = sqlite3.connect(sqlite_path)
    table_name = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';",
        conn
    ).iloc[0, 0]  # Assume first table
    df = pd.read_sql(f"SELECT Symbol FROM [{table_name}]", conn)
    conn.close()
    symbols = df["Symbol"].dropna().unique().tolist()
    return symbols

# Step 2: Use LLM to infer The RealReal, Inc. symbol
def infer_symbol_for_realreal(symbol_list):
    prompt = (
        f"""You're given a list of stock ticker symbols for publicly traded companies:\n\n{symbol_list}\n\n
Your task is to figure out which ticker symbol belongs to **The RealReal, Inc.**.
Output only the ticker symbol itself, no extra text. If none of them corresponds to The RealReal, Inc., reply with 'None'.
"""
    )
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a financial assistant who maps company names to their stock symbols."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=10
        )
        output = response.choices[0].message.content.strip()
        return output
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None

# Step 3: Query DuckDB for max adjusted close price in 2020
def get_max_adj_close_2020(duckdb_path, symbol):
    con = duckdb.connect(database=duckdb_path, read_only=True)
    tables = con.execute("SHOW TABLES").fetchdf()["name"].values
    if symbol not in tables:
        raise ValueError(f"Table for symbol '{symbol}' not found in DuckDB.")
    query = f"""
        SELECT MAX("Adj Close") AS max_adj_close_2020
        FROM "{symbol}"
        WHERE DATE >= '2020-01-01' AND DATE <= '2020-12-31'
    """
    result_df = con.execute(query).fetchdf()
    con.close()
    return result_df.iloc[0, 0]

if __name__ == "__main__":
    # Paths to your databases
    sqlite_path = r"..\query_dataset\stockinfo_query.db"
    duckdb_path = r"..\query_dataset\stocktrade_query.db"

    # Step 1: Get all symbols
    symbols = get_all_symbols(sqlite_path)
    print(f"✅ Found {len(symbols)} unique symbols.")

    # Step 2: Infer symbol for The RealReal, Inc.
    realreal_symbol = infer_symbol_for_realreal(symbols)
    if not realreal_symbol or realreal_symbol.lower() == "none":
        print("❌ Could not find symbol for The RealReal, Inc.")
    else:
        print(f" The RealReal, Inc. symbol: {realreal_symbol}")

        # Step 3: Find max adjusted close in 2020
        max_price = get_max_adj_close_2020(duckdb_path, realreal_symbol)
        print(f" Maximum Adjusted Close price for {realreal_symbol} in 2020: {max_price}")

import pandas as pd
import duckdb

# Step 1: Load metadata CSV
df_meta = pd.read_csv("../ground_truth_dataset/stockinfo_gt.csv")

# Step 2: Find the symbol for "The RealReal, Inc. - Common Stock"
symbol_row = df_meta[df_meta["Security Name"] == "The RealReal, Inc. - Common Stock"]
if symbol_row.empty:
    raise ValueError("❌ Could not find the symbol for The RealReal, Inc. - Common Stock")

symbol = symbol_row.iloc[0]["Symbol"]
print(f"✅ Found symbol for The RealReal, Inc.: {symbol}")

# Step 3: Connect to DuckDB database
con = duckdb.connect("../ground_truth_dataset/stocktrade_gt.db")

# Step 4: Query maximum Adjusted Close price in 2020
query = f"""
SELECT MAX("Adj Close") AS max_adj_close
FROM "{symbol}"
WHERE EXTRACT(YEAR FROM DATE(Date)) = 2020
"""

result = con.execute(query).fetchone()
if result[0] is None:
    print(" No data found for 2020.")
else:
    print(f" Maximum Adjusted Close price for The RealReal, Inc. ({symbol}) in 2020: {result[0]}")
    with open("ground_truth.csv", "w") as f:
        f.write(f"{result[0]}\n")

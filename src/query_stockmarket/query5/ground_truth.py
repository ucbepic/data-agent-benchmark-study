import pandas as pd
import duckdb

# Step 1: Load metadata
df_meta = pd.read_csv("../ground_truth_dataset/stockinfo_gt.csv")

# Step 2: Filter for NASDAQ Capital Market companies
df_capital_market = df_meta[
    (df_meta["Market Category"] == "S") &
    (df_meta["Listing Exchange"] == "Q")
].copy()

if df_capital_market.empty:
    raise ValueError("❌ No companies found with Market Category=S and Listing Exchange=Q.")

print(f"✅ Found {len(df_capital_market)} companies on NASDAQ Capital Market.")

# Step 3: Connect to DuckDB
con = duckdb.connect("../ground_truth_dataset/stocktrade_gt.db")

results = []

# Step 4: Iterate through symbols and count days
for idx, row in df_capital_market.iterrows():
    symbol = row["Symbol"]
    security_name = row["Security Name"]

    query = f"""
    SELECT COUNT(*) AS count_days
    FROM "{symbol}"
    WHERE EXTRACT(YEAR FROM DATE(Date)) = 2019
      AND (("High" - "Low") / "Low") > 0.2
    """

    try:
        result = con.execute(query).fetchone()
        count_days = result[0]
        if count_days > 0:
            results.append((symbol, security_name, count_days))
            print(f"✅ {symbol} ({security_name}): {count_days} days with >20% intraday gain.")
        else:
            print(f"ℹ️ {symbol} ({security_name}): No >20% intraday gain days.")
    except Exception as e:
        print(f"⚠️ Failed to query {symbol}: {e}")

# Step 5: Sort and output top 5
results.sort(key=lambda x: x[2], reverse=True)
top5 = results[:5]

print("\n Top 5 NASDAQ Capital Market companies (2019) by days with >20% intraday gain:")
for symbol, name, days in top5:
    print(f"- {name} ({symbol}): {days} days")


with open("ground_truth.csv", "w") as f:
    for _, name, _ in top5:
        f.write(f"{name}\n")
import pandas as pd
import duckdb

# Step 1: Load metadata
df_meta = pd.read_csv("../ground_truth_dataset/stockinfo_gt.csv")

# Step 2: Filter for non-ETF stocks listed on NYSE
df_nyse_stocks = df_meta[
    (df_meta["ETF"] == "N") &
    (df_meta["Listing Exchange"] == "N")
].copy()

if df_nyse_stocks.empty:
    raise ValueError("❌ No non-ETF stocks listed on NYSE found.")

print(f"✅ Found {len(df_nyse_stocks)} non-ETF stocks on NYSE.")

# Step 3: Connect to DuckDB
con = duckdb.connect("../ground_truth_dataset/stocktrade_gt.db")

results = []

# Step 4: Iterate over each symbol
for idx, row in df_nyse_stocks.iterrows():
    symbol = row["Symbol"]
    security_name = row["Security Name"]

    query = f"""
    SELECT 
        SUM(CASE WHEN "Close" > "Open" THEN 1 ELSE 0 END) AS up_days,
        SUM(CASE WHEN "Close" < "Open" THEN 1 ELSE 0 END) AS down_days
    FROM "{symbol}"
    WHERE EXTRACT(YEAR FROM DATE(Date)) = 2017
    """
    try:
        up_down = con.execute(query).fetchone()
        up_days, down_days = up_down
        if up_days is None or down_days is None:
            continue

        diff = up_days - down_days
        results.append((symbol, security_name, up_days, down_days, diff))

        print(f"✅ {symbol} ({security_name}): +{up_days} / -{down_days} (diff={diff})")

    except Exception as e:
        print(f"⚠️ Failed to query {symbol}: {e}")

# Step 5: Sort and output top 5
results.sort(key=lambda x: x[4], reverse=True)
top5 = results[:5]

print("\n Top 5 non-ETF NYSE stocks (2017) with more up days than down days:")
for symbol, name, up, down, diff in top5:
    print(f"- {name} ({symbol}): Up={up}, Down={down}, Diff={diff}")

with open("ground_truth.csv", "w") as f:
    for _, name, _, _, _ in top5:
        f.write(f"{name}\n")
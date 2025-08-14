import pandas as pd
import duckdb

# Step 1: Load metadata
df_meta = pd.read_csv("../ground_truth_dataset/stockinfo_gt.csv")

# Step 2: Filter troubled companies on NASDAQ (Listing Exchange == Q)
df_troubled_q = df_meta[
    (df_meta["Listing Exchange"] == "Q") &
    (df_meta["Financial Status"].isin(["D", "H", "E"]))
].copy()

if df_troubled_q.empty:
    raise ValueError("❌ No companies found on NASDAQ with Financial Status D, H, or E.")

print(f"✅ Found {len(df_troubled_q)} companies with Listing Exchange=Q and troubled status.")

# Step 3: Connect to DuckDB
con = duckdb.connect("../ground_truth_dataset/stocktrade_gt.db")

results = []

# Step 4: Iterate over each symbol
for idx, row in df_troubled_q.iterrows():
    symbol = row["Symbol"]
    security_name = row["Security Name"]

    query = f"""
    SELECT AVG(Volume) AS avg_volume
    FROM "{symbol}"
    WHERE EXTRACT(YEAR FROM DATE(Date)) = 2008
    """
    try:
        result = con.execute(query).fetchone()
        avg_volume = result[0]
        if avg_volume is not None:
            results.append((symbol, security_name, avg_volume))
            print(f"✅ {symbol} ({security_name}): Avg Volume in 2008 = {avg_volume:.2f}")
        else:
            print(f"ℹ️ {symbol} ({security_name}): No data for 2008.")
    except Exception as e:
        print(f"⚠️ Failed to query {symbol}: {e}")

# Step 5: Output results
print("\n Companies on NASDAQ Global Select Market with troubled status and their 2008 average volume:")
for symbol, name, avg_vol in results:
    print(f"- {symbol} ({name}): {avg_vol:.2f}")

print(f"\n✅ Total: {len(results)} companies found.")
with open("ground_truth.csv", "w") as f:
    for _, name, avg_vol in results:
        f.write(f"{name},{avg_vol:.2f}\n")
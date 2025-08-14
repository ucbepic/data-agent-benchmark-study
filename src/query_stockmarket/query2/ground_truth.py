import pandas as pd
import duckdb

# Step 1: Load metadata CSV
df_meta = pd.read_csv("../ground_truth_dataset/stockinfo_gt.csv")

# Step 2: Filter ETFs on NYSE Arca
df_etfs = df_meta[(df_meta["ETF"] == "Y") & (df_meta["Listing Exchange"] == "P")].copy()

if df_etfs.empty:
    raise ValueError("❌ No ETFs found on NYSE Arca in metadata.")

print(f"✅ Found {len(df_etfs)} ETF symbols on NYSE Arca.")

# Step 3: Connect to DuckDB
con = duckdb.connect("../ground_truth_dataset/stocktrade_gt.db")

# Step 4: Iterate through symbols and check condition
qualified_names = []

for idx, row in df_etfs.iterrows():
    symbol = row["Symbol"]
    security_name = row["Security Name"]

    query = f"""
    SELECT 1
    FROM "{symbol}"
    WHERE EXTRACT(YEAR FROM DATE(Date)) = 2015
      AND "Adj Close" > 200
    LIMIT 1
    """
    try:
        result = con.execute(query).fetchone()
        if result is not None:
            qualified_names.append(security_name)
            print(f"✅ {security_name} ({symbol}) met the condition.")
        else:
            print(f"ℹ️ {security_name} ({symbol}) did NOT meet the condition.")
    except Exception as e:
        print(f"⚠️ Failed to query {symbol}: {e}")

# Step 5: Output results
print("\n ETFs on NYSE Arca with Adj Close > $200 at any time in 2015:")
for name in qualified_names:
    print(f"- {name}")

print(f"\n Total: {len(qualified_names)} ETFs found.")

with open("ground_truth.csv", "w") as f:
    for name in qualified_names:
        f.write(f"{name}\n")
    f.write(f"Total: {len(qualified_names)}\n")
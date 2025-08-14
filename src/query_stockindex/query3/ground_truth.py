import pandas as pd

def compute_long_term_index_returns(df_trade, df_info):
    """
    Compute long-term return (since 2000) for each stock index based on CloseUSD.

    Args:
        df_trade (pd.DataFrame): Trading data with 'CloseUSD'.
        df_info (pd.DataFrame): Index metadata with 'Region'.

    Returns:
        pd.DataFrame: Top 5 indices with highest return and their regions.
    """
    # Ensure date is datetime
    df_trade["Date"] = pd.to_datetime(df_trade["Date"])

    # Filter for data since 2000
    df_since_2000 = df_trade[df_trade["Date"] >= pd.to_datetime("2000-01-01")].copy()

    # Get first and last CloseUSD per index
    first_close = df_since_2000.sort_values("Date").groupby("Index").first()["CloseUSD"]
    last_close = df_since_2000.sort_values("Date").groupby("Index").last()["CloseUSD"]

    # Compute return ratio
    df_return = pd.DataFrame({
        "start_price": first_close,
        "end_price": last_close
    })
    df_return["return_ratio"] = (df_return["end_price"] - df_return["start_price"]) / df_return["start_price"]
    df_return = df_return.reset_index()

    # Join with region info
    df_result = pd.merge(df_return, df_info[["Index", "Region"]], on="Index", how="left")
    df_result = df_result.sort_values("return_ratio", ascending=False).reset_index(drop=True)

    return df_result.head(5)


if __name__ == "__main__":
    # Load data from fixed paths
    df_trade = pd.read_csv("../ground_truth_dataset/indextrade_gt.csv")
    df_info = pd.read_csv("../ground_truth_dataset/indexInfo_gt.csv")

    # Compute top returns
    top_returns = compute_long_term_index_returns(df_trade, df_info)

    print("Top 5 indices with highest return since 2000:")
    print(top_returns.to_string(index=False))
    with open("ground_truth.csv", "w") as f:
        for _, row in top_returns.iterrows():
            f.write(f"{row['Index']},{row['Region']}\n")
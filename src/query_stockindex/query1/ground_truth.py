import pandas as pd

def compute_asian_volatility(df_process):
    """
    Compute average intraday volatility for selected Asian indices
    from 2020 onward.

    Args:
        df_process (pd.DataFrame): Index trading data.

    Returns:
        pd.DataFrame: Average intraday volatility per index.
    """
    asian_indices = ["HSI", "000001.SS", "399001.SZ", "N225", "KS11", "NSEI", "TWII"]

    # Filter for Asian indices
    df_asian = df_process[df_process["Index"].isin(asian_indices)].copy()

    # Compute intraday volatility: (High - Low) / Open
    df_asian["volatility"] = (df_asian["High"] - df_asian["Low"]) / df_asian["Open"]

    # Keep records since 2020
    df_asian["Date"] = pd.to_datetime(df_asian["Date"])
    df_recent = df_asian[df_asian["Date"] >= pd.to_datetime("2020-01-01")].copy()

    # Group by index and compute average
    df_avg = df_recent.groupby("Index")["volatility"].mean().reset_index()
    df_avg = df_avg.sort_values("volatility", ascending=False).reset_index(drop=True)

    return df_avg


if __name__ == "__main__":
    # Load dataset from predefined paths
    df_process = pd.read_csv("../ground_truth_dataset/indextrade_gt.csv")
    df_info = pd.read_csv("../ground_truth_dataset/indexInfo_gt.csv")

    # Compute average intraday volatility for Asian indices
    result = compute_asian_volatility(df_process)

    print("Average intraday volatility since 2020 (Asian indices):")
    print(result.to_string(index=False))
    print("The highest average intraday volatility index:")
    print(result.head(1))

    top_index = result.iloc[0]['Index']

    with open("ground_truth.csv", "w") as f:
        f.write(f"{top_index}\n")
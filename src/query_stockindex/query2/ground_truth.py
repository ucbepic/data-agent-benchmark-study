import pandas as pd

def filter_up_dominant_indices_2018(df_process):
    """
    Filter North American stock indices that had more up days than down days in 2018.

    Args:
        df_process (pd.DataFrame): Index trading data.

    Returns:
        pd.DataFrame: Indices where up_days > down_days in 2018.
    """
    # North American indices based on indexInfo
    na_indices = ["NYA", "IXIC", "GSPTSE"]

    # Filter for relevant indices and year
    df_na = df_process[df_process["Index"].isin(na_indices)].copy()
    df_na["Date"] = pd.to_datetime(df_na["Date"])
    df_2018 = df_na[df_na["Date"].dt.year == 2018].copy()

    # Compare Close vs Open
    df_2018["up_day"] = df_2018["Close"] > df_2018["Open"]
    df_2018["down_day"] = df_2018["Close"] < df_2018["Open"]

    # Count up/down days
    up_counts = df_2018.groupby("Index")["up_day"].sum()
    down_counts = df_2018.groupby("Index")["down_day"].sum()

    # Combine and filter where up > down
    df_counts = pd.DataFrame({
        "up_days": up_counts,
        "down_days": down_counts
    })
    df_counts["up_minus_down"] = df_counts["up_days"] - df_counts["down_days"]
    df_filtered = df_counts[df_counts["up_days"] > df_counts["down_days"]].reset_index()
    df_filtered = df_filtered.sort_values("up_minus_down", ascending=False).reset_index(drop=True)

    return df_filtered


if __name__ == "__main__":
    # Load data from fixed paths
    df_process = pd.read_csv("../ground_truth_dataset/indextrade_gt.csv")
    df_info = pd.read_csv("../ground_truth_dataset/indexInfo_gt.csv")

    # Get result
    result = filter_up_dominant_indices_2018(df_process)

    print("North American indices with more up days than down days in 2018:")
    if result.empty:
        print("→ None of the indices had more up days than down days.")
    else:
        print(result.to_string(index=False))


        with open("ground_truth.csv", "w") as f:
            for idx in result['Index']:
                f.write(f"{idx}\n")
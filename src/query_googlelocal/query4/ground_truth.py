import pandas as pd

def get_top_highscore_businesses_2018(meta_path, review_path, top_k=3):
    """
    Get businesses with the most high-score (≥4.5) reviews in the year 2018.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        top_k (int): Number of top businesses to return.

    Returns:
        pd.DataFrame: A DataFrame with business names and high-score counts.
    """
    # Load datasets
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Convert Unix timestamp to datetime
    df_review['datetime'] = pd.to_datetime(df_review['time'], unit='ms')

    # Define fixed time window: Jan 1, 2018 – Jan 1, 2019
    start_date = pd.Timestamp("2019-01-01")
    end_date = pd.Timestamp("2020-01-01")
    df_2018 = df_review[(df_review['datetime'] >= start_date) & (df_review['datetime'] < end_date)]

    # Filter high-score reviews (rating ≥ 4.5)
    df_highscore = df_2018[df_2018['rating'] >= 4.5]

    # Count high-score reviews per business
    df_highscore_count = df_highscore.groupby('gmap_id').size().reset_index(name='highscore_count')

    # Join with metadata to get business names
    df_result = pd.merge(df_highscore_count, df_meta[['gmap_id', 'name']], on='gmap_id', how='left')

    # Sort by count and select top-K
    df_top = df_result.sort_values(by='highscore_count', ascending=False).head(top_k)

    return df_top[['name', 'highscore_count']]

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    top_businesses = get_top_highscore_businesses_2018(meta_file, review_file, top_k=3)

    print("Top 3 businesses with the most high-score (≥4.5) reviews in 2018:")
    print(top_businesses.to_string(index=False))

    # Optional: save to CSV
    top_businesses.to_csv("ground_truth.csv", index=False, header=False)

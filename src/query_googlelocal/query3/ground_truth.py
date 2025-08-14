import pandas as pd
from datetime import datetime

def closes_after_6pm(hours_list, state_value):
    """
    Determine whether a business operates past 6PM on any day,
    or if it is marked as 'Open 24 hours'.
    """
    # Top-level check for state field
    if isinstance(state_value, str) and "open 24 hours" in state_value.lower():
        return True

    if not isinstance(hours_list, list):
        return False

    for day_info in hours_list:
        if not (isinstance(day_info, list) and len(day_info) == 2):
            continue

        _, time_range = day_info
        if not isinstance(time_range, str):
            continue

        time_range = time_range.strip().lower()

        # ✅ Add check for "Open 24 hours" in hours
        if "open 24 hours" in time_range:
            return True

        if time_range == "closed":
            continue

        parts = time_range.replace("–", "-").split("-")
        if len(parts) != 2:
            continue

        _, end_time_str = parts
        try:
            fmt = "%I:%M%p" if ":" in end_time_str else "%I%p"
            end_time = datetime.strptime(end_time_str.upper(), fmt)
            if end_time.hour > 18 or (end_time.hour == 18 and end_time.minute > 0):
                return True
        except:
            continue

    return False


def get_top_late_open_businesses(meta_path, review_path, top_k=5):
    """
    Get the top-rated businesses that operate past 6PM on any day
    or are open 24 hours.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        top_k (int): Number of top businesses to return based on average rating.

    Returns:
        pd.DataFrame: A DataFrame with business names, hours, and average ratings.
    """
    # Load datasets
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Determine which businesses operate after 6PM or are open 24h
    df_meta['open_after_6pm'] = df_meta.apply(
        lambda row: closes_after_6pm(row['hours'], row.get('state')), axis=1
    )
    df_open_late = df_meta[df_meta['open_after_6pm']].copy()

    # Merge with review ratings
    df_merged = pd.merge(
        df_open_late[['gmap_id', 'name', 'hours']],
        df_review[['gmap_id', 'rating']],
        on='gmap_id',
        how='inner'
    )

    # Group by business and compute average rating
    df_avg = df_merged.groupby(
        ['gmap_id', 'name', df_merged['hours'].astype(str)]
    ).agg(avg_score=('rating', 'mean')).reset_index()

    # Sort and get top K
    df_top = df_avg.sort_values(by='avg_score', ascending=False).head(top_k)

    return df_top[['name', 'hours', 'avg_score']]

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    top_businesses = get_top_late_open_businesses(meta_file, review_file, top_k=5)

    print("Top-rated businesses open after 6PM (including 24h):")
    print(top_businesses.to_string(index=False))


    # Optional: save to CSV
    top_businesses.to_csv("ground_truth.csv", index=False, header=False)

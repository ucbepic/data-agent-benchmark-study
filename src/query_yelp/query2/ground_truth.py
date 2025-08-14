import pandas as pd

def get_top_state_review_stats(business_path, review_path):
    """
    Identify the U.S. state with the highest number of reviews,
    and compute the average rating from reviews in that state.

    Args:
        business_path (str): Path to the Yelp business JSONL file.
        review_path (str): Path to the Yelp review JSONL file.

    Returns:
        tuple:
            - str: State abbreviation with most reviews
            - int: Number of reviews in that state
            - float: Average rating in that state
            - pd.DataFrame: Full state-level statistics (for optional export)
    """
    # Load datasets
    df_business = pd.read_json(business_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Merge to associate state with each review
    df_merged = pd.merge(df_review, df_business[["business_id", "state"]], on="business_id", how="inner")

    # Group by state and compute review count and average stars
    state_stats = df_merged.groupby("state").agg(
        review_count=("review_id", "count"),
        avg_rating=("stars", "mean")
    ).reset_index()

    # Find the top state
    top_row = state_stats.sort_values(by="review_count", ascending=False).iloc[0]
    top_state = top_row["state"]
    top_count = int(top_row["review_count"])
    top_avg_rating = float(top_row["avg_rating"])

    return top_state, top_count, top_avg_rating, state_stats


if __name__ == "__main__":
    business_file = "../ground_truth_dataset/business_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    # Compute stats
    state, count, avg_rating, df_stats = get_top_state_review_stats(business_file, review_file)

    # Print result
    print(state, count, avg_rating)

    top_row = df_stats.loc[df_stats['review_count'].idxmax()]

    top_state = top_row['state']
    top_avg_rating = top_row['avg_rating']

    with open("ground_truth.csv", "w") as f:
        f.write(f"{top_state},{top_avg_rating}\n")

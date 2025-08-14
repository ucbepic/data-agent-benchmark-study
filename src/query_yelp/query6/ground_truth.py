import pandas as pd
import ast

def get_top_rated_business_in_period(business_path, review_path, target_period="2016-H1"):
    """
    Find the highest-rated business (with at least 5 reviews) in the specified half-year period.

    Args:
        business_path (str): Path to the business JSONL file.
        review_path (str): Path to the review JSONL file.
        target_period (str): Half-year period label (e.g., "2016-H1")

    Returns:
        pd.DataFrame: Single-row DataFrame with period, name, avg_rating, review_count, and categories.
    """
    df_business = pd.read_json(business_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Convert review date to datetime
    df_review["date"] = pd.to_datetime(df_review["date"])

    # Create half-year label
    def get_half_year_period(date):
        return f"{date.year}-H1" if date.month <= 6 else f"{date.year}-H2"
    
    df_review["period"] = df_review["date"].apply(get_half_year_period)

    # Filter reviews for the specified period
    df_period = df_review[df_review["period"] == target_period]

    # Aggregate average rating and review count per business
    df_agg = df_period.groupby("business_id").agg(
        avg_rating=("stars", "mean"),
        review_count=("stars", "count")
    ).reset_index()

    # Keep only businesses with at least 5 reviews
    df_agg = df_agg[df_agg["review_count"] >= 5]

    # Select the highest-rated business (break ties by more reviews)
    df_top = df_agg.sort_values(["avg_rating", "review_count"], ascending=[False, False]).head(1)

    # Merge business metadata
    df_top = df_top.merge(df_business[["business_id", "name", "categories"]], on="business_id", how="left")

    # Add period column for completeness
    df_top.insert(0, "period", target_period)

    # Select relevant columns
    df_top = df_top[["name", "avg_rating", "review_count", "categories"]]

    return df_top


if __name__ == "__main__":
    business_file = "../ground_truth_dataset/business_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    result = get_top_rated_business_in_period(business_file, review_file, target_period="2016-H1")

    # Print result in one line
    print(result.to_string(index=False))

    # Optional export
    top_row = result.iloc[0]
    name = top_row['name']
    avg_rating = top_row['avg_rating']
    categories = top_row['categories']

    with open("ground_truth.csv", "w") as f:
        f.write(f"{name},{categories}\n")

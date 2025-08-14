import pandas as pd
import ast

def get_highly_rated_history_books(meta_path, review_path, rating_threshold=4.0, year_threshold="2020-01-01"):
    """
    Find books categorized as 'History' with average ratings >= threshold since a given date.

    Args:
        meta_path (str): Path to the book metadata JSONL file.
        review_path (str): Path to the book review JSONL file.
        rating_threshold (float): Minimum average rating (default is 4.0).
        year_threshold (str): ISO date string (e.g., "2020-01-01") to filter recent reviews.

    Returns:
        pd.DataFrame: DataFrame containing matching books with title, categories, and average rating.
    """
    # Load data
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Convert timestamp to datetime
    df_review["timestamp"] = pd.to_datetime(df_review["timestamp"])

    # Filter reviews after threshold date
    df_recent = df_review[df_review["timestamp"] >= pd.Timestamp(year_threshold)].copy()

    # Parse categories safely
    def safe_parse(cat):
        if isinstance(cat, list):
            return cat
        try:
            return ast.literal_eval(cat)
        except:
            return []

    df_meta["categories"] = df_meta["categories"].apply(safe_parse)

    # Filter metadata for books containing "History" in categories
    df_meta_history = df_meta[df_meta["categories"].apply(lambda cats: "Children's Books" in cats)].copy()

    # Merge review and metadata
    df_merged = pd.merge(
        df_recent[["parent_asin", "rating"]],
        df_meta_history[["parent_asin", "title", "categories"]],
        on="parent_asin",
        how="inner"
    )

    # Group by title and categories, calculate average rating
    df_avg = df_merged.groupby(["title", df_merged["categories"].apply(tuple)])["rating"].mean().reset_index()
    df_avg.columns = ["title", "categories", "avg_rating"]

    # Filter by rating threshold
    df_result = df_avg[df_avg["avg_rating"] >= rating_threshold].sort_values(by="avg_rating", ascending=False)

    return df_result


# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    result_df = get_highly_rated_history_books(meta_file, review_file, rating_threshold=4.5)

    if not result_df.empty:
        print("📚 Highly-rated 'Children's Books' books (avg rating ≥ 4.5 since 2020):")
        print(result_df.to_string(index=False))
    else:
        print("⚠️ No 'Children's Books' books found with avg rating ≥ 4.5 since 2020.")

    # Optional: Save results
    result_df.to_csv("ground_truth.csv", index=False, header=False)


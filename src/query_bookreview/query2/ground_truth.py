import pandas as pd
import ast

def get_english_litfic_books_rating5(meta_path, review_path):
    """
    Find books written in English, categorized as 'Literature & Fiction',
    and with an average rating of exactly 5.

    Args:
        meta_path (str): Path to the book metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.

    Returns:
        pd.DataFrame: A DataFrame containing book titles and their categories.
    """
    # Load metadata and review data
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse the 'details' field safely
    def parse_details(details):
        if isinstance(details, dict):
            return details
        try:
            return ast.literal_eval(details)
        except:
            return {}

    # Parse the 'categories' field safely
    def parse_categories(cats):
        if isinstance(cats, list):
            return cats
        try:
            return ast.literal_eval(cats)
        except:
            return []

    # Extract details and categories
    df_meta["details_dict"] = df_meta["details"].apply(parse_details)
    df_meta["categories"] = df_meta["categories"].apply(parse_categories)

    # Extract language from details
    df_meta["language"] = df_meta["details_dict"].apply(
        lambda d: d.get("Language") if isinstance(d, dict) else None
    )

    # Merge metadata with reviews using parent_asin
    df_merged = pd.merge(
        df_review[["parent_asin", "rating"]],
        df_meta[["parent_asin", "title", "language", "categories"]],
        on="parent_asin",
        how="inner"
    )

    # Group by book and compute average rating
    df_grouped = df_merged.groupby(["parent_asin", "title", "language"]).agg({
        "rating": "mean",
        "categories": "first"
    }).reset_index()

    df_grouped.rename(columns={"rating": "avg_rating"}, inplace=True)

    # Filter for English books in Literature & Fiction with avg rating = 5.0
    df_filtered = df_grouped[
        (df_grouped["language"] == "English") &
        (df_grouped["avg_rating"] == 5.0) &
        (df_grouped["categories"].apply(lambda cats: "Literature & Fiction" in cats))
    ]

    return df_filtered[["title", "categories"]]

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    top_books = get_english_litfic_books_rating5(meta_file, review_file)

    # Print results
    print(top_books.to_string(index=False))

    # Optional: Save results
    top_books.to_csv("ground_truth.csv", index=False, header=False)


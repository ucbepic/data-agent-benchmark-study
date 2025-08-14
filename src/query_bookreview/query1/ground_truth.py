import pandas as pd
import re
import ast

def get_top_decade_by_rating(meta_path, review_path, min_books=10):
    """
    Identify which publication decade has the highest average book rating,
    considering only decades with at least `min_books` distinct rated books.

    Args:
        meta_path (str): Path to the book metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        min_books (int): Minimum number of rated books required per decade.

    Returns:
        dict or None: Dictionary with keys 'decade', 'book_count', 'avg_rating', or None if no valid result.
    """

    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    def parse_details(details):
        if isinstance(details, dict):
            return details
        try:
            return ast.literal_eval(details)
        except:
            return {}

    def extract_year(publisher):
        if not isinstance(publisher, str):
            return None
        match = re.search(r'\((?:.*?)(\d{4})\)', publisher)
        if match:
            return int(match.group(1))
        return None

    df_meta["details_dict"] = df_meta["details"].apply(parse_details)
    df_meta["publisher_str"] = df_meta["details_dict"].apply(
        lambda d: d.get("Publisher") if isinstance(d, dict) else None
    )
    df_meta["publish_year"] = df_meta["publisher_str"].apply(extract_year)
    df_year = df_meta.dropna(subset=["publish_year"]).copy()
    df_year["decade"] = (df_year["publish_year"] // 10) * 10

    df_review_with_decade = pd.merge(
        df_review[["parent_asin", "rating"]],
        df_year[["parent_asin", "decade"]],
        on="parent_asin",
        how="inner"
    )

    grouped = df_review_with_decade.groupby("decade")
    book_counts = grouped["parent_asin"].nunique()
    avg_ratings = grouped["rating"].mean()

    df_result = pd.DataFrame({
        "book_count": book_counts,
        "avg_rating": avg_ratings
    }).reset_index()

    df_result = df_result[df_result["book_count"] >= min_books]
    df_result = df_result.sort_values(by="avg_rating", ascending=False)

    if not df_result.empty:
        top = df_result.iloc[0]
        return {
            "decade": int(top["decade"]),
            "book_count": int(top["book_count"]),
            "avg_rating": round(top["avg_rating"], 2)
        }
    else:
        return None


# ==== Main block ====
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    result = get_top_decade_by_rating(meta_file, review_file, min_books=10)

    if result:
        print(result)
    else:
        print("No decade has at least 10 rated books.")

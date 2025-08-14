import pandas as pd
import ast

def parse_category(cat):
    """
    Ensure the category field is a list. If it's a stringified list, parse it.
    """
    if isinstance(cat, list):
        return cat
    try:
        return ast.literal_eval(cat)
    except:
        return []

def get_top_category_statistics(meta_path, review_path, top_k=None):
    """
    Compute the most frequently reviewed categories and their average ratings.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        top_k (int or None): If set, return only the top-K categories by count.

    Returns:
        pd.DataFrame: A DataFrame with category name, count, and average rating, sorted by count.
    """
    # Load datasets
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse category into list
    df_meta['category_list'] = df_meta['category'].apply(parse_category)

    # Explode multi-category entries into multiple rows
    df_exploded = df_meta[['gmap_id', 'category_list']].explode('category_list').dropna()

    # Join with ratings
    df_merged = pd.merge(df_review[['gmap_id', 'rating']], df_exploded, on='gmap_id', how='inner')

    # Compute count and average rating per category
    df_stats = df_merged.groupby('category_list').agg(
        count=('rating', 'size'),
        avg_rating=('rating', 'mean')
    ).reset_index()

    # Sort by count descending
    df_top = df_stats.sort_values(by='count', ascending=False)

    if top_k:
        return df_top.head(top_k)
    return df_top

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    # Get top 10 most-reviewed categories with average rating
    top_categories = get_top_category_statistics(meta_file, review_file, top_k=5)

    # Print without index
    print(top_categories.to_string(index=False))

    # Optional: save to CSV
    # top_categories.to_csv("top_categories.csv", index=False)

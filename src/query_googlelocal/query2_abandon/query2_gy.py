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

def get_top_businesses_by_category_keyword(meta_path, review_path, keyword, top_k=None):
    """
    Get top-rated businesses whose categories contain the specified keyword.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        keyword (str): Keyword to search for in category list.
        top_k (int or None): If set, return only the top-K highest-rated businesses.

    Returns:
        pd.DataFrame: A DataFrame with business names and their average ratings, sorted in descending order.
    """
    # Load metadata and review datasets
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse category field into list
    df_meta['category_list'] = df_meta['category'].apply(parse_category)

    # Filter businesses with category containing the keyword (case-insensitive)
    df_meta_filtered = df_meta[df_meta['category_list'].apply(
        lambda cat_list: any(keyword.lower() in str(c).lower() for c in cat_list)
    )].copy()

    # Rename name to avoid collision
    df_meta_filtered.rename(columns={"name": "meta_name"}, inplace=True)

    # Join with reviews
    df_merged = pd.merge(df_review, df_meta_filtered[['gmap_id', 'meta_name']], on='gmap_id', how='inner')

    # Group by name and compute average rating
    df_avg_rating = df_merged.groupby('meta_name')['rating'].mean().reset_index()

    # Sort by rating
    df_top = df_avg_rating.sort_values(by='rating', ascending=False)

    # Return top-K businesses if specified
    if top_k:
        return df_top.head(top_k)
    return df_top

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"
    keyword = "store"

    # Get top 10 highest-rated businesses with category containing the keyword
    top_businesses = get_top_businesses_by_category_keyword(meta_file, review_file, keyword, top_k=10)

    # Print results without index
    print(top_businesses.to_string(index=False))

    # Optional: save to CSV
    # top_businesses.to_csv("top_store_businesses.csv", index=False)

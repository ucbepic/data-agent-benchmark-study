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

def get_massage_therapist_with_high_rating(meta_path, review_path, rating_threshold=4.0):
    """
    Get businesses categorized as Massage therapist with average rating >= rating_threshold.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        rating_threshold (float): Minimum average rating.

    Returns:
        pd.DataFrame: A DataFrame with business names and their average ratings.
    """
    # Load data
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse category field
    df_meta['category_list'] = df_meta['category'].apply(parse_category)

    # Filter category list for "Massage therapist"
    df_meta_filtered = df_meta[df_meta['category_list'].apply(
        lambda cat_list: any("massage therapist" in str(c).lower() for c in cat_list)
    )].copy()

    # Rename to avoid column conflict
    df_meta_filtered.rename(columns={"name": "meta_name"}, inplace=True)

    # Join with review data
    df_merged = pd.merge(df_review, df_meta_filtered[['gmap_id', 'meta_name']], on='gmap_id', how='inner')

    # Group by business and calculate average rating
    df_avg_rating = df_merged.groupby('meta_name')['rating'].mean().reset_index()

    # Filter by threshold
    df_filtered = df_avg_rating[df_avg_rating['rating'] >= rating_threshold].copy()

    # Sort by rating descending
    df_sorted = df_filtered.sort_values(by='rating', ascending=False)

    return df_sorted

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    result = get_massage_therapist_with_high_rating(meta_file, review_file, rating_threshold=4.0)

    # Print results
    print(result.to_string(index=False))

    # Optional: Save to CSV
    result.to_csv("ground_truth.csv", index=False, header=False)

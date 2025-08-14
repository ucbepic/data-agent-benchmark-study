import pandas as pd

def get_top_los_angeles_businesses(meta_path, review_path, top_k=None):
    """
    Get top-rated businesses located in Los Angeles.

    Args:
        meta_path (str): Path to the business metadata JSONL file.
        review_path (str): Path to the review dataset JSONL file.
        top_k (int or None): If set, return only the top-K highest-rated businesses.

    Returns:
        pd.DataFrame: A DataFrame with business names and their average ratings, sorted in descending order.
    """
    # Load metadata and review datasets
    df_meta = pd.read_json(meta_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Filter businesses located in Los Angeles
    df_meta_ca = df_meta[df_meta['address'].str.contains("Los Angeles", na=False)].copy()

    # Rename the name column to avoid collision during merge
    df_meta_ca.rename(columns={"name": "meta_name"}, inplace=True)

    # Join metadata with reviews on gmap_id
    df_merged = pd.merge(df_review, df_meta_ca[['gmap_id', 'meta_name']], on='gmap_id', how='inner')

    # Group by business name and calculate average rating
    df_avg_rating = df_merged.groupby('meta_name')['rating'].mean().reset_index()

    # Sort businesses by average rating in descending order
    df_top = df_avg_rating.sort_values(by='rating', ascending=False)

    # Return top-K businesses if specified
    if top_k:
        return df_top.head(top_k)
    return df_top

# Example usage
if __name__ == "__main__":
    meta_file = "../ground_truth_dataset/meta_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    # Get top 5 highest-rated businesses in Los Angeles
    top_businesses = get_top_los_angeles_businesses(meta_file, review_file, top_k=5)

    # Print results without index
    print(top_businesses.to_string(index=False))

    # Optionally save to CSV (uncomment if needed)
    top_businesses.to_csv("ground_truth.csv", index=False, header=False)

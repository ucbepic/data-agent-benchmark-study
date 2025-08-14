import pandas as pd
import ast

def get_top_credit_card_category(business_path, review_path):
    """
    Find the business category with the largest number of businesses that accept credit cards,
    and return its average user rating.

    Args:
        business_path (str): Path to business JSONL.
        review_path (str): Path to review JSONL.

    Returns:
        pd.DataFrame: A single-row DataFrame with [category, count, avg_rating].
    """
    df_business = pd.read_json(business_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse attributes
    def parse_attributes(attr):
        if isinstance(attr, dict):
            return attr
        try:
            return ast.literal_eval(attr)
        except:
            return {}

    df_business["attributes_parsed"] = df_business["attributes"].apply(parse_attributes)
    df_business["accepts_credit"] = df_business["attributes_parsed"].apply(
        lambda x: x.get("BusinessAcceptsCreditCards", "").lower() == "true"
    )

    df_cc = df_business[df_business["accepts_credit"] == True].copy()

    # Parse categories
    def parse_categories(cat):
        if isinstance(cat, str):
            return [c.strip() for c in cat.split(",") if c.strip()]
        return []

    df_cc["category_list"] = df_cc["categories"].apply(parse_categories)
    df_exploded = df_cc[["business_id", "category_list"]].explode("category_list").dropna()

    # Count businesses per category
    category_counts = df_exploded.groupby("category_list")["business_id"].nunique().reset_index()
    category_counts.columns = ["category", "count"]

    # Join reviews and compute avg rating per category
    df_review_filtered = df_review[df_review["business_id"].isin(df_exploded["business_id"])]
    df_merged = pd.merge(df_review_filtered, df_exploded, on="business_id", how="inner")
    category_ratings = df_merged.groupby("category_list")["stars"].mean().reset_index()
    category_ratings.columns = ["category", "avg_rating"]

    # Merge and get top category
    df_result = pd.merge(category_counts, category_ratings, on="category")
    top_row = df_result.sort_values(by="count", ascending=False).head(1)

    return top_row


if __name__ == "__main__":
    business_file = "../ground_truth_dataset/business_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    top_category = get_top_credit_card_category(business_file, review_file)

    print(top_category.to_string(index=False))


    top_category.to_csv("ground_truth.csv", index=False, header=False)

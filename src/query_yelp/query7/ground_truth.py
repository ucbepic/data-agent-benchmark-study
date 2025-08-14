import pandas as pd
from collections import defaultdict

def get_2016_user_category_stats(user_path, review_path, business_path):
    """
    For users who registered in 2016 (down to timestamp):
      - Count number of such users
      - Count total reviews they wrote after registration
      - Identify top 5 business categories reviewed by them

    Returns:
        (user_count, total_review_count, pd.DataFrame of top categories)
    """
    df_user = pd.read_json(user_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)
    df_business = pd.read_json(business_path, lines=True)

    # Convert time columns to datetime
    df_user["yelping_since"] = pd.to_datetime(df_user["yelping_since"], errors="coerce")
    df_review["date"] = pd.to_datetime(df_review["date"], errors="coerce")

    #  Keep users whose exact registration timestamp is in 2016
    df_users_2016 = df_user[
        (df_user["yelping_since"] >= "2016-01-01") &
        (df_user["yelping_since"] < "2017-01-01")
    ].copy()

    # Merge registration time into reviews
    df_review_merged = df_review.merge(
        df_users_2016[["user_id", "yelping_since"]],
        on="user_id",
        how="inner"
    )

    #  Only keep reviews written strictly after registration timestamp
    df_review_after_reg = df_review_merged[
        df_review_merged["date"] >= df_review_merged["yelping_since"]
    ].copy()

    user_count = df_users_2016["user_id"].nunique()
    total_review_count = len(df_review_after_reg)

    # Join with business to get categories
    df_merged = df_review_after_reg.merge(
        df_business[["business_id", "categories"]],
        on="business_id",
        how="left"
    )

    def parse_categories(cat_str):
        if isinstance(cat_str, str):
            return [c.strip() for c in cat_str.split(",") if c.strip()]
        return []

    df_merged["category_list"] = df_merged["categories"].apply(parse_categories)

    category_counter = defaultdict(int)
    for cats in df_merged["category_list"]:
        for cat in cats:
            category_counter[cat] += 1

    top_categories = sorted(category_counter.items(), key=lambda x: x[1], reverse=True)[:5]
    df_top = pd.DataFrame(top_categories, columns=["category", "review_count"])

    return user_count, total_review_count, df_top


if __name__ == "__main__":
    user_file = "../ground_truth_dataset/user_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"
    business_file = "../ground_truth_dataset/business_gt.json"

    user_count, review_count, top_categories = get_2016_user_category_stats(
        user_path=user_file,
        review_path=review_file,
        business_path=business_file
    )

    print(f"Number of users who registered in 2016: {user_count}")
    print(f"Total reviews written *after registration*: {review_count}")
    print("Top 5 most-reviewed business categories by these users:")
    print(top_categories.to_string(index=False))


    # Optional: save to CSV
    with open("ground_truth.csv", "w") as f:
        for cat in top_categories['category']:
            f.write(f"{cat}\n")

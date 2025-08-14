import pandas as pd

def get_indianapolis_average_rating(business_path, review_path):
    """
    Compute the average rating of all businesses located in Indianapolis.

    Args:
        business_path (str): Path to the Yelp business JSONL file.
        review_path (str): Path to the Yelp review JSONL file.

    Returns:
        tuple:
            - int: Number of businesses in Indianapolis
            - float: Average rating
            - pd.DataFrame: Raw review records for Indianapolis businesses (for optional export)
    """
    # Load datasets
    df_business = pd.read_json(business_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Filter businesses located in Indianapolis
    df_indy = df_business[df_business["city"] == "Indianapolis"].copy()

    # Get list of business_id
    indy_ids = df_indy["business_id"]

    # Filter reviews for these businesses
    df_indy_reviews = df_review[df_review["business_id"].isin(indy_ids)]

    # Compute average rating
    average_rating = df_indy_reviews["stars"].mean()

    return len(indy_ids), average_rating, df_indy_reviews


if __name__ == "__main__":
    business_file = "../ground_truth_dataset/business_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    # Run computation
    num_businesses, avg_rating, df_reviews = get_indianapolis_average_rating(business_file, review_file)

    # Print result
    print(avg_rating)

    

    # Optional: save reviews to CSV
    pd.DataFrame([[avg_rating]]).to_csv("ground_truth.csv", index=False, header=False)
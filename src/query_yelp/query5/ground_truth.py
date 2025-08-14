import pandas as pd
import ast

def get_top_wifi_state(business_path, review_path):
    """
    Find the U.S. state with the most businesses offering WiFi,
    and compute the average rating of those businesses.

    Args:
        business_path (str): Path to the business JSONL file.
        review_path (str): Path to the review JSONL file.

    Returns:
        pd.DataFrame: A one-row DataFrame with columns [state, wifi_business_count, avg_rating].
    """
    df_business = pd.read_json(business_path, lines=True)
    df_review = pd.read_json(review_path, lines=True)

    # Parse attributes safely
    def parse_attributes(attr):
        if isinstance(attr, dict):
            return attr
        try:
            return ast.literal_eval(attr)
        except:
            return {}

    df_business["attributes_parsed"] = df_business["attributes"].apply(parse_attributes)

    # Check if business offers WiFi
    def offers_wifi(attr_dict):
        wifi = attr_dict.get("WiFi", "").lower()
        return wifi in ["u'free'", "u'paid'", "'free'", "'paid'", "free", "paid"]

    df_business["offers_wifi"] = df_business["attributes_parsed"].apply(offers_wifi)
    df_wifi = df_business[df_business["offers_wifi"] == True].copy()

    # Count per state
    state_counts = df_wifi.groupby("state")["business_id"].nunique().reset_index()
    state_counts.columns = ["state", "wifi_business_count"]
    top_state_row = state_counts.sort_values(by="wifi_business_count", ascending=False).head(1)

    # Extract that state's business IDs
    top_state = top_state_row.iloc[0]["state"]
    wifi_business_ids = df_wifi[df_wifi["state"] == top_state]["business_id"]
    df_review_filtered = df_review[df_review["business_id"].isin(wifi_business_ids)]
    avg_rating = df_review_filtered["stars"].mean()

    # Assemble result
    result = pd.DataFrame([{
        "state": top_state,
        "wifi_business_count": int(top_state_row.iloc[0]["wifi_business_count"]),
        "avg_rating": round(avg_rating, 2)
    }])

    return result


if __name__ == "__main__":
    business_file = "../ground_truth_dataset/business_gt.json"
    review_file = "../ground_truth_dataset/review_gt.json"

    result = get_top_wifi_state(business_file, review_file)

    print(result.to_string(index=False))

    top_row = result.iloc[0]
    state = top_row['state']
    avg_rating = top_row['avg_rating']

    with open("ground_truth.csv", "w") as f:
        f.write(f"{state},{avg_rating}\n")

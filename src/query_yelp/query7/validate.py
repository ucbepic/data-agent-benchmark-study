def validate(llm_output: str) -> (bool, str):
    """
    Validate if all ground truth categories are present in LLM output (case-insensitive).

    Returns:
        (True, "OK") if all found
        (False, reason) if any missing
    """
    # ground truth
    categories = [
        "Restaurants",
        "Food",
        "American (New)",
        "Shopping",
        "Breakfast & Brunch"
    ]

    llm_lower = llm_output.lower()
    categories_lower = [c.lower() for c in categories]

    # check all categories
    for cat in categories_lower:
        if cat not in llm_lower:
            reason = f"Missing category: {cat}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All categories are present.")
    return True, "OK"

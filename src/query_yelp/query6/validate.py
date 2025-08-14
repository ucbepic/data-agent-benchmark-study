def validate(llm_output: str) -> (bool, str):
    """
    Validate if:
    - name is present
    - all categories are present
    (rating not required)

    Returns:
        (True, "OK") if all pass
        (False, reason) if not
    """
    # ground truth
    name = "Coffee House Too Cafe"
    categories = ["Restaurants", "Breakfast & Brunch", "American (New)", "Cafes"]

    llm_lower = llm_output.lower()
    name_lower = name.lower()
    categories_lower = [c.lower() for c in categories]

    # check name
    if name_lower not in llm_lower:
        reason = f"Missing name: {name}"
        print(f"❌ {reason}")
        return False, reason

    # check all categories
    for cat in categories_lower:
        if cat not in llm_lower:
            reason = f"Missing category: {cat}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ Name and all categories are present.")
    return True, "OK"

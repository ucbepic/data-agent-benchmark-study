def validate(llm_output: str) -> (bool, str):
    """
    Validate that:
    - All name+country pairs from ground truth appear in LLM output
    - In the same order (not necessarily contiguous)
    - For each name, its *own* country (or alias) appears within 50 chars
    - Case-insensitive

    Returns:
        (True, "OK") if all good
        (False, reason) if failed
    """
    gt_pairs = [
        ("399001.SZ", "China"),
        ("NSEI", "India"),
        ("IXIC", "United States"),
        ("000001.SS", "China"),
        ("NYA", "United States"),
    ]

    # mapping: country → list of acceptable forms
    country_aliases = {
        "china": ["china", "cn"],
        "india": ["india", "in"],
        "united states": ["united states", "us", "usa"],
    }

    llm_lower = llm_output.lower()
    last_idx = -1

    for name, country in gt_pairs:
        name_lower = name.lower()
        country_lower = country.lower()

        idx = llm_lower.find(name_lower, last_idx + 1)
        if idx == -1:
            reason = f"Missing name: {name}"
            print(f"❌ {reason}")
            return False, reason

        # get acceptable forms for this specific country
        valid_countries = country_aliases.get(country_lower, [country_lower])

        # look in window
        window = llm_lower[idx: idx + len(name_lower) + 20]

        if not any(alias in window for alias in valid_countries):
            reason = (
                f"Country '{country}' (or alias) not found within 20 chars after name '{name}'"
            )
            print(f"❌ {reason}")
            return False, reason

        print(f"✅ Found: {name} + {country} (or alias) at position {idx}")
        last_idx = idx

    print("✅ All name-country pairs matched correctly in order.")
    return True, "OK"
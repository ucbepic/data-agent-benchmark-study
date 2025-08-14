import re

ground_truth = [
    (
        "TACOS LA CABANA",
        [
            ['Thursday', 'Closed'],
            ['Friday', '5–11PM'],
            ['Saturday', '5–11PM'],
            ['Sunday', '5–11PM'],
            ['Monday', '5–11PM'],
            ['Tuesday', 'Closed'],
            ['Wednesday', 'Closed']
        ],
        5.0
    ),
    (
        "White Barn Candle Co",
        [
            ['Thursday', '10AM–9PM'],
            ['Friday', '10AM–9PM'],
            ['Saturday', '10AM–9PM'],
            ['Sunday', '11AM–7PM'],
            ['Monday', '10AM–9PM'],
            ['Tuesday', '10AM–9PM'],
            ['Wednesday', '10AM–9PM']
        ],
        5.0
    ),
    (
        "Mariscos el poblano",
        [
            ['Thursday', 'Open 24 hours'],
            ['Friday', '8AM–3:30PM'],
            ['Saturday', '8AM–3:30PM'],
            ['Sunday', '8AM–3:30PM'],
            ['Monday', '9AM–3:30AM'],
            ['Tuesday', '8AM–3:30PM'],
            ['Wednesday', '8AM–3:30PM']
        ],
        5.0
    ),
    (
        "Beauty Divine Artistry",
        [
            ['Thursday', '9AM–8PM'],
            ['Friday', '9AM–8PM'],
            ['Saturday', '10AM–7PM'],
            ['Sunday', '11AM–6PM'],
            ['Monday', '9AM–8PM'],
            ['Tuesday', '9AM–8PM'],
            ['Wednesday', '9AM–8PM']
        ],
        5.0
    ),
    (
        "Taba Rug Gallery",
        [
            ['Thursday', '10AM–7PM'],
            ['Friday', '10AM–7PM'],
            ['Saturday', '10AM–7PM'],
            ['Sunday', '11AM–6PM'],
            ['Monday', '10AM–7PM'],
            ['Tuesday', '10AM–7PM'],
            ['Wednesday', '10AM–7PM']
        ],
        5.0
    )
]


def validate(llm_output: str) -> (bool, str):
    """
    Validate LLM output for query3:
    - Business names must appear
    - All hours (day + hours) must appear near the name (case-insensitive, full match)
    - Score must appear after hours block, rounded to 2 decimals
    Returns:
        (True, "OK") if pass
        (False, reason) if fail
    """
    llm_lower = llm_output.lower()

    for name, hours_list, score in ground_truth:
        name_lower = name.lower()
        idx = llm_lower.find(name_lower)
        if idx == -1:
            reason = f"Missing business name: {name}"
            print(f"❌ {reason}")
            return False, reason

        # Get a window after name to check hours and score
        window = llm_output[idx:idx+500].lower()

        # Check that all (day, hours) pairs appear
        for day, hours in hours_list:
            day_l, hours_l = day.lower(), hours.lower()
            if day_l not in window or hours_l not in window:
                reason = f"Missing hours [{day}, {hours}] for business: {name}"
                print(f"❌ {reason}")
                return False, reason

        # After hours block, look for score
        matches = re.findall(r"(\d+(?:\.\d+)?)", window)
        if not matches:
            reason = f"No score found after hours info for business: {name}"
            print(f"❌ {reason}")
            return False, reason

        # Compare each number found in window
        gt_score_rounded = round(score, 2)
        found = False
        for m in matches:
            try:
                val = float(m)
                if round(val, 2) == gt_score_rounded:
                    found = True
                    break
            except:
                continue

        if not found:
            reason = f"Score mismatch for business: {name}, expected ~{gt_score_rounded:.2f}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All businesses validated successfully.")
    return True, "OK"

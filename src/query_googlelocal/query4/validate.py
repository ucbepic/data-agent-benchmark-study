import re

ground_truth = [
    ("Encino Dermatology & Laser", 19),
    ("The Boochyard @ Local Roots", 17),
    ("Aurora Massage", 14),
]

def validate(llm_output: str) -> (bool, str):
    """
    Validate LLM output:
    - All names from ground truth appear (case-insensitive)
    - For each name, a number appears within 10 characters AFTER the name
    Returns:
        (True, "OK") if valid
        (False, reason) if not
    """
    llm_lower = llm_output.lower()

    for name, expected_num in ground_truth:
        name_lower = name.lower()
        idx = llm_lower.find(name_lower)
        if idx == -1:
            reason = f"Missing business name: {name}"
            print(f"❌ {reason}")
            return False, reason

        after_name_start = idx + len(name)
        after_window = llm_output[after_name_start:after_name_start + 25]
        matches = re.findall(r"\d+", after_window)

        if not matches:
            reason = f"No number found after {name}"
            print(f"❌ {reason}")
            return False, reason

        found_match = any(int(m) == expected_num for m in matches)
        if not found_match:
            reason = f"Number mismatch for {name}: expected {expected_num}"
            print(f"❌ {reason}")
            return False, reason

        print(f"✅ Matched: {name} → {expected_num}")

    print("✅ All names and numbers matched.")
    return True, "OK"

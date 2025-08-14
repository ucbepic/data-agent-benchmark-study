import re

ground_truth = [
    ("Encino Dermatology & Laser", 19),
    ("The Boochyard @ Local Roots", 17),
    ("Aurora Massage", 14),
]

def validate(llm_output: str) -> (bool, str):
    """
    Validate LLM output:
    - All names from ground truth appear
    - Each name has a number nearby equal to ground truth
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

        # name 后面取 50 个字符
        window = llm_output[idx:idx+50]
        matches = re.findall(r"\d+", window)

        if not matches:
            reason = f"No number found near {name}"
            print(f"❌ {reason}")
            return False, reason

        found_match = False
        for m in matches:
            if int(m) == expected_num:
                found_match = True
                break

        if not found_match:
            reason = f"Number mismatch for {name}: expected {expected_num}"
            print(f"❌ {reason}")
            return False, reason

    print("✅ All names and numbers matched.")
    return True, "OK"

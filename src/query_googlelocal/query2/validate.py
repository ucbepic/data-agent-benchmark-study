import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate LLM output for query1:
    - All names from ground truth appear
    - For each name, a score appears nearby, rounded to 2 decimals matches ground truth
    - Order does NOT matter
    Returns:
        (True, "OK") if valid
        (False, reason) if invalid
    """
    ground_truth = [
        ("Elite Massage", 5.0),
        ("Angel-A Massage", 4.333333333333333),
        ("Aurora Massage", 4.178571428571429),
        ("J B Oriental Inc", 4.166666666666667)
    ]

    for name, true_score in ground_truth:
        idx = llm_output.find(name)
        if idx == -1:
            reason = f"Missing name in LLM output: {name}"
            print(f"❌ {reason}")
            return False, reason

        window = llm_output[idx:idx+50]
        matches = re.findall(r"(\d+\.\d+)", window)
        if not matches:
            reason = f"No score found near {name}"
            print(f"❌ {reason}")
            return False, reason

        gt_rounded = round(true_score, 2)
        for m in matches:
            llm_val = float(m)
            if round(llm_val, 2) == gt_rounded:
                break
        else:
            reason = f"Score mismatch for {name}: expected ~{gt_rounded:.2f}, but not found nearby."
            print(f"❌ {reason}")
            return False, reason

    print("✅ All names and scores are present, and scores match within 2 decimals.")
    return True, "OK"

import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate LLM output for query1:
    - All names from ground truth appear (case-sensitive exact match)
    - For each name, a score appears in the next 50 characters (after name, excluding name itself)
    - Score must round to ground truth score to 2 decimals
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

        # Get 10 characters AFTER the name (exclude name itself)
        start = idx + len(name)
        window = llm_output[start:start+10]
        matches = re.findall(r"(\d+\.\d+)", window)
        if not matches:
            reason = f"No score found after name: {name}"
            print(f"❌ {reason}")
            return False, reason

        gt_rounded = round(true_score, 2)
        for m in matches:
            llm_val = float(m)
            if round(llm_val, 2) == gt_rounded:
                break
        else:
            reason = f"Score mismatch for {name}: expected ~{gt_rounded:.2f}, but not found after name."
            print(f"❌ {reason}")
            return False, reason

        print(f"✅ Matched {name} with score ~{gt_rounded:.2f}")

    print("✅ All names and scores matched successfully.")
    return True, "OK"

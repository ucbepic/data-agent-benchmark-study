def validate(llm_output: str) -> (bool, str):
    """
    Validate if ground truth number (rounded to 2 decimals) is present in LLM output.
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    import re

    ground_truth = 3.547008547008547
    gt_rounded = round(ground_truth, 2)

    # 找出 LLM 输出里所有数字
    matches = re.findall(r"(\d+\.\d+)", llm_output)
    if not matches:
        reason = f"No number found in LLM output."
        print(f"❌ {reason}")
        return False, reason

    for m in matches:
        try:
            val = float(m)
            if round(val, 2) == gt_rounded:
                print(f"✅ Found matching number: {val} ≈ {gt_rounded}")
                return True, "OK"
        except:
            continue

    reason = f"No matching number (≈ {gt_rounded:.2f}) found in LLM output."
    print(f"❌ {reason}")
    return False, reason

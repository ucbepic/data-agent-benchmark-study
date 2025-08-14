import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate if any number in LLM output (rounded to 2 decimals) equals ground truth.
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    gt_value = 18.440000534057617
    gt_rounded = round(gt_value, 2)

    # find all numbers
    matches = re.findall(r"(\d+\.\d+)", llm_output)
    if not matches:
        reason = "No number found in LLM output."
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

    reason = f"No number ≈ {gt_rounded} found in LLM output."
    print(f"❌ {reason}")
    return False, reason

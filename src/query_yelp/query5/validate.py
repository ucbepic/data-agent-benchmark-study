import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate if 'PA' or 'Pennsylvania' (case-insensitive) 
    and its number (rounded to 2 decimals) are present in LLM output.
    Returns:
        (True, "OK") if valid
        (False, reason) if not
    """
    gt_names = ["PA", "Pennsylvania"]
    ground_truth_value = 3.48
    gt_rounded = round(ground_truth_value, 2)

    llm_output_lower = llm_output.lower()

    for name in gt_names:
        name_lower = name.lower()
        idx = llm_output_lower.find(name_lower)
        if idx != -1:
            print(f"✅ Found name: '{name}' at position {idx}")

            # look for a number in the next 50 chars
            window = llm_output[idx: idx+50]
            matches = re.findall(r"\d+(?:\.\d+)?", window)

            if not matches:
                reason = f"No number found near name: {name}"
                print(f"❌ {reason}")
                return False, reason

            for m in matches:
                try:
                    val = float(m)
                    if round(val, 2) == gt_rounded:
                        print(f"✅ Found: name='{name}', value≈{gt_rounded}")
                        return True, "OK"
                except Exception:
                    continue

            reason = f"Number near '{name}' does not match ≈{gt_rounded}"
            print(f"❌ {reason}")
            return False, reason

    reason = f"Neither 'PA' nor 'Pennsylvania' found in LLM output"
    print(f"❌ {reason}")
    return False, reason


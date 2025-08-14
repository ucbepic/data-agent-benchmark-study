import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate if ground truth 'PA' or 'Pennsylvania' and its number (rounded to 2 decimals) 
    are present in LLM output.
    
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    ground_truth_names = ["PA", "Pennsylvania"]
    ground_truth_value = 3.699395770392749
    gt_rounded = round(ground_truth_value, 2)

    llm_lower = llm_output.lower()

    found_name = None
    idx = -1

    for name in ground_truth_names:
        name_lower = name.lower()
        idx = llm_lower.find(name_lower)
        if idx != -1:
            found_name = name
            break

    if not found_name:
        reason = f"Missing name: {ground_truth_names}"
        print(f"❌ {reason}")
        return False, reason

    print(f"✅ Found name: '{found_name}' at position {idx}")

    # search for number near name (within 50 chars after name)
    window = llm_output[idx:idx+50]
    matches = re.findall(r"(\d+\.\d+)", window)

    if not matches:
        reason = f"No number found near name: {found_name}"
        print(f"❌ {reason}")
        return False, reason

    for m in matches:
        try:
            val = float(m)
            if round(val, 2) == gt_rounded:
                print(f"✅ Found: name='{found_name}', value≈{gt_rounded}")
                return True, "OK"
        except:
            continue

    reason = f"Number near '{found_name}' does not match ≈{ground_truth_value}"
    print(f"❌ {reason}")
    return False, reason



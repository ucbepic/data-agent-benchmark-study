import re

def validate(llm_output: str) -> (bool, str):
    """
    Validate if the integer 35 is present in LLM output.
    Returns:
        (True, "OK") if found
        (False, reason) if not
    """
    ground_truth = 35

    # find all integers in LLM output
    matches = re.findall(r"\b\d+\b", llm_output)

    if not matches:
        reason = "No number found in LLM output."
        print(f"❌ {reason}")
        return False, reason

    for m in matches:
        if int(m) == ground_truth:
            print(f"✅ Found number: {ground_truth}")
            return True, "OK"

    reason = f"Number {ground_truth} not found in LLM output."
    print(f"❌ {reason}")
    return False, reason

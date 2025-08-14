def validate(llm_output: str) -> (bool, str):
    """
    Validate that:
    - 'IXIC' is present in LLM output
    - None of the other candidates are present

    Returns:
        (True, "OK") if all good
        (False, reason) if failed
    """
    gt = "IXIC"
    forbidden = [
        "J203.JO", "N225", "GSPTSE", "NSEI", "GDAXI", "NYA",
        "000001.SS", "SSMI", "TWII", "N100", "399001.SZ", "HSI"
    ]

    llm_lower = llm_output.lower()
    gt_lower = gt.lower()
    forbidden_lower = [f.lower() for f in forbidden]

    # check gt
    if gt_lower not in llm_lower:
        reason = f"Missing target: {gt}"
        print(f"❌ {reason}")
        return False, reason

    # check forbidden
    for f in forbidden_lower:
        if f in llm_lower:
            reason = f"Found forbidden value: {f}"
            print(f"❌ {reason}")
            return False, reason

    print(f"✅ Only target '{gt}' present, no forbidden values.")
    return True, "OK"
